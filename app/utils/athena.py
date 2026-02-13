import boto3
import time
import os
from core.logging import logger

def get_athena_client():
    return boto3.client(
        "athena",
        region_name=os.getenv("AWS_REGION", "us-east-2"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def run_athena_query(query, database, output_location):
    client = get_athena_client()
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": output_location},
    )
    return response["QueryExecutionId"]

def wait_for_query(execution_id):
    client = get_athena_client()
    while True:
        response = client.get_query_execution(QueryExecutionId=execution_id)
        state = response["QueryExecution"]["Status"]["State"]
        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            return state
        time.sleep(1)

def get_query_results(execution_id):
    client = get_athena_client()
    response = client.get_query_results(QueryExecutionId=execution_id)
    
    # Process results into a list of dicts
    # This is a basic implementation; might need refinement for complex types
    column_info = response['ResultSet']['ResultSetMetadata']['ColumnInfo']
    rows = response['ResultSet']['Rows']
    
    results = []
    # Skip header row if present (Athena usually includes it in the first row)
    if not rows:
        return results
        
    headers = [col['Label'] for col in column_info]
    
    # Start from index 1 to skip header row
    for row in rows[1:]:
        data = row.get('Data', [])
        row_dict = {}
        for i, val in enumerate(data):
            # Handle potential missing values or varying structures
            value = val.get('VarCharValue')
            row_dict[headers[i]] = value
        results.append(row_dict)
        
    return results
