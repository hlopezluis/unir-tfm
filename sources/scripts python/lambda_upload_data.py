import os
import boto3
import csv
import pandas as pd
import numpy as np
import io
import re
from pymongo import MongoClient

def lambda_handler(event, context):
    s3 = boto3.client('s3') 

    try:
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]
        
        print(f"Bucket: {bucket_name}, Key: {object_key}")

        # Conexión a MongoDB
        client = MongoClient(host=os.environ.get("ATLAS_URI"))
        db = client["tfm"]
        collection = db["raecmbd"]

        # Obtener el archivo desde S3
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')

        # Leer el CSV
        df = pd.read_csv(io.StringIO(content), sep=';')      

        # Nos quedamos sólo con las columnas útiles para el proyecto
        columnas_a_conservar = [
            'Número de registro anual', 'Comunidad Autónoma', 'Edad', 'Sexo', 'País Nacimiento', 'Tipo Alta',
            'Ingreso en UCI', 'Días UCI', 'Estancia Días', 'Diagnóstico Principal', 
        ] + [f'Diagnóstico {i}' for i in range(2, 21)] + [f'Procedimiento {i}' for i in range(1, 21)]

        df = df[columnas_a_conservar]
        
        # Renombrar columnas
        df = df.rename(columns={'Número de registro anual': 'numRegistro', 'Comunidad Autónoma': 'comunidadAutonoma', 'Edad': 'edad', 
                                'Sexo': 'sexo', 'País Nacimiento': 'paisNacimiento', 'Tipo Alta': 'tipoAlta',
                                'Ingreso en UCI': 'ingresoUCI', 'Días UCI': 'diasUCI', 'Estancia Días': 'estanciaDias'})

        # Eliminamos los registros cuyo número de registro ya esté en la colección
        batch_size = 1000
        filtered_df = pd.DataFrame()

        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            existing = collection.find(
                {"numRegistro": {"$in": batch["numRegistro"].tolist()}},
                {"numRegistro": 1, "_id": 0}
            )
            existing_nums = {doc["numRegistro"] for doc in existing}
            filtered_batch = batch[~batch["numRegistro"].isin(existing_nums)]
            filtered_df = pd.concat([filtered_df, filtered_batch])

        df = filtered_df

        # Transformamos valores nulos de alguna columna
        df['diasUCI'] = df['diasUCI'].fillna(0)
        df['ingresoUCI'] = np.where(df['ingresoUCI'] == 1, True, False)

        # Definir el rango de edad
        def asignar_rango(edad):
            if edad < 25:
                return '< 25'
            elif 25 <= edad < 35:
                return '25 - 34'
            elif 35 <= edad <= 40:
                return '35 - 40'
            else:
                return '> 40'

        df['rango'] = df['edad'].apply(asignar_rango)

        # Definir los razas
        razas = {
            'no identificada': ['000'],
            'árabe': ['004', '012', '031', '048', '275','364', '368', '398', '400', '414', '417', '422','430', '434', '504','512','586', '634', '682', '732', '760', '762', '784', '788', '792', '795', '818', '860', '887'],
            'caucásica': ['008','020','032','036','040','051','056','070','100','112','124','152','191','196','203','208','233','234','246','248','250','268','276','292','300','304','336','348','352','372','376','380','428',
                        '438','440','442','492','498','499','528','554','574','578','616','620','642','643','688','703','705','724','744','752','756','804','807','826','833','840'],
            'indeterminada': ['016'],
            'negra': ['024','028','044','052','060','072','076','090','092','108','120','132','136','140','148','174','175','178','180','204','212','214','226','231','232','258','262','266',
                    '270','288','308','324','332','384','388','404','426','450','454','466','474','478','508','516','562','566','598','624','630','646','686','690','694','706','716','728','729','748','768','780','796','800','834','854','894'],
            'polinesia_malayo': ['050','096','104','144','184','242','254','316','360','418','446','458','520','570','583','585','608','626','652','704','764','772','776','798','876','882'],
            'china': ['064','116','156','344','392','408','410','496','524','702'],
            'hindú': ['356'],
            'hispana': ['068','084','170','188','218','222','320','340','484','558','591','600','604','862'],
            'mixta': ['192','238','296','312','328','462','470','480','500','531','533','534','535','540','548','580','581','584','612','638','654','659','660','662','663','666','670','674','678','710','740','831','832','850','858']
        }

        # Crear un diccionario de país -> raza
        raza_por_codigo = {}
        for raza, codigos in razas.items():
            for codigo in codigos:
                raza_por_codigo[codigo] = raza

        # Formatear 'País Nacimiento' y asignar raza
        df['paisNacimiento'] = df['paisNacimiento'].astype(str).str.zfill(3)
        df['raza'] = df['paisNacimiento'].map(raza_por_codigo)
        df['raza'] = df['raza'].fillna('no identificada')

        # Comunidad autónoma
        comunidades_autonoma = {
            'Andalucía': 1,
            'Aragón': 2,
            'Asturias': 3,
            'Balears': 4,
            'Canarias': 5,	
            'Cantabria': 6,
            'Castilla y León': 7,
            'Castilla La Mancha': 8,
            'Cataluña': 9,
            'Comunitat Valenciana': 10,
            'Extremadura': 11,
            'Galicia': 12,
            'Madrid': 13,
            'Murcia': 14,
            'Navarra': 15,
            'País Vasco': 16,
            'La Rioja': 17,
            'Ceuta': 18,
            'Melilla': 19
        }

        codigo_a_comunidad = {v: k for k, v in comunidades_autonoma.items()}

        df['comunidadAutonomaNombre'] = df['comunidadAutonoma'].map(codigo_a_comunidad)
        df['comunidadAutonomaCodigo'] = df['comunidadAutonoma'].astype(str).str.zfill(2)

        # Países
        paises = {
            "no identificado": 0,
            "Afganistán": 4,
            "Albania": 8,
            "Alemania": 276,
            "Andorra": 20,
            "Angola": 24,
            "Antigua y Barbuda": 28,
            "Arabia Saudita": 682,
            "Argelia": 12,
            "Argentina": 32,
            "Armenia": 51,
            "Australia": 36,
            "Austria": 40,
            "Azerbaiyán": 31,
            "Bahamas": 44,
            "Bangladés": 50,
            "Barbados": 52,
            "Baréin": 48,
            "Bélgica": 56,
            "Belice": 84,
            "Benín": 204,
            "Bielorrusia": 112,
            "Birmania": 104,
            "Bolivia": 68,
            "Bosnia y Herzegovina": 70,
            "Botsuana": 72,
            "Brasil": 76,
            "Brunéi": 96,
            "Bulgaria": 100,
            "Burkina Faso": 854,
            "Burundi": 108,
            "Bután": 64,
            "Cabo Verde": 132,
            "Camboya": 116,
            "Camerún": 120,
            "Canadá": 124,
            "Catar": 634,
            "Chad": 148,
            "Chile": 152,
            "China": 156,
            "Chipre": 196,
            "Colombia": 170,
            "Comoras": 174,
            "Congo": 178,
            "Corea del Norte": 408,
            "Corea del Sur": 410,
            "Costa de Marfil": 384,
            "Costa Rica": 188,
            "Croacia": 191,
            "Cuba": 192,
            "Dinamarca": 208,
            "Dominica": 212,
            "Ecuador": 218,
            "Egipto": 818,
            "El Salvador": 222,
            "Emiratos Árabes Unidos": 784,
            "Eritrea": 232,
            "Eslovaquia": 703,
            "Eslovenia": 705,
            "España": 724,
            "Estados Unidos": 840,
            "Estonia": 233,
            "Etiopía": 231,
            "Filipinas": 608,
            "Finlandia": 246,
            "Fiyi": 242,
            "Francia": 250,
            "Gabón": 266,
            "Gambia": 270,
            "Georgia": 268,
            "Ghana": 288,
            "Granada": 308,
            "Grecia": 300,
            "Guatemala": 320,
            "Guinea": 324,
            "Guinea-Bisáu": 624,
            "Guinea Ecuatorial": 226,
            "Guyana": 328,
            "Haití": 332,
            "Honduras": 340,
            "Hungría": 348,
            "India": 356,
            "Indonesia": 360,
            "Irán": 364,
            "Irak": 368,
            "Irlanda": 372,
            "Islandia": 352,
            "Islas Marshall": 584,
            "Islas Salomón": 90,
            "Israel": 376,
            "Italia": 380,
            "Jamaica": 388,
            "Japón": 392,
            "Jordania": 400,
            "Kazajistán": 398,
            "Kenia": 404,
            "Kirguistán": 417,
            "Kiribati": 296,
            "Kuwait": 414,
            "Laos": 418,
            "Lesoto": 426,
            "Letonia": 428,
            "Líbano": 422,
            "Liberia": 430,
            "Libia": 434,
            "Liechtenstein": 438,
            "Lituania": 440,
            "Luxemburgo": 442,
            "Madagascar": 450,
            "Malasia": 458,
            "Malaui": 454,
            "Maldivas": 462,
            "Malí": 466,
            "Malta": 470,
            "Marruecos": 504,
            "Mauricio": 480,
            "Mauritania": 478,
            "México": 484,
            "Micronesia": 583,
            "Moldavia": 498,
            "Mónaco": 492,
            "Mongolia": 496,
            "Montenegro": 499,
            "Mozambique": 508,
            "Namibia": 516,
            "Nauru": 520,
            "Nepal": 524,
            "Nicaragua": 558,
            "Níger": 562,
            "Nigeria": 566,
            "Noruega": 578,
            "Nueva Zelanda": 554,
            "Omán": 512,
            "Países Bajos": 528,
            "Pakistán": 586,
            "Palaos": 585,
            "Panamá": 591,
            "Papúa Nueva Guinea": 598,
            "Paraguay": 600,
            "Perú": 604,
            "Polonia": 616,
            "Portugal": 620,
            "Reino Unido": 826,
            "República Centroafricana": 140,
            "República Checa": 203,
            "República Democrática del Congo": 180,
            "República Dominicana": 214,
            "Ruanda": 646,
            "Rumanía": 642,
            "Rusia": 643,
            "Samoa": 882,
            "San Cristóbal y Nieves": 659,
            "San Marino": 674,
            "San Vicente y las Granadinas": 670,
            "Santa Lucía": 662,
            "Santo Tomé y Príncipe": 678,
            "Senegal": 686,
            "Serbia": 688,
            "Seychelles": 690,
            "Sierra Leona": 694,
            "Singapur": 702,
            "Siria": 760,
            "Somalia": 706,
            "Sri Lanka": 144,
            "Suazilandia": 748,
            "Sudáfrica": 710,
            "Sudán": 729,
            "Sudán del Sur": 728,
            "Suecia": 752,
            "Suiza": 756,
            "Surinam": 740,
            "Tailandia": 764,
            "Tanzania": 834,
            "Tayikistán": 762,
            "Timor Oriental": 626,
            "Togo": 768,
            "Tonga": 776,
            "Trinidad y Tobago": 780,
            "Túnez": 788,
            "Turkmenistán": 795,
            "Turquía": 792,
            "Tuvalu": 798,
            "Ucrania": 804,
            "Uganda": 800,
            "Uruguay": 858,
            "Uzbekistán": 860,
            "Vanuatu": 548,
            "Venezuela": 862,
            "Vietnam": 704,
            "Yemen": 887,
            "Yibuti": 262,
            "Zambia": 894,
            "Zimbabue": 716
        }

        codigo_a_paises = {v: k for k, v in paises.items()}

        df['paisNacimiento'] = np.where(df['paisNacimiento'] == 'ZZZ', 0, df['paisNacimiento'])
        df['paisNacimientoNombre'] = df['paisNacimiento'].astype(int).map(codigo_a_paises)
        df['paisNacimientoCodigo'] = df['paisNacimiento'].astype(int)

        # Alta
        tipo_altas = {
            "Domicilio": 1,
            "Traslado a otro Hospital": 2,
            "Alta voluntaria": 3,
            "Exitus": 4,
            "Traslado a centro sociosanitario": 5,
            "Otros": 8,
            "Desconocido": 9
        }

        codigo_a_tipo_altas = {v: k for k, v in tipo_altas.items()}

        df['tipoAltaNombre'] = df['tipoAlta'].astype(int).map(codigo_a_tipo_altas)
        df['tipoAltaCodigo'] = df['tipoAlta'].astype(int)

        # Sexo
        sexos = {
            "Varón": 1,
            "Mujer": 2,
            "No especificado": 9
        }

        codigo_a_sexos = {v: k for k, v in sexos.items()}

        df['sexoNombre'] = df['sexo'].astype(int).map(codigo_a_sexos)
        df['sexoCodigo'] = df['sexo'].astype(int)

        # Entradas y Salidas
        columnas_diagnostico = [f'Diagnóstico {i}' for i in range(1, 21)]

        columnas_procedimiento = [f'Procedimiento {i}' for i in range(1, 21)]

        columnas_condiciones_entradas = [
            'embarazoAltoRiesgo', 'esterilidadPrevia', 'historiaObstetricaAdversa', 'perdidaPrevia',
            'abortoPrevio', 'muerteFetalPrevia', 'multipara', 'primipara', 'embarazoTra',
            'embarazoTraPrevio', 'enfermedadCardiacaHipertensiva', 'enfermedadRenalCronicaHipertensiva',
            'enfermedadCardiacaYRenalCronicaHipertensiva', 'embarazoMultiple', 'hta', 'dm',
            'sobrepesoYObesidad', 'tabaco', 'alcohol', 'dislipemia', 'neumopatiaIntersticialGenerica',
            'easIntersticialGenerica', 'hipertensionPulmonarGenerica', 'erc', 'ic', 'les',
            'nefritisLupica', 'lesPulmon', 'safV1', 'safV2', 'safV3', 'portadorAafV1', 'portadorAafV2',
            'esclerosisSistemica', 'sscRespiratorio', 'sindromeSeco', 'sjsRespiratorio',
            'sjsTubulointersticial', 'emtc', 'enfermedadBehcet', 'miopatiaInflamatoria',
            'vasculitisSistemica', 'vasculitisAnca', 'sarcoidosis', 'artritisReumatoide',
            'artropatiasEnteropaticas', 'artropatiaPsoriasica', 'eii', 'enfermedadGlomerular',
            'sindromeDeSjogrenPrimario', 'antiagregacion', 'aspirina', 'anticoagulacion',
            'esteroides', 'covid19', 'neumoniaCovid'
        ]

        condiciones_entradas = {
            'embarazoAltoRiesgo': ['O09'],
            'esterilidadPrevia': ['O09.0'],
            'historiaObstetricaAdversa': ['O09.2', 'O26.2'],
            'perdidaPrevia': ['O09.29', 'O26.2'],
            'abortoPrevio': ['O26.21'],
            'muerteFetalPrevia': ['O09.29', 'O26.23'],
            'multipara': ['O09.4', 'O09.52', 'O09.62'],
            'primipara': ['O09.51', 'O09.61'],
            'embarazoTra': ['O09.81'],
            'embarazoTraPrevio': ['O09.82'],
            'enfermedadCardiacaHipertensiva': ['O10.1', 'O10.3'],
            'enfermedadRenalCronicaHipertensiva': ['O10.2', 'O10.3'],
            'enfermedadCardiacaYRenalCronicaHipertensiva': ['O10.3'],
            'embarazoMultiple': ['O30', 'O31', 'Z37.2', 'Z37.3'],
            'hta': ['I10', 'I11', 'I12', 'I13', 'I15', 'I16', 'I67.4', 'O10', 'O11'],
            'dm': ['E08', 'E09', 'E10', 'E11', 'O24.0', 'O24.1', 'O24.4', 'O24.8'],
            'sobrepesoYObesidad': ['E66', 'O99.21'],
            'tabaco': ['Z72.0', 'F17', 'T65.22', 'O99.33'],
            'alcohol': ['F10', 'O99.31'],
            'dislipemia': ['E78.0', 'E78.2', 'E78.4', 'E78.5'],
            'neumopatiaIntersticialGenerica': ['J84', 'J82.81', 'J82.82', '515', '516', '517.1', '517.2', '517.8'],
            'easIntersticialGenerica': ['J84.17', '517.1', '517.2', '517.8'],
            'hipertensionPulmonarGenerica': ['I27.0', 'I27.2', '416.0', '416.8'],
            'erc': ['I12', 'I13', 'N18'],
            'ic': ['I25.5', '142', 'I50', 'I05', 'I06', 'I07', 'I08', 'I09', '134', '135', 'I36', 'I37', 'I27', 'I11', 'I13'],
            'les': ['M32'],
            'nefritisLupica': ['M32.14', 'M32.15'],
            'lesPulmon': ['M32.13'],
            'safV1': ['D68.61'],
            'safV2': ['D68.62'],
            'safV3': ['D68.61', 'D68.62'],
            'portadorAafV1': ['D68.312'],
            'portadorAafV2': ['D68.61', 'D68.312', 'D68.62'],
            'esclerosisSistemica': ['M34'],
            'sscRespiratorio': ['M34.81'],
            'sindromeSeco': ['M35.0'],
            'sjsRespiratorio': ['M35.02'],
            'sjsTubulointersticial': ['M35.04'],
            'emtc': ['M35.1'],
            'enfermedadBehcet': ['M35.2'],
            'miopatiaInflamatoria': ['M33', 'M36.0', 'G72.49'],
            'vasculitisSistemica': ['M30.0', 'M30.1', 'M30.2', 'M30.3', 'M30.8', 'M31.3', 'M31.4', 'M31.5', 'M31.6', 'M31.8', 'M31.9', 'D69.0', 'D89.1'],
            'vasculitisAnca': ['M30.1', 'M31.3', 'M31.7'],
            'sarcoidosis': ['D86'],
            'artritisReumatoide': ['M05', 'M06'],
            'artropatiasEnteropaticas': ['M07'],
            'artropatiaPsoriasica': ['L40.5'],
            'eii': ['K50', 'K51'],
            'enfermedadGlomerular': ['N00', 'N01', 'N02', 'N03', 'N04', 'N05', 'N06', 'N08'],
            'sindromeDeSjogrenPrimario': ['M35.04'],
            'antiagregacion': ['Z79.02', 'Z79.82'],
            'aspirina': ['Z79.82'],
            'anticoagulacion': ['Z79.01'],
            'esteroides': ['Z79.52'],
            'covid19': ['U07.1'],
            'neumoniaCovid': ['J12.82']
        }

        columnas_condiciones_salidas = [
            'aborto', 'muerteFetal', 'rnMuerto', 'muerteTardia', 'rnVivo', 'rn', 'preclampsia', 'preclampsiaPrecoz',
            'preclampsiaGrave', 'preclampsiaGravePrecoz', 'preclampsiaGraveTardia', 'eclampsia', 'helpp', 'ictusPe',
            'ictusHemorragicoPe', 'ictusIsquemicoPe', 'peCriteriosGravedad', 'ppp', 'sufrimientoFetal', 'cirBajoPeso',
            'cesarea', 'roturaPrematuraMembranas', 'abruptioPlacentae', 'peAdverseFetal', 'hemorragiaFaseTempranaEmbarazo',
            'hemorragiaPartoAntepartoPosparto', 'instrumental', 'trombosisEmbarazoPuerperio', 'trombosisPuerperio',
            'trombosisEmbarazo', 'tromboembolismoPulmonar', 'trombosisVenosaProfunda', 'trombosisVenosaAtipicos', 'trombosisSenos'
        ]

        # Creamos atributos de salidas basadas en códigos de procedimiento
        condiciones_salidas_procedimiento = {
            'cesarea': ['10D00Z0', '10D00Z1'],
            'instrumental': ['10D07Z']
        }

        # Creamos atributos de salidas basadas en códigos de diagnóstico
        condiciones_salidas_diagnostico = {
            'aborto': ['O03', 'O02.1', 'O31.1'],
            'muerteFetal': ['O36.4', 'O31.2'],
            'rnMuerto': ['Z37.1', 'Z37.3', 'Z37.4'],
            'muerteTardia': ['O36.4', 'O31.2', 'Z37.1', 'Z37.3', 'Z37.4'],
            'rnVivo': ['Z37.0', 'Z37.2', 'Z37.3', 'Z38'],
            'rn': ['Z37.1', 'Z37.3', 'Z37.4', 'Z37.0', 'Z37.2', 'Z37.3', 'Z38'],
            'preclampsia': ['O11', 'O14', 'O15'],
            'preclampsiaPrecoz': ['O11.1', 'O11.2', 'O14.02', 'O14.12', 'O14.22', 'O14.92'],
            'preclampsiaGrave': ['O14.1'],
            'preclampsiaGravePrecoz': ['O14.12'],
            'preclampsiaGraveTardia': ['O14.13'],
            'eclampsia': ['O15'],
            'helpp': ['O14.2'],
            'ictusPe': ['I60', 'I61', 'I63'],
            'ictusHemorragicoPe': ['I60', 'I61'],
            'ictusIsquemicoPe': ['I63'],
            'peCriteriosGravedad': ['O11.1', 'O11.2', 'O14.02', 'O14.12', 'O14.22', 'O14.92', 'O14.1', 'O15', 'O14.2'],
            'ppp': ['O60.1', 'O60.2'],
            'sufrimientoFetal': ['O68', 'O69', 'O76', 'O77', 'O36.83', 'O36.89', 'O36.9', 'O36.81', 'O36.9'],
            'cirBajoPeso': ['O36.5'],	
            'roturaPrematuraMembranas': ['O42'],
            'abruptioPlacentae': ['O45'],
            'peAdverseFetal': ['O60.1', 'O60.2', 'O68', 'O69', 'O76', 'O77', 'O36.83', 'O36.89', 'O36.9', 'O36.81', 'O36.9'],
            'hemorragiaFaseTempranaEmbarazo': ['O20.0'],
            'hemorragiaPartoAntepartoPosparto': ['O46', 'O72'],    
            'trombosisEmbarazoPuerperio': ['O87.1', 'O87.3', 'O22.3', 'O22.5', 'I26', 'I81', 'I82'],
            'trombosisPuerperio': ['O87.1', 'O87.3'],
            'trombosisEmbarazo': ['O22.3', 'O22.5'],
            'tromboembolismoPulmonar': ['I26'],
            'trombosisVenosaProfunda': ['I82.4'],
            'trombosisVenosaAtipicos': ['I81', 'I82'],
            'trombosisSenos': ['G08', 'I67.6']
        }

        def crear_columnas(condiciones, columnas, df):      
            # Compilar patrones una sola vez
            patrones = {
                condicion: re.compile(r'^(' + '|'.join([re.escape(cod.strip()) for cod in codigos]) + r')')
                for condicion, codigos in condiciones.items()
            }

            # Convertir columnas de diagnóstico a matriz NumPy de strings
            matriz = df[columnas].astype(str).values

            # Crear DataFrame para resultados
            resultados = pd.DataFrame(index=df.index)

            # Aplicar patrones con vectorización
            for condicion, patron in patrones.items():
                # Vectorizar la función de coincidencia
                match_func = np.vectorize(lambda x: bool(patron.match(x.strip())))
                mask = match_func(matriz)
                resultados[condicion] = mask.any(axis=1).astype(int)

            # Combinar resultados con el DataFrame original
            return pd.concat([df, resultados], axis=1)

        # Crear columnas 'entrada'
        df = crear_columnas(condiciones_entradas, columnas_diagnostico, df)

        # Crear columnas 'salidas'
        df = crear_columnas(condiciones_salidas_procedimiento, columnas_procedimiento, df)
        df = crear_columnas(condiciones_salidas_diagnostico, columnas_diagnostico, df)
        
        # Exitus
        df['exitus'] = (df['tipoAltaCodigo'] == 4).astype(int)

        # PE Adverse Maternal
        df['peAdverseMaternal'] = (
            (df['exitus'] == 1) | 
            (df['ingresoUCI'] == 1) | 
            (df['ictusPe'] == 1)
        ).astype(int)

        # Crear un dataframe final con las columnas que nos interesan
        columnas_iniciales = ['numRegistro', 'edad', 'rango', 'sexoCodigo', 'sexoNombre', 'raza', 
                            'paisNacimientoCodigo', 'paisNacimientoNombre', 'comunidadAutonomaCodigo', 'comunidadAutonomaNombre', 
                            'tipoAltaCodigo', 'tipoAltaNombre', 'exitus', 'estanciaDias', 'ingresoUCI', 'diasUCI']

        columnas = columnas_iniciales + columnas_condiciones_entradas + columnas_condiciones_salidas + ['peAdverseMaternal']

        df_final= df[columnas]

        # Volcar el DataFrame a MongoDB
        #collection.insert_many(df_final.to_dict("records"))
        def insertar_por_chunks(df, collection, chunk_size=10000):
            for start in range(0, len(df), chunk_size):
                end = start + chunk_size
                collection.insert_many(df.iloc[start:end].to_dict("records"))

        # Insertar
        insertar_por_chunks(df_final, collection)

        print(f"Registros insertados: {len(df)}")

        return {
            'statusCode': 200,
            'body': f'Archivo {object_key} leído correctamente desde {bucket_name} y volcado a Mongo.'
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }