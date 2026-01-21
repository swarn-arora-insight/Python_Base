
#####################################################

import os
import boto3
import pandas as pd
from datetime import datetime
from io import BytesIO
from core.logging import logger 

aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
region_name = "us-east-2"

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_access_key,
    region_name=region_name
)

s3 = session.client("s3")
athena = session.client("athena")

def repair_athena_table(database, table_name, athena_output):
    query = f"MSCK REPAIR TABLE {table_name};"
    logger.info(f"Query: {query}")
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": athena_output}
    )

    logger.info("Athena partition repair started")
    return response["QueryExecutionId"]

def upload_df_to_s3_parquet(df: pd.DataFrame,bucket: str,project_name: str,database: str,table_name: str,athena_output: str):
    """
    Upload dataframe to S3 in partitioned parquet format
    and update Athena partitions
    """
    # print("df",df)
    # Date partitions
    now = datetime.utcnow()
    year = now.year
    month = f"{now.month:02d}"
    day = f"{now.day:02d}"
    logger.info(f"Year: {year}")
    logger.info(f"Month: {month}")
    logger.info(f"Day: {day}")    
    filename = "versionauction_inventory_records"

    s3_key = (
        f"{project_name}/"
        f"year={year}/month={month}/day={day}/"
        f"{filename}.parquet"
    )
    logger.info(f"S3 Key: {s3_key}")
    s3_path = f"s3://{bucket}/{s3_key}"
    logger.info(f"S3 Path: {s3_path}")
    # Convert DF → Parquet in memory
    buffer = BytesIO()
    df.to_parquet(buffer, engine="pyarrow", index=False)
    buffer.seek(0)

    # Upload to S3
    s3.put_object(
        Bucket=bucket,
        Key=s3_key,
        Body=buffer.getvalue()
    )

    logger.info(f"Uploaded parquet to {s3_path}")

    # Update Athena partitions
    try:
        repair_athena_table(database, table_name, athena_output)
    except Exception as e:
        logger.error(f"Athena repair failed (likely permission issue): {e}")
        # We don't raise here because the S3 upload was successful
        # and checking Athena permissions might be out of user's immediate control.
    BUCKET = "taverna-auto-job"
    KEY = "leadBoostAI/year=2026/month=01/day=21/versionauction_inventory_records.parquet"

    try:
        s3.head_object(Bucket=BUCKET, Key=KEY)
        logger.info("S3 parquet file exists")
    except Exception as e:
        logger.error("S3 parquet file NOT found", e)
    return s3_path


# if __name__ == "__main__":

#     ## Write filepath where file get download
#     FILEPATH = r""
#     df = pd.read_csv(FILEPATH)

#     BUCKET = "taverna-auto-job"
#     PROJECT_NAME = "leadBoostAI"
#     ATHENA_DB = "leadboost_db"
#     ATHENA_TABLE = "leadboost_table"
#     ATHENA_OUTPUT = "s3://taverna-auto-job/leadBoostAI/athena-results/"

#     upload_df_to_s3_parquet(
#         df=df,
#         bucket=BUCKET,
#         project_name=PROJECT_NAME,
#         database=ATHENA_DB,
#         table_name=ATHENA_TABLE,
#         athena_output=ATHENA_OUTPUT
#     )







# s3://<bucket>/<project_name>/
#     └── year=YYYY/
#         └── month=MM/
#             └── day=DD/
#                 └── versionauction_inventory_records.parquet

# Example:
# s3://taverna-auto-job/leadBoostAI/
#     year=2026/month=01/day=21/versionauction_inventory_records.parquet


