const pageSize = 10;
let currentPage = 1;
let totalPages = 1;

async function fetchData(page) {
    console.log('fetchData')

    $('#loading-spinner').show();
    $('#table-body').empty();

    try {
        let queryString = generarQueryString();
        let api = `https://61yfnkfn3i.execute-api.eu-west-3.amazonaws.com/diagnostics?page=${page}&pageSize=${pageSize}`;

        if (queryString != "") {
            api += "&" + queryString;
        }

        console.log(api);

        const response = await fetch(api);            
        const text = await response.text();
        const result = JSON.parse(text);

        console.log(result);

        document.getElementById('total-records').textContent = `Total registros: ${result.total}`;

        state.querySet = result.data;
        totalPages = Math.ceil(result.total / pageSize);

        buildTable();
    } catch (error) {
        console.error('Error al cargar los datos:', error);
        $('#table-body').append('<tr><td colspan="3">Error al cargar los datos</td></tr>');
    } finally {
        $('#loading-spinner').hide(); // Ocultar spinner
    } 
}

var state = {
    'querySet': [],
    'page': 1,
    'rows': 10,
    'window': 5,
}

fetchData(currentPage);

function pagination(querySet, page, rows) {            
    console.log('pagination');
    console.log('querySet: ' + querySet);

    return {
        'querySet': querySet,
        'pages': totalPages,
    }
}

function pageButtons(pages) {
    var wrapper = document.getElementById('pagination-wrapper');

    wrapper.innerHTML = ``;
    console.log('Pages:', pages);

    var maxLeft = (state.page - Math.floor(state.window / 2));
    var maxRight = (state.page + Math.floor(state.window / 2));

    if (maxLeft < 1) {
        maxLeft = 1;
        maxRight = state.window;
    }

    if (maxRight > pages) {
        maxLeft = pages - (state.window - 1);

        if (maxLeft < 1) {
            maxLeft = 1;
        }
        maxRight = pages;
    }

    for (var page = maxLeft; page <= maxRight; page++) {
        wrapper.innerHTML += `<button value=${page} class="page btn btn-sm btn-outline-secondary">${page}</button>`;
    }

    if (state.page != 1) {
        wrapper.innerHTML = `<button value=${1} class="page btn btn-sm btn-secondary">&#171; Primera</button>` + wrapper.innerHTML;
    }

    if (state.page != pages) {
        wrapper.innerHTML += `<button value=${pages} class="page btn btn-sm btn-secondary">Última &#187;</button>`;
    }

    $('.page').on('click', function () {
        $('#table-body').empty();
        state.page = Number($(this).val());
        fetchData(state.page);
    });
}

function buildTable() {
    var table = $('#table-body');
    table.empty(); // Limpia la tabla antes de volver a construirla

    var data = pagination(state.querySet, state.page, state.rows);
    var myList = data.querySet;

    for (var i in myList) {
        var item = myList[i];

        var row = `
            <tr class="main-row" onclick="toggleDetail(this)">
                <td>${item.numRegistro}</td>
                <td>${item.edad}</td>
                <td>${item.paisNacimientoNombre}</td>
                <td>${item.raza}</td>
                <td>${item.comunidadAutonomaNombre}</td>
                <td>${item.tipoAltaNombre}</td>
            </tr>
            <tr class="detail-row" style="display: none; font-size: 0.85em;">
                <td colspan="2">
                    Embarazo de alto riesgo: ${item.embarazoAltoRiesgo === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Esterilidad previa: ${item.esterilidadPrevia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Historia obstétrica adversa: ${item.historiaObstetricaAdversa === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Pérdida previa: ${item.perdidaPrevia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Aborto previo: ${item.abortoPrevio === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Muerte fetal previa: ${item.muerteFetalPrevia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Multípara: ${item.multipara === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Primípara: ${item.primipara === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Embarazo TRA: ${item.embarazoTra === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Embarazo TRA previo: ${item.embarazoTraPrevio === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Enfermedad cardiaca hipertensiva: ${item.enfermedadCardiacaHipertensiva === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Enfermedad renal crónica hipertensiva: ${item.enfermedadRenalCronicaHipertensiva === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Enfermedad cardiaca y renal crónica hipertensiva: ${item.enfermedadCardiacaYRenalCronicaHipertensiva === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Embarazo múltiple: ${item.embarazoMultiple === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Sobrepeso y obesidad: ${item.sobrepesoYObesidad === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Tabaco: ${item.tabaco === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Alcohol: ${item.alcohol === 1 ? "<span style='color: red;'>Sí</span>" : "No"}
                    Dislipemia: ${item.dislipemia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Neumopatía intersticial (genérica): ${item.neumopatiaIntersticialGenerica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    EAS intersticial (genérica): ${item.easIntersticialGenerica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Hipertensión pulmonar (genérica): ${item.hipertensionPulmonarGenerica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    ERC (coincide con Charlson): ${item.erc === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    IC (coincide con Charlson): ${item.ic === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    LES: ${item.les === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Nefritis lúpica: ${item.nefritisLupica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    LES-pulmón: ${item.lesPulmon === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br> 
                    SAF v1: ${item.safV1 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                </td>
                <td colspan="2">                       
                    SAF v2: ${item.safV2 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>                    
                    SAF v3: ${item.safV2 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Portador AAF v1: ${item.portadorAafV1 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Portador AAF v2: ${item.portadorAafV2 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Esclerosis sistémica: ${item.esclerosisSistemica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    SSc-respiratorio: ${item.sscRespiratorio === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Síndrome seco: ${item.sindromeSeco === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    SjS-respiratorio: ${item.sjsRespiratorio === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    SjS-tubulointersticial: ${item.sjsTubulointersticial === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    EMTC: ${item.emtc === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Enfermedad de Behçet: ${item.enfermedadBehcet === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Miopatía inflamatoria: ${item.miopatiaInflamatoria === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Vasculitis sistémica: ${item.vasculitisSistemica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Vasculitis ANCA: ${item.vasculitisAnca === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Sarcoidosis: ${item.sarcoidosis === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Artritis reumatoide: ${item.artritisReumatoide === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Artropatías enteropáticas: ${item.artropatiasEnteropaticas === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Artropatia psoriásica: ${item.artropatiaPsoriasica === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    EII: ${item.eii === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Enfermedad glomerular: ${item.enfermedadGlomerular === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Síndrome de Sjögren primario: ${item.sindromeDeSjogrenPrimario === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Antiagregación: ${item.antiagregacion === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Aspirina: ${item.aspirina === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Anticoagulación: ${item.anticoagulacion === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Esteroides: ${item.esteroides === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    COVID-19: ${item.covid19 === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>                    
                </td>
                <td colspan="2">
                    Neumonía COVID: ${item.neumoniaCovid === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Exitus: ${item.exitus === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Aborto: ${item.aborto === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Muerte fetal: ${item.muerteFetal === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    RN muerto: ${item.rnMuerto === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Muerte tardía: ${item.muerteTardia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    RN vivo: ${item.rnVivo === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    RN: ${item.rn === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Preclampsia: ${item.preclampsia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Preclampsia precoz: ${item.preclampsiaPrecoz === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Preclampsia grave: ${item.preclampsiaGrave === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Preclampsia grave precoz: ${item.preclampsiaGravePrecoz === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Preclampsia grave tardía: ${item.preclampsiaGraveTardia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Eclampsia: ${item.eclampsia === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    HELPP: ${item.helpp === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Ictus en PE: ${item.ictusPe === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Ictus hemorrágico en PE: ${item.ictusHemorragicoPe === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Ictus isquémico en PE: ${item.ictusIsquemicoPe === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    PE-criterios de gravedad: ${item.peCriteriosGravedad === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Parto prematuro-pretérmino (PPP): ${item.ppp === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Sufrimiento fetal: ${item.sufrimientoFetal === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    CIR-bajo peso: ${item.cirBajoPeso === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Cesárea: ${item.cesarea === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Rotura prematura de membranas: ${item.roturaPrematuraMembranas === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    Abruptio placentae: ${item.abruptioPlacentae === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    PE adverse maternal outcome: ${item.peAdverseMaternal === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                    PE-adverse fetal outcome: ${item.peAdverseFetal === 1 ? "<span style='color: red;'>Sí</span>" : "No"}<br>
                </td>
            </tr>
        `;
        table.append(row);
    }   

    pageButtons(data.pages);
}

// Función para mostrar/ocultar la fila de detalle
function toggleDetail(row) {
    var detailRow = $(row).next('.detail-row');
    detailRow.toggle();
}

function search() {
    state.page = 1;
    fetchData(state.page);
}

function generarQueryString() {
  const checkboxes = document.querySelectorAll('#collapseOne input[type="checkbox"]');
  const seleccionados = [];

  checkboxes.forEach(checkbox => {
    if (checkbox.checked) {
      seleccionados.push(checkbox.id);
    }
  });

  const params = new URLSearchParams();
  if (seleccionados.length > 0) {
    params.append('params', seleccionados.join(','));
  }

  const queryString = params.toString();
  console.log(queryString); // Puedes usarlo para redirigir, enviar por AJAX, etc.
  return queryString;
}
