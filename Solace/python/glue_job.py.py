import os
import json
import uuid
import boto3
from datetime import datetime

dynamo = boto3.resource('dynamodb')
table = dynamo.Table(os.environ['DDB_TABLE'])

def handler(event, context):
    for record in event.get('Records', []):
        payload = json.loads(record['body'])
        
        enriched = {
            "eventId": str(uuid.uuid4()),                  # unique hash ID
            "userId": payload.get("userId"),
            "ingestedAt": datetime.utcnow().isoformat(),    # ingestion timestamp
            "eventTimestamp": payload.get("timestamp"),
            "location": payload.get("location", {}),
            "timesPurchased": payload.get("timesPurchased", 0),
            "totalSpent": sum(item.get("price", 0) for item in payload.get("itemsPurchased", [])),
            
            # original details
            "itemsPurchased": payload.get("itemsPurchased", [])
        }
        
        # Persist enriched event
        table.put_item(Item=enriched)
    return {"status": "processed", "count": len(event.get("Records", []))}
