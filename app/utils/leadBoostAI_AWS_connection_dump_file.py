
#####################################################

import os
import boto3
import pandas as pd
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from core.logging import logger 

# Load .env BEFORE reading AWS credentials
load_dotenv()

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

def run_athena_query(query, database, athena_output):
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": athena_output},
    )
    return response["QueryExecutionId"]


def wait_for_query(execution_id):
    while True:
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status["QueryExecution"]["Status"]["State"]

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            return state
        time.sleep(1)


def athena_table_exists(database, table_name, athena_output):
    query = f"SHOW TABLES IN {database} LIKE '{table_name}';"
    execution_id = run_athena_query(query, database, athena_output)
    state = wait_for_query(execution_id)

    if state != "SUCCEEDED":
        return False

    results = athena.get_query_results(QueryExecutionId=execution_id)
    return len(results["ResultSet"]["Rows"]) > 1


def create_athena_table_if_not_exists22(
    database, table_name, bucket, project_name, athena_output
):
    query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
        make string,
        model string,
        year int,
        trim string,
        type string,
        vin string,
        stock# string,

        price string,
        deal_rating string,
        new_price string,
        new_deal_rating string,

        cargurus_imv string,
        price_change string,
        price_change_to_next_best_deal_rating string,
        price_at_next_deal_rating string,

        days_at_dealership int,
        days_on_cargurus int,
        saves int,

        recommended_price string,
        mds string,
        opportunity string,
        turn_time string,
        store string
    )
    PARTITIONED BY (
        year string,
        month string,
        day string
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/{project_name}/'
    """

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    print(f"🆕 Athena table ensured: {table_name}")


def create_athena_table_if_not_exists(
    database, table_name, bucket, project_name, athena_output
):
    query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
    red_black string,

    carfax_has_report string,
    carfax_has_manufacturer_recall string,
    carfax_has_warnings string,
    carfax_has_problems string,

    certified string,
    tags string,

    vehicle string,
    body string,
    stock_number string,
    vin string,

    odometer bigint,
    color string,
    age int,

    price string,
    mkt_avg_price string,

    adjusted_pct_of_market string,
    adj_cost_to_market string,

    appraised_value string,
    appraiser string,
    book string,
    cost string,
    water string,
    markup string,
    last_change string,

    overall int,
    like_mine int,

    price_rank_description string,
    vrank_description string,

    autotrader_list_price string,
    autotrader_odometer bigint,
    autotrader_image_count int,
    autotrader_srp int,
    autotrader_vdp int,
    autotrader_pct_vdp string,

    cars_list_price string,
    cars_odometer bigint,
    cars_image_count int,
    cars_srp int,
    cars_vdp int,
    cars_pct_vdp string,

    provisioning_grade string
    )
    PARTITIONED BY (
        year string,
        month string,
        day string
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/{project_name}/'  
    
    """

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    print(f"🆕 Athena table ensured: {table_name}")


def repair_athena_table(database, table_name, athena_output):
    query = f"MSCK REPAIR TABLE {table_name};"
    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    print("🔄 Athena partition repair completed")


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

    # #  Ensure Athena table exists
    # if not athena_table_exists(database, table_name, athena_output):
    #     create_athena_table_if_not_exists(database, table_name, bucket, project_name, athena_output)
    
    # # Update Athena partitions
    # try:
    #     repair_athena_table(database, table_name, athena_output)
    # except Exception as e:
    #     logger.error(f"Athena repair failed (likely permission issue): {e}")
    #     # We don't raise here because the S3 upload was successful
    #     # and checking Athena permissions might be out of user's immediate control.
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


