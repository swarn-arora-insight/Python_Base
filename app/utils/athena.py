# import boto3
# import time
# import os
# from core.logging import logger

# def get_athena_client():
#     return boto3.client(
#         "athena",
#         region_name=os.getenv("AWS_REGION", "us-east-2"),
#         aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
#         aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
#     )

# # def run_athena_query(query, database, output_location):
# #     client = get_athena_client()
# #     response = client.start_query_execution(
# #         QueryString=query,
# #         QueryExecutionContext={"Database": database},
# #         ResultConfiguration={"OutputLocation": output_location},
# #     )
# #     return response["QueryExecutionId"]

# # def wait_for_query(execution_id):
# #     client = get_athena_client()
# #     while True:
# #         response = client.get_query_execution(QueryExecutionId=execution_id)
# #         state = response["QueryExecution"]["Status"]["State"]
# #         if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
# #             return state
# #         time.sleep(1)

# # def get_query_results(execution_id):
# #     client = get_athena_client()
# #     response = client.get_query_results(QueryExecutionId=execution_id)
    
# #     # Process results into a list of dicts
# #     # This is a basic implementation; might need refinement for complex types
# #     column_info = response['ResultSet']['ResultSetMetadata']['ColumnInfo']
# #     rows = response['ResultSet']['Rows']
    
# #     results = []
# #     # Skip header row if present (Athena usually includes it in the first row)
# #     if not rows:
# #         return results
        
# #     headers = [col['Label'] for col in column_info]
    
# #     # Start from index 1 to skip header row
# #     for row in rows[1:]:
# #         data = row.get('Data', [])
# #         row_dict = {}
# #         for i, val in enumerate(data):
# #             # Handle potential missing values or varying structures
# #             value = val.get('VarCharValue')
# #             row_dict[headers[i]] = value
# #         results.append(row_dict)
        
# #     return results












import boto3
import time
import os
from core.logging import logger
from typing import List, Dict, Any

def get_athena_client():
    return boto3.client(
        "athena",
        region_name=os.getenv("AWS_REGION", "us-east-2"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

def run_athena_query(query: str, database: str, output_location: str) -> str:
    client = get_athena_client()
    # logger.info(f"Running Athena query: {query}")
    resp = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": output_location},
    )
    return resp["QueryExecutionId"]

def wait_for_query(execution_id: str, poll_seconds: float = 0.75, timeout_seconds: int = 300) -> str:
    client = get_athena_client()
    start = time.time()

    while True:
        resp = client.get_query_execution(QueryExecutionId=execution_id)
        status = resp["QueryExecution"]["Status"]["State"]

        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            return status

        if time.time() - start > timeout_seconds:
            raise TimeoutError(f"Athena query timed out after {timeout_seconds}s: {execution_id}")

        time.sleep(poll_seconds)

def get_query_results(execution_id: str, page_size: int = 1000) -> list[dict]:
    """
    ✅ Pagination-safe: fetches ALL pages using NextToken.
    Returns list[dict] with column names as keys.
    Skips the header row (only present on first page).
    """
    client = get_athena_client()

    results: list[dict] = []
    next_token = None
    columns = None
    first_page = True

    while True:
        kwargs = {"QueryExecutionId": execution_id, "MaxResults": page_size}
        if next_token:
            kwargs["NextToken"] = next_token

        resp = client.get_query_results(**kwargs)

        rs = resp.get("ResultSet", {})
        rows = rs.get("Rows", [])

        # Column names
        if columns is None:
            colinfo = rs.get("ResultSetMetadata", {}).get("ColumnInfo", [])
            columns = [c.get("Name") for c in colinfo]

        # Skip header row only for first page
        start_idx = 1 if first_page else 0

        for r in rows[start_idx:]:
            data = r.get("Data", [])
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = data[i].get("VarCharValue") if i < len(data) else None
            results.append(row_dict)

        first_page = False
        next_token = resp.get("NextToken")
        if not next_token:
            break

    return results

def run_athena_query_blocking(query: str, database: str, output_location: str) -> List[Dict[str, Any]]:
    execution_id = run_athena_query(query, database, output_location)
    state = wait_for_query(execution_id)
    if state == "SUCCEEDED":
        return get_query_results(execution_id)
    return [] 











# # utils/athena.py
# import time
# import boto3

# athena = boto3.client("athena")

# def run_athena_query(query: str, database: str, output_location: str) -> str:
#     """
#     Starts an Athena query and returns QueryExecutionId.
#     """
#     resp = athena.start_query_execution(
#         QueryString=query,
#         QueryExecutionContext={"Database": database},
#         ResultConfiguration={"OutputLocation": output_location},
#     )
#     return resp["QueryExecutionId"]


# def wait_for_query(execution_id: str, poll_seconds: float = 0.75, timeout_seconds: int = 300) -> str:
#     """
#     Waits for Athena query to complete and returns final state.
#     """
#     start = time.time()
#     while True:
#         resp = athena.get_query_execution(QueryExecutionId=execution_id)
#         status = resp["QueryExecution"]["Status"]["State"]

#         if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
#             return status

#         if (time.time() - start) > timeout_seconds:
#             raise TimeoutError(f"Athena query timed out after {timeout_seconds}s: {execution_id}")

#         time.sleep(poll_seconds)


# def get_query_results(execution_id: str, max_results: int = 1000) -> list[dict]:
#     """
#     Fetches ALL rows from Athena result set using pagination.
#     Returns list[dict] where dict keys are column names.
#     Skips the header row.
#     """
#     results: list[dict] = []
#     next_token = None
#     columns = None
#     first_page = True

#     while True:
#         kwargs = {"QueryExecutionId": execution_id, "MaxResults": max_results}
#         if next_token:
#             kwargs["NextToken"] = next_token

#         resp = athena.get_query_results(**kwargs)
#         rs = resp["ResultSet"]
#         rows = rs.get("Rows", [])

#         # Column names (from ResultSetMetadata)
#         if columns is None:
#             meta = rs.get("ResultSetMetadata", {})
#             colinfo = meta.get("ColumnInfo", [])
#             columns = [c.get("Name") for c in colinfo]

#         # Convert rows -> dict
#         # Athena's first row is header row (only on the first page)
#         start_index = 1 if first_page else 0
#         for r in rows[start_index:]:
#             data = r.get("Data", [])
#             item = {}
#             for i, col in enumerate(columns):
#                 # Some rows can have fewer columns, handle safely
#                 val = data[i].get("VarCharValue") if i < len(data) else None
#                 item[col] = val
#             results.append(item)

#         first_page = False
#         next_token = resp.get("NextToken")
#         if not next_token:
#             break

#     return results

