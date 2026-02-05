import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dotenv import load_dotenv
from core.logging import logger
from utils.leadBoostAI_AWS_connection_dump_file import upload_df_to_s3_parquet
load_dotenv()

# Constants
NECESSARY_RENAME_MAP_DRIVECENTRIC = {}
NECESSARY_RENAME_MAP = {}
NECESSARY_RENAME_MAP_VAUTO = {
    "Photo Thumbnail": "photo_thumbnail",
    "Red/Black": "red_black",
    "Autowriter Description": "autowriter_description",
    "Recall Status Icon Small": "recall_status_icon_small",
    "Stock #": "stock_id",
    "Interior Color": "interior_color",
    "Req. Fields Missing": "req_fields_missing",
    "Adjusted % of Market": "adjusted_pct_of_market",
    "Adj Cost To Market": "adj_cost_to_market",
    "KBB.com Fair Market Range High": "kbb_fair_market_range_high",
    "Last $ Change": "last_change",

    # AutoTrader
    "AutoTrader.com List Price": "autotrader_list_price",
    "AutoTrader.com Odometer": "autotrader_odometer",
    "AutoTrader.com Image Count": "autotrader_image_count",
    "AutoTrader.com SRP": "autotrader_srp",
    "AutoTrader.com VDP": "autotrader_vdp",
    "AutoTrader.com % VDP": "autotrader_pct_vdp",

    # Cars.com
    "Cars.com List Price": "cars_list_price",
    "Cars.com Odometer": "cars_odometer",
    "Cars.com Image Count": "cars_image_count",
    "Cars.com SRP": "cars_srp",
    "Cars.com VDP": "cars_vdp",
    "Cars.com % VDP": "cars_pct_vdp",

    # CarGurus
    "CarGurus List Price": "cargurus_list_price",
    "CarGurus Odometer": "cargurus_odometer",
    "CarGurus Image Count": "cargurus_image_count",
    "CarGurus SRP": "cargurus_srp",
    "CarGurus VDP": "cargurus_vdp",
    "CarGurus % VDP": "cargurus_pct_vdp",

    # J.D. Power
    "J.D. Power Trade In Clean": "jd_power_trade_in_clean",
    "J.D. Power Trade In Diff Clean": "jd_power_trade_in_diff_clean",
}

NECESSARY_RENAME_MAP_CARGURUS = {
    "Year": "vehicle_year",  # vehicle year (avoid conflict with partition year)
    "Stock#": "stock_id",
    "Deal Rating": "deal_rating",
    "New Price": "new_price",
    "New Deal Rating": "new_deal_rating",
    "CarGurus IMV": "cargurus_imv",
    "Price Change": "price_change",
    "Price Change to Next Best Deal Rating": "price_change_to_next_best_deal_rating",
    "Price at Next Deal Rating": "price_at_next_deal_rating",
    "Days at Dealership": "days_at_dealership",
    "Days on CarGurus": "days_on_cargurus",
    "Recommended price": "recommended_price",
    "Turn time": "turn_time",
}

class DataProcessor:
    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET")
        self.project_name = os.getenv("S3_PROJECT_NAME")
        self.athena_db = os.getenv("ATHENA_DB")
        self.athena_output = os.getenv("ATHENA_OUTPUT")
        
        self.tables = {
            "vauto": os.getenv("ATHENA_VAUTO_TABLE"),
            "cargurus": os.getenv("ATHENA_CARGURU_TABLE"),
            "drivecentric": os.getenv("ATHENA_DRIVECENTRIC_TABLE")
        }

    def process_and_upload(self, webpage: str, base_dir: str) -> str:
        try:
            download_path = self._get_download_path(base_dir, webpage)
            latest_file = self._find_latest_file(download_path)
            
            if not latest_file:
                return ""

            df = self._read_file(latest_file)
            if df is None:
                return ""

            df = self._sanitize_dataframe(df)
            df = self._add_partitions(df)
            df = self._standardize_columns(df, webpage)

            # Local Validation Save
            self._save_local_validation(df, webpage, base_dir)

            # Upload
            table_name = self.tables.get(webpage)
            if not table_name:
                raise Exception(f"Unknown webpage: {webpage}")

            return upload_df_to_s3_parquet(
                df=df,
                bucket=self.bucket,
                project_name=self.project_name,
                database=self.athena_db,
                table_name=table_name,
                athena_output=self.athena_output,
                webpage=webpage
            )
            # return "uploaded successfully"

        except Exception as e:
            logger.error(f"Error processing/uploading to S3: {e}")
            raise e

    def _get_download_path(self, base_dir: str, webpage: str) -> str:
        if webpage in ["vauto", "cargurus", "drivecentric"]:
            return os.path.join(base_dir, "downloads", webpage)
        return os.path.join(base_dir, "downloads", "other")

    def _find_latest_file(self, download_path: str) -> Optional[str]:
        list_of_files = glob.glob(os.path.join(download_path, "*"))
        logger.info(f"List of files found: {len(list_of_files)}")
        
        if not list_of_files:
            logger.warning("No files found in downloads directory to upload.")
            return None

        # Filter out temporary or unwanted files just in case
        valid_files = [f for f in list_of_files if not f.endswith('.tmp') and not f.endswith('.crdownload')]
        if not valid_files:
             logger.warning("No valid files found (filtered out tmp/crdownload).")
             return None

        latest_file = max(valid_files, key=os.path.getctime)
        logger.info(f"Latest file found: {latest_file}")
        return latest_file

    def _read_file(self, file_path: str) -> Optional[pd.DataFrame]:
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.endswith(".xls"):
            logger.info("xls file found")
            xlsx_path = file_path.replace(".xls", ".xlsx")
            # Convert xls to xlsx
            try:
                df = pd.read_excel(file_path, engine="xlrd")
                df.to_excel(xlsx_path, index=False, engine="openpyxl")
                return pd.read_excel(xlsx_path)
            except Exception as e:
                logger.error(f"Error converting xls: {e}")
                return None
        elif file_path.endswith(".xlsx"):
            return pd.read_excel(file_path)
        else:
            logger.warning(f"Unsupported file format: {file_path}")
            return None

    def _sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = (
                    df[col]
                    .astype(str)
                    .replace("nan", None)
                )
                logger.info(f"Column '{col}' normalized as STRING")
        return df

    def _add_partitions(self, df: pd.DataFrame) -> pd.DataFrame:
        now = datetime.utcnow()
        year = now.year
        month = f"{now.month:02d}"
        day = f"{now.day:02d}"

        for col in ["year", "month", "day"]:
            if col not in df.columns:
                logger.info(f"Adding empty column: {col}")
                df[col] = None

        logger.info(f"Adding partition columns: Year: {year}, Month: {month}, Day: {day}")
        df["year"] = year
        df["month"] = month
        df["day"] = day
        return df

    def _standardize_columns(self, df: pd.DataFrame, webpage: str) -> pd.DataFrame:
        # Initial Rename for Stock#
        if "stock#" in df.columns.str.lower() or "stock #" in df.columns.str.lower():
            df.rename(columns={"stock#": "stock_id"}, inplace=True)
            logger.info("Renamed 'stock#' column to 'stock_id'")

        # Clean Column Names
        df.columns = (
            df.columns
            .astype(str)
            .str.replace("\n", " ")
            .str.replace("\r", " ")
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )

        if webpage == "cargurus":
            df = df.rename(columns=NECESSARY_RENAME_MAP_CARGURUS)
            df.columns = df.columns.str.lower()

            MONEY_COLUMNS = [
                "price", "new_price", "cargurus_imv", "price_change",
                "price_change_to_next_best_deal_rating",
                "price_at_next_deal_rating", "recommended_price"
            ]

            for col in MONEY_COLUMNS:
                if col in df.columns:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace(r"[\$,]", "", regex=True)
                        .str.strip()
                        .replace({"": np.nan, "nan": np.nan})
                    )
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            
            # Print dtypes for debugging
            print(df[MONEY_COLUMNS].dtypes)

        elif webpage == "vauto":
            df = df.rename(columns=NECESSARY_RENAME_MAP_VAUTO)
            df["store"] = "Taverna INFINITI North Miami - MP6497"
        
        elif webpage == "drivecentric":
            df = df.rename(columns=NECESSARY_RENAME_MAP_DRIVECENTRIC)
        
        else:
            df = df.rename(columns=NECESSARY_RENAME_MAP)
        
        return df

    def _save_local_validation(self, df: pd.DataFrame, webpage: str, base_dir: str):
        validated_path = os.path.join(base_dir, "validated", webpage)
        os.makedirs(validated_path, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        local_csv = os.path.join(validated_path, f"{webpage}_validated_{timestamp}.csv")
        local_parquet = os.path.join(validated_path, f"{webpage}_validated_{timestamp}.parquet")

        df.to_csv(local_csv, index=False)
        df.to_parquet(local_parquet, index=False)

        logger.info(f"Local CSV saved for validation: {local_csv}")
        logger.info(f"Local Parquet saved for validation: {local_parquet}")
