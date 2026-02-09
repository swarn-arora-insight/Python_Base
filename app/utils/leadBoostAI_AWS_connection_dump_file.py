import os
import boto3
import pandas as pd
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv
from core.logging import logger 
import time

# Load .env BEFORE reading AWS credentials
load_dotenv()
ATHENA_VAUTO_TABLE = os.getenv("ATHENA_VAUTO_TABLE")
ATHENA_CARGURU_TABLE = os.getenv("ATHENA_CARGURU_TABLE")
ATHENA_DRIVECENTRIC_TABLE = os.getenv("ATHENA_DRIVECENTRIC_TABLE")
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
    logger.info(f"Running Athena query: {query}")
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": athena_output},
    )
    logger.info(f"Query execution started-- {response}")
    logger.info(f"Query execution started: {response['QueryExecutionId']}")
    return response["QueryExecutionId"]


def wait_for_query(execution_id):
    while True:
        logger.info(f"Waiting for query execution: {execution_id}")
        status = athena.get_query_execution(QueryExecutionId=execution_id)
        state = status["QueryExecution"]["Status"]["State"]
        logger.info(f"Query execution state: {state}")

        if state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            return state
        time.sleep(1)
        logger.info("Waiting for query execution to complete...")
    

def athena_table_exists(database, table_name, athena_output):
    query = f"SHOW TABLES IN {database} LIKE '{table_name}'"
    execution_id = run_athena_query(query, database, athena_output)
    state = wait_for_query(execution_id)
    logger.info(f"Athena table check state: {state}")

    if state != "SUCCEEDED":
        logger.error(f"Athena table check failed: {state}")
        return False

    results = athena.get_query_results(QueryExecutionId=execution_id)
    rows = results.get("ResultSet", {}).get("Rows", [])

    # Extract actual table names returned
    table_names = [
        r["Data"][0].get("VarCharValue")
        for r in rows
        if r.get("Data") and len(r["Data"]) > 0 and r["Data"][0].get("VarCharValue")
    ]

    logger.info(f"SHOW TABLES returned: {table_names}")
    return table_name in table_names


def create_athena_drivecentric_table_if_not_exists(
    database, table_name, bucket, project_name, athena_output
):
    query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
        customer string,
        store_name string,
        vehicle_1_stock_number string,
        vehicle_1_year_make_model_trim string,
        deal_date_created string,
        current_stage string,
        next_task string,
        deal_sales_1 string,
        deal_bdc string,
        phone_count int,
        text_count int,
        email_count int,
        video_count int
    )
    PARTITIONED BY (
        year string,
        month string,
        day string,
        platform_name string
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/{project_name}/'

    """

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    logger.info(f"Athena table ensured: {table_name}")


def create_athena_carguru_table_if_not_exists(
    database, table_name, bucket, project_name, athena_output
):

    query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
        make string,
        model string,
        vehicle_year bigint,    
        trim string,
        type string,
        vin string,
        stock_id string,
        price double,
        deal_rating string,
        new_price double,
        new_deal_rating string,
        cargurus_imv double,
        price_change double,
        price_change_to_next_best_deal_rating double,
        price_at_next_deal_rating double,
        days_at_dealership bigint,
        days_on_cargurus bigint,
        saves double,
        recommended_price double,
        mds string,
        opportunity string,
        turn_time string,
        store string
    )
    PARTITIONED BY (
        year string,
        month string,
        day string,
        platform_name string
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/{project_name}/'
    """

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    logger.info(f"Athena table ensured: {table_name}")


def create_athena_vauto_table_if_not_exists(
    database, table_name, bucket, project_name, athena_output
):
    query = f"""
    CREATE EXTERNAL TABLE IF NOT EXISTS {database}.{table_name} (
        photo_thumbnail double,
        red_black string,
        certified string,
        autowriter_description string,
        tags string,
        recall_status_icon_small string,
        disp string,
        vehicle string,
        body string,
        stock_id string,
        vin string,
        odometer double,
        color string,
        interior_color string,
        req_fields_missing double,
        age bigint,
        price double,
        mkt_avg_price double,
        adjusted_pct_of_market double,
        adj_cost_to_market string,
        appraised_value double,
        appraiser string,
        book double,
        cost double,
        water double,
        markup double,
        kbb_fair_market_range_high string,
        last_change timestamp,
        overall double,
        like_mine double,
        price_rank_description string,
        vrank_description string,
        autotrader_list_price double,
        autotrader_odometer double,
        autotrader_image_count double,
        autotrader_srp double,
        autotrader_vdp double,
        autotrader_pct_vdp double,
        cars_list_price double,
        cars_odometer double,
        cars_image_count double,
        cars_srp double,
        cars_vdp double,
        cars_pct_vdp double,
        cargurus_list_price double,
        cargurus_odometer double,
        cargurus_image_count double,
        cargurus_srp double,
        cargurus_vdp double,
        cargurus_pct_vdp double,
        jd_power_trade_in_clean string,
        jd_power_trade_in_diff_clean string,
        vehicle_year bigint,
        make string,
        model string,
        store string
    )
    PARTITIONED BY (
        year string,
        month string,
        day string,
        platform_name string
    )
    STORED AS PARQUET
    LOCATION 's3://{bucket}/{project_name}/'
    """

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    logger.info(f"Athena table ensured: {table_name}")


def repair_athena_table(database, table_name, athena_output):
    query = f"MSCK REPAIR TABLE {table_name};"
    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)
    logger.info("Athena partition repair completed")


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

def drop_athena_table(database, table_name, athena_output):
    query = f"DROP TABLE IF EXISTS {database}.{table_name}"

    execution_id = run_athena_query(query, database, athena_output)
    wait_for_query(execution_id)

    logger.info(f"Athena table dropped: {database}.{table_name}")

def upload_df_to_s3_parquet(df: pd.DataFrame,bucket: str,project_name: str,database: str,table_name: str,athena_output: str,webpage: str):
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
    platform = "versionauction"
    if webpage == "vauto":
        platform = "vauto"
        filename = "versionauction_vauto_inventory_records"
    elif webpage == "cargurus":
        platform = "carguru"
        filename = "versionauction_carguru_inventory_records"
    elif webpage == "drivecentric":
        platform = "drive_centric"
        filename = "versionauction_drive_centric_inventory_records"
        # Normalize column names if needed
        df.columns = df.columns.str.strip()
        # logger.info(f"dtypes before conversion to deal date created and next task parquet:\n{df.dtypes}")
        for col in ["deal_date_created", "next_task"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

    s3_key = (
        f"{project_name}/"
        f"year={year}/month={month}/day={day}/platform_name={platform}/"
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
    # Ensure Athena database exists
    db_query = f"CREATE DATABASE IF NOT EXISTS {database}"
    db_execution_id = run_athena_query(db_query, "default", athena_output)
    wait_for_query(db_execution_id)
    logger.info(f"Athena database ensured: {database}")
    
    # # Drop Athena database
    # b_query = f"DROP DATABASE IF EXISTS {database}"
    # db_execution_id = run_athena_query(b_query, "default", athena_output)
    # wait_for_query(db_execution_id)
    # logger.info(f"Athena database dropped: {database}")

    if table_name == ATHENA_CARGURU_TABLE:
        # if athena_table_exists(database, table_name, athena_output):
        #     logger.info(f"Dropping Athena table: {table_name}")
        #     drop_athena_table(database, table_name, athena_output)

        if not athena_table_exists(database, table_name, athena_output):
            logger.info(f"Creating Athena table: {table_name}")
            create_athena_carguru_table_if_not_exists(database, table_name, bucket, project_name, athena_output)
    elif table_name == ATHENA_VAUTO_TABLE:
        # if athena_table_exists(database, table_name, athena_output):
        #     logger.info(f"Dropping Athena table: {table_name}")
        #     drop_athena_table(database, table_name, athena_output)

        if not athena_table_exists(database, table_name, athena_output):
            logger.info(f"Creating Athena table: {table_name}")
            create_athena_vauto_table_if_not_exists(database, table_name, bucket, project_name, athena_output)
    elif table_name == ATHENA_DRIVECENTRIC_TABLE:
        # if athena_table_exists(database, table_name, athena_output):
        #     logger.info(f"Dropping Athena table: {table_name}")
        #     drop_athena_table(database, table_name, athena_output)

        if not athena_table_exists(database, table_name, athena_output):
            logger.info(f"Creating Athena table: {table_name}")
            create_athena_drivecentric_table_if_not_exists(database, table_name, bucket, project_name, athena_output)        
    # Update Athena partitions
    try:
        logger.info(f"Repairing Athena partitions for table: {table_name}")
        repair_athena_table(database, table_name, athena_output)
    except Exception as e:
        logger.error(f"Athena repair failed (likely permission issue): {e}")

    BUCKET = "taverna-auto-job"
    KEY = f"leadBoostAI/year={year}/month={month}/day={day}/platform_name={platform}/{filename}.parquet"


    try:
        s3.head_object(Bucket=BUCKET, Key=KEY)
        logger.info("S3 parquet file exists")
    except Exception as e:
        logger.error("S3 parquet file NOT found", e)
    return s3_path




# s3://<bucket>/<project_name>/
#     └── year=YYYY/
#         └── month=MM/
#             └── day=DD/
#                 └── versionauction_inventory_records.parquet

# Example:
# s3://taverna-auto-job/leadBoostAI/
#     year=2026/month=01/day=21/versionauction_inventory_records.parquet


