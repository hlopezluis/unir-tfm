import os
import pandas as pd
import numpy as np
import json
from pymongo import MongoClient

def lambda_handler(event, context):  
    try:
        print("Evento recibido:", event)

        query_params = event.get('queryStringParameters', {})

        page = int(query_params.get('page', 1))
        pageSize = int(query_params.get('pageSize', 10))
        skip = (page - 1) * pageSize

        client = MongoClient(host=os.environ.get("ATLAS_URI"))

        db = client.tfm
        collection = db.raecmbd

        total = collection.count_documents({})

        documents = list(
            collection.find({}, {'_id': 0})
            .skip(skip)
            .limit(pageSize)
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'data': documents,
                'total': total
            })
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
