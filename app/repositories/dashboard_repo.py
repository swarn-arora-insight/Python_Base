from utils.athena import run_athena_query, wait_for_query, get_query_results
import os
from core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

# class DashboardRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db
#         self.athena_db = os.getenv("ATHENA_DB", "leadboost_db")
#         self.s3_bucket = os.getenv("S3_BUCKET", "taverna-auto-job")
#         self.s3_project_name = os.getenv("S3_PROJECT_NAME", "leadBoostAI")
#         self.athena_output = f"s3://{self.s3_bucket}/{self.s3_project_name}/output/"
#         self.athena_vauto_table = os.getenv("ATHENA_VAUTO_TABLE", "vauto_inventry")
#         self.athena_carguru_table = os.getenv("ATHENA_CARGURU_TABLE", "carguru_inventry")
#         self.athena_drivecentric_table = os.getenv("ATHENA_DRIVECENTRIC_TABLE", "drivecentric_inventry")
        
#     async def get_data(self):
#         # Placeholder for data fetching logic
#         return {}

#     async def get_vauto_body_details(self):
#         query = f"SELECT DISTINCT body FROM {self.athena_vauto_table} WHERE platform_name = 'vauto'"
#         logger.info(f"Running Athena query: {query}")
        
#         try:
#             execution_id = run_athena_query(query, self.athena_db, self.athena_output)
#             state = wait_for_query(execution_id)
            
#             if state == "SUCCEEDED":
#                 results = get_query_results(execution_id)
#                 # Extract just the body names for a cleaner list, or return as is
#                 # Returning list of strings for "body"
#                 bodies = [item.get("body") for item in results if item.get("body")]
#                 return sorted(bodies)
#             else:
#                 logger.error(f"Athena query failed with state: {state}")
#                 return []
#         except Exception as e:
#             logger.error(f"Error fetching vauto body details: {str(e)}")
#             return []

#     async def get_vauto_store_details(self):
#         # query = f"SELECT DISTINCT store FROM {self.athena_vauto_table} WHERE platform_name = 'vauto'"
#         query = f"SELECT DISTINCT store FROM {self.athena_vauto_table}"
#         logger.info(f"Running Athena query: {query}")
        
#         try:
#             execution_id = run_athena_query(query, self.athena_db, self.athena_output)
#             state = wait_for_query(execution_id)
            
#             if state == "SUCCEEDED":
#                 results = get_query_results(execution_id)
#                 stores = [item.get("store") for item in results if item.get("store")]
#                 return sorted(stores)
#             else:
#                 logger.error(f"Athena query failed with state: {state}")
#                 return []
#         except Exception as e:
#             logger.error(f"Error fetching vauto store details: {str(e)}")
#             return []

#     async def get_filtered_data(self, filters: dict):
#         day = str(datetime.now().day)
#         # day = "15"
#         base_query = f"SELECT * FROM {self.athena_vauto_table} WHERE day = '{day}'"
#         conditions = []
        
#         # Mapping: Schema Field -> Athena Column
#         # body_type -> body
#         if filters.get("body_type") != "":
#             conditions.append(f"body = '{filters['body_type']}'")
        
#         # store -> store
#         if filters.get("store") != "":
#              conditions.append(f"store = '{filters['store']}'")
             
#         # vin -> vin
#         if filters.get("vin") != "":
#             conditions.append(f"vin = '{filters['vin']}'")
            
#         # demand_level -> Skipped for now
#         # leads_per_day -> Skipped for now
        
#         if conditions:
#             base_query += " AND " + " AND ".join(conditions)
            
#         logger.info(f"Running Athena query: {base_query}")
        
#         try:
#             execution_id = run_athena_query(base_query, self.athena_db, self.athena_output)
#             state = wait_for_query(execution_id)
            
#             if state == "SUCCEEDED":
#                 results = get_query_results(execution_id)
#                 return results
#             else:
#                 logger.error(f"Athena query failed with state: {state}")
#                 return []
#         except Exception as e:
#             logger.error(f"Error fetching filtered data: {str(e)}")
#             return []


# from utils.athena import run_athena_query, wait_for_query, get_query_results
# import os
# from core.logging import logger
# # import datetime
# from datetime import datetime, timedelta

# from sqlalchemy.ext.asyncio import AsyncSession

# class DashboardRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db
#         self.athena_db = os.getenv("ATHENA_DB", "leadboost_db")
#         self.s3_bucket = os.getenv("S3_BUCKET", "taverna-auto-job")
#         self.s3_project_name = os.getenv("S3_PROJECT_NAME", "leadBoostAI")
#         self.athena_output = f"s3://{self.s3_bucket}/{self.s3_project_name}/output/"
        
#         # Table configurations
#         self.athena_vauto_table = os.getenv("ATHENA_VAUTO_TABLE", "vauto_inventry")
#         self.athena_carguru_table = os.getenv("ATHENA_CARGURU_TABLE", "carguru_inventry")
#         self.athena_drivecentric_table = os.getenv("ATHENA_DRIVECENTRIC_TABLE", "drivecentric_inventry")

#     def _sanitize(self, value):
#         """Helper to escape single quotes to prevent SQL syntax errors."""
#         if isinstance(value, str):
#             return value.replace("'", "''")
#         return value

#     async def _execute_query(self, query):
#         """
#         Centralized method to run, wait, and fetch Athena results.
#         Handles all logging and error catching here.
#         """
#         logger.info(f"Running Athena query: {query}")
#         try:
#             execution_id = run_athena_query(query, self.athena_db, self.athena_output)
#             state = wait_for_query(execution_id)

#             if state == "SUCCEEDED":
#                 return get_query_results(execution_id)
#             else:
#                 logger.error(f"Athena query failed with state: {state}")
#                 return []
#         except Exception as e:
#             logger.error(f"Athena Execution Error: {str(e)} | Query: {query}")
#             return []

#     async def fetch_dynamic_data(self, table: str, columns: list, filters: dict = None, distinct: bool = False):
#         """
#         Dynamically builds and executes a query.
        
#         Args:
#             table (str): The table name.
#             columns (list): List of column names to select (e.g. ['body', 'store']).
#             filters (dict): Key-value pairs for WHERE clause (e.g. {'store': 'ABC'}).
#             distinct (bool): Whether to use SELECT DISTINCT.
#         """
#         # 1. Build SELECT clause
#         col_str = ", ".join(columns)
#         select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
#         query = f"{select_prefix} {col_str} FROM {table}"

#         # 2. Build WHERE clause
#         if filters:
#             conditions = ["platform_name = 'vauto'"]
#             for col, val in filters.items():
#                 if val is not None and val != "":
#                     # Sanitize and quote the value
#                     clean_val = self._sanitize(val)
#                     conditions.append(f"{col} = '{clean_val}'")
            
#             if conditions:
#                 query += " WHERE " + " AND ".join(conditions)

#         # 3. Execute
#         return await self._execute_query(query)


#     async def fetch_dynamic_data2(self, table: str, columns: list, filters: dict = None, distinct: bool = False, extra_conditions: list = None):
#         """
#         Dynamically builds and executes a query.
        
#         Args:
#             table (str): The table name.
#             columns (list): List of column names to select (e.g. ['body', 'store']).
#             filters (dict): Key-value pairs for WHERE clause (e.g. {'store': 'ABC'}).
#             distinct (bool): Whether to use SELECT DISTINCT.
#             extra_conditions (list): List of raw SQL condition strings to append.
#         """
#         # 1. Build SELECT clause
#         col_str = ", ".join(columns)
#         select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
#         query = f"{select_prefix} {col_str} FROM {table}"

#         # 2. Build WHERE clause
#         conditions = ["platform_name = 'vauto'"]
        
#         if filters:
#             for col, val in filters.items():
#                 if val is not None and val != "":
#                     # Sanitize and quote the value
#                     clean_val = self._sanitize(val)
#                     conditions.append(f"{col} = '{clean_val}'")
#         # extra_conditions = [f"(year = '2026' AND month = '02' AND day = '13')"]
#         if extra_conditions:
#             conditions.extend(extra_conditions)
            
#         if conditions:
#             query += " WHERE " + " AND ".join(conditions)

#         # 3. Execute
#         logger.info(f"Executing query: {query}")
#         return await self._execute_query(query)



#     async def get_data(self):
#         # Placeholder
#         return {}

#     async def get_body_types(self):
#         # Reuses the generic function
#         results = await self.fetch_dynamic_data(
#             table=self.athena_vauto_table,
#             columns=["body"],
#             filters={"platform_name": "vauto"}, # Optional: Keep if you need this filter
#             distinct=True
#         )
#         # Flatten list: [{'body': 'SUV'}, {'body': 'Sedan'}] -> ['SUV', 'Sedan']
#         bodies = [item.get("body") for item in results if item.get("body")]
#         return sorted(bodies)

#     async def get_stores(self):
#         # Reuses the generic function
#         results = await self.fetch_dynamic_data(
#             table=self.athena_vauto_table,
#             columns=["store"],
#             distinct=True
#         )
#         stores = [item.get("store") for item in results if item.get("store")]
#         return sorted(stores)

#     async def get_filtered_data(self, filters: dict):
#         # 1. Map frontend filter keys to Database Column names
#         today = datetime.now()
#         # Testing: last week
#         today = datetime.now()
#         start_of_current_week = today - timedelta(days=today.weekday())  # This Monday
#         start_of_last_week = start_of_current_week - timedelta(days=7)   # Last Monday
        
#         date_conditions = []
        
#         # Generate date conditions for 14 days (Last Week + Current Week)
#         # We iterate 14 days starting from LAST week's Monday
#         for i in range(14):
#             day_date = start_of_last_week + timedelta(days=i)
#             y = str(day_date.year)
#             m = day_date.strftime('%m')
#             # Assuming Athena uses single digit for days < 10 based on '1', '2' etc? 
#             # Previous code used str(day_date.day). format(day_date.day) is safer if it's not zero-padded.
#             # But the user code `m = day_date.strftime('%m')` implies 0-padded.
#             # Let's stick to what was working or standard.
#             # If `d = day_date.strftime('%d')` (01-31) was used in recent user edit, I will stick to it.
#             # Re-checking user edit: `d = day_date.strftime('%d')`. OK.
#             d = day_date.strftime('%d')
#             date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

#         date_query_part = " OR ".join(date_conditions)
#         # logger.info(f"Date query part: {date_query_part}")

#         # Key = DB Column, Value = Filter Value
#         query_filters = {
#             "body": filters.get("body_type"),
#             "store": filters.get("store"),
#             "vin": filters.get("vin")
#         }
        
#         # 2. Call the generic function to get vAuto data
#         vauto_results = await self.fetch_dynamic_data2(
#             table=self.athena_vauto_table,
#             columns=["*"],
#             filters=query_filters,
#             extra_conditions=[f"({date_query_part})"]
#         )
        
#         # 3. Extract stock IDs
#         stock_ids = [item.get("stock_id") for item in vauto_results if item.get("stock_id")]
#         logger.info(f"Extracted stock IDs: {len(stock_ids)}")
        
#         total_leads_current = 0
#         avg_leads_current = 0
#         total_leads_pct = 0
#         avg_leads_pct = 0

#         # 4. If we have stock IDs, fetch DriveCentric data
#         if stock_ids:
#             logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks")
#             sanitized_stocks = [self._sanitize(s) for s in stock_ids]
#             stock_list_str = "', '".join(sanitized_stocks)
            
#             drivecentric_query = f"""
#                 SELECT vehicle_1_stock_number, current_stage, year, month, day
#                 FROM {self.athena_drivecentric_table} 
#                 WHERE vehicle_1_stock_number IN ('{stock_list_str}') 
#                 AND platform_name = 'drive_centric' 
#                 AND ({date_query_part})
#             """
            
#             logger.info(f"Fetching DriveCentric data (2 Weeks)")
#             drivecentric_results = await self._execute_query(drivecentric_query)
#             logger.info(f"DriveCentric results count: {len(drivecentric_results)}")

#             # Helper to parse date from row
#             def get_date(row):
#                 try:
#                     return datetime(int(row.get('year', 0)), int(row.get('month', 1)), int(row.get('day', 1)))
#                 except:
#                     return datetime.min

#             # --- Segregate Data ---
#             current_week_data = []
#             last_week_data = []
            
#             # Use strict comparison relying on the date object
#             # start_of_current_week has time 00:00:00.
#             for item in drivecentric_results:
#                 item_date = get_date(item)
#                 if item_date >= start_of_current_week:
#                     current_week_data.append(item)
#                 elif item_date >= start_of_last_week:
#                     last_week_data.append(item)
            
#             # --- Helper to Calculate Metrics for a Data Set ---
#             def calculate_metrics_for_set(data_set):
#                 # 1. Avg Leads Logic (Count 'Lead' instances per day sum / 7)
#                 daily_leads_sum = 0
#                 for item in data_set:
#                     stage = str(item.get("current_stage", "")).lower()
#                     if stage == "lead":
#                         daily_leads_sum += 1
#                 avg = round(daily_leads_sum / 7, 1)

#                 # 2. Total Leads Logic (Latest Snapshot)
#                 # Sort by date ASC
#                 sorted_data = sorted(data_set, key=get_date)
#                 # Lookup dict (latest status wins)
#                 lookup = {item.get("vehicle_1_stock_number"): item.get("current_stage") for item in sorted_data if item.get("vehicle_1_stock_number")}
#                 # Count current leads
#                 total = sum(1 for stage in lookup.values() if str(stage).lower() == "lead")
                
#                 return total, avg, lookup

#             # Calculate for Current Week
#             total_leads_current, avg_leads_current, current_lookup = calculate_metrics_for_set(current_week_data)
            
#             # Calculate for Last Week
#             total_leads_last, avg_leads_last, _ = calculate_metrics_for_set(last_week_data)
            
#             logger.info(f"Current Week: Total={total_leads_current}, Avg={avg_leads_current}")
#             logger.info(f"Last Week: Total={total_leads_last}, Avg={avg_leads_last}")

#             # --- Calculate Percentages ---
#             def calc_pct(current, last):
#                 if last == 0:
#                     return 100 if current > 0 else 0
#                 diff = current - last
#                 return round((diff / last) * 100, 1)

#             total_leads_pct = calc_pct(total_leads_current, total_leads_last)
#             avg_leads_pct = calc_pct(avg_leads_current, avg_leads_last)

#             # 5. Merge current_week logic into vauto_results for display
#             # We use the current_lookup (latest status of this week)
#             for item in vauto_results:
#                 stock = item.get("stock_id")
#                 if stock in current_lookup:
#                     item["current_stage"] = current_lookup[stock]
#                 else:
#                     item["current_stage"] = None 

#         return {
#             # "data": vauto_results,
#             "metrics": {
#                 "total_leads_per_week": total_leads_current,
#                 "avg_leads_per_day": avg_leads_current,
#                 "total_leads_pct_compared_to_last_week": total_leads_pct,
#                 "avg_leads_pct_compared_to_last_week": avg_leads_pct
#             }
#         }






#     async def get_filtered_data_backup(self, filters: dict):
#         # 1. Map frontend filter keys to Database Column names
#         today = datetime.now()
#         start_of_week = today - timedelta(days=today.weekday())  # Monday
#         date_conditions = []
        
#         # Generate date conditions for the whole week (Mon-Sun)
#         for i in range(7):
#             day_date = start_of_week + timedelta(days=i)
#             # Athena partitions are usually strings, ensure format matches (e.g., '2024', '10', '13')
#             # Assuming single digit days/months might need leading zero depending on Athena data. 
#             # Based on previous code `day='13'`, it seems just string.
#             # Let's assume standard zero-padded might be safer, but '13' implies 2 digits.
#             # If existing data uses '1', '2', etc., straight str(int) is safer?
#             # The previous code used `str(datetime.now().day)` which gives '1', '10'.
#             # Let's use str(day_date.day), str(day_date.month), etc.
#             y = str(day_date.year)
#             m = str(day_date.month)
#             d = str(day_date.day)
#             date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

#         date_query_part = " OR ".join(date_conditions)
#         logger.info(f"Date query part: {date_query_part}")

#         # Key = DB Column, Value = Filter Value
#         query_filters = {
#             # "day": date_query_part,  <-- REMOVED, handled via extra_conditions
#             "body": filters.get("body_type"),
#             "store": filters.get("store"),
#             "vin": filters.get("vin")
#         }
        
#         # 2. Call the generic function to get vAuto data
#         vauto_results = await self.fetch_dynamic_data2(
#             table=self.athena_vauto_table,
#             columns=["*"],
#             filters=query_filters,
#             extra_conditions=[f"({date_query_part})"]
#         )
        
#         # 3. Extract stock IDs
#         stock_ids = [item.get("stock_id") for item in vauto_results if item.get("stock_id")]
#         logger.info(f"Extracted stock IDs: {len(stock_ids)}")
#         # 4. If we have stock IDs, fetch DriveCentric data
#         if stock_ids:
#             logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks")
#             # Format stock IDs for SQL IN clause: 'stock1', 'stock2', ...
#             # sanitize just in case
#             sanitized_stocks = [self._sanitize(s) for s in stock_ids]
#             stock_list_str = "', '".join(sanitized_stocks)
            
#             # Calculate start (Monday) and end (Sunday) of the current week
#             # today = datetime.now()
#             # start_of_week = today - timedelta(days=today.weekday())  # Monday
#             # date_conditions = []
            
#             # # Generate date conditions for the whole week (Mon-Sun)
#             # for i in range(7):
#             #     day_date = start_of_week + timedelta(days=i)
#             #     # Athena partitions are usually strings, ensure format matches (e.g., '2024', '10', '13')
#             #     # Assuming single digit days/months might need leading zero depending on Athena data. 
#             #     # Based on previous code `day='13'`, it seems just string.
#             #     # Let's assume standard zero-padded might be safer, but '13' implies 2 digits.
#             #     # If existing data uses '1', '2', etc., straight str(int) is safer?
#             #     # The previous code used `str(datetime.now().day)` which gives '1', '10'.
#             #     # Let's use str(day_date.day), str(day_date.month), etc.
#             #     y = str(day_date.year)
#             #     m = str(day_date.month)
#             #     d = str(day_date.day)
#             #     date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

#             # date_query_part = " OR ".join(date_conditions)

#             drivecentric_query = f"""
#                 SELECT vehicle_1_stock_number, current_stage, year, month, day
#                 FROM {self.athena_drivecentric_table} 
#                 WHERE vehicle_1_stock_number IN ('{stock_list_str}') 
#                 AND platform_name = 'drive_centric' 
#                 AND ({date_query_part})
#             """
#             logger.info(f"DriveCentric query: {drivecentric_query}")
#             logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks (Weekly)")
#             drivecentric_results = await self._execute_query(drivecentric_query)
#             logger.info(f"DriveCentric results count: {len(drivecentric_results)}")

#             # Helper to parse date from row
#             def get_date(row):
#                 try:
#                     return datetime(int(row.get('year', 0)), int(row.get('month', 1)), int(row.get('day', 1)))
#                 except:
#                     return datetime.min
            
#             # 1. Calculate Daily Lead Counts for Avg Metric
#             # Count how many leads existed on each day
#             daily_leads_sum = 0
#             for item in drivecentric_results:
#                 stage = str(item.get("current_stage", "")).lower()
#                 if stage == "lead":
#                     daily_leads_sum += 1
#             logger.info(f"Daily Leads Sum: {daily_leads_sum}")

#             # Avg Leads / Day = Total Leads Sum / 7
#             avg_leads = round(daily_leads_sum / 7, 1)
#             logger.info(f"Average Leads per Day: {avg_leads}")

#             # 2. Process for Snapshot (Latest Status)
#             # Sort by date ASC so latest date is last
#             sorted_results = sorted(drivecentric_results, key=get_date)

#             # Create a lookup dictionary: stock -> current_stage (Latest wins)
#             dc_lookup = {item.get("vehicle_1_stock_number"): item.get("current_stage") for item in sorted_results if item.get("vehicle_1_stock_number")}
            
#             # Total Leads (Snapshot) based on unique latest status
#             total_leads = sum(1 for stage in dc_lookup.values() if str(stage).lower() == "lead")
            
#             # 5. Merge current_stage into vauto_results
#             for item in vauto_results:
#                 stock = item.get("stock_id")
#                 logger.info(f"Merging current_stage for stock: {stock}")
#                 if stock in dc_lookup:
#                     item["current_stage"] = dc_lookup[stock]
#                     logger.info(f"Merged current_stage for stock: {stock}")
#                 else:
#                     item["current_stage"] = None # Or "Unknown"
#                     logger.info(f"Merged current_stage for stock: {stock}")
#         else:
#              total_leads = 0
#              avg_leads = 0
             
#         return {
#             "data": vauto_results,
#             "metrics": {
#                 "total_leads": total_leads,
#                 "avg_leads": avg_leads
#             }
#         }



import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DashboardRepository:
    # Assuming _execute_query, _sanitize, etc. are defined elsewhere in the class
    def __init__(self, db: AsyncSession):
        self.db = db
        self.athena_db = os.getenv("ATHENA_DB", "leadboost_db")
        self.s3_bucket = os.getenv("S3_BUCKET", "taverna-auto-job")
        self.s3_project_name = os.getenv("S3_PROJECT_NAME", "leadBoostAI")
        self.athena_output = f"s3://{self.s3_bucket}/{self.s3_project_name}/output/"
        
        # Table configurations
        self.athena_vauto_table = os.getenv("ATHENA_VAUTO_TABLE", "vauto_inventry")
        self.athena_carguru_table = os.getenv("ATHENA_CARGURU_TABLE", "carguru_inventry")
        self.athena_drivecentric_table = os.getenv("ATHENA_DRIVECENTRIC_TABLE", "drivecentric_inventry")

    def _sanitize(self, value):
        if isinstance(value, str):
            return value.replace("'", "''")
        return value

    async def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        # logger.info(f"Running Athena query: {query}")
        try:
            execution_id = run_athena_query(query, self.athena_db, self.athena_output)
            state = wait_for_query(execution_id)
            if state == "SUCCEEDED":
                return get_query_results(execution_id)
            logger.error(f"Athena query failed with state: {state}")
            return []
        except Exception as e:
            logger.error(f"Athena Execution Error: {str(e)} | Query: {query}")
            return []

    async def fetch_dynamic_data(
        self,
        table: str,
        columns: List[str],
        filters: Optional[Dict[str, Any]] = None,
        distinct: bool = False,
        custom_where: Optional[str] = None,
        platform_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        col_str = ", ".join(columns)
        select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
        query_parts = [f"{select_prefix} {col_str} FROM {table}"]

        conditions = []
        if platform_name:
            conditions.append(f"platform_name = '{self._sanitize(platform_name)}'")

        if filters:
            for col, val in filters.items():
                if val is not None and val != "":
                    clean_val = self._sanitize(val)
                    conditions.append(f"{col} = '{clean_val}'")

        if custom_where:
            conditions.append(custom_where)

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        final_query = " ".join(query_parts)
        # logger.debug(f"Generated SQL: {final_query}")
        return await self._execute_query(final_query)


    async def get_body_types(self) -> List[str]:
        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["body"],
            distinct=True
        )
        # Filter None/Empty and sort
        return sorted([item["body"] for item in results if item.get("body")])

    async def get_stores(self) -> List[str]:
        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["store"],
            distinct=True
        )
        return sorted([item["store"] for item in results if item.get("store")])

    async def get_vins(self) -> List[str]:
        today = datetime.now()
        start_of_current_week = (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        date_clause = self._generate_partition_clause(start_of_current_week, 7)

        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["vin"],
            distinct=True,
            custom_where=date_clause
        )
        logger.info(f"Fetched {len(results)} unique VINs")
        return sorted([item["vin"] for item in results if item.get("vin")])


    def _get_date_tuples_str(self, start_date: datetime, days: int) -> str:
        date_tuples = []
        for i in range(days):
            current = start_date + timedelta(days=i)
            y, m, d = current.strftime("%Y"), current.strftime("%m"), current.strftime("%d")
            date_tuples.append(f"('{y}', '{m}', '{d}')")
        return ", ".join(date_tuples)

    def _generate_partition_clause(self, start_date: datetime, days: int) -> str:
        tuples_str = self._get_date_tuples_str(start_date, days)
        return f"(year, month, day) IN ({tuples_str})"

    async def get_filtered_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # ✅ FIXED week math (current week Monday 00:00)
        today = datetime.now()
        start_of_current_week = (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_of_last_week = start_of_current_week - timedelta(days=7)

        vauto_date_clause = self._generate_partition_clause(start_of_last_week, 14)
        
        # For Metrics: Fetch 2 weeks of history (Current Week + Last Week)
        drive_date_clause = self._generate_partition_clause(start_of_last_week, 14)

        query_filters = {
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin"),
        }

        # ✅ STABLE vAuto: latest row per stock_id (instead of DISTINCT *)
        # vauto_query = f"""
        # WITH x AS (
        #   SELECT
        #     *,
        #     row_number() OVER (
        #       PARTITION BY stock_id
        #       ORDER BY year DESC, month DESC, day DESC
        #     ) AS rn
        #   FROM {self.athena_vauto_table}
        #   WHERE platform_name = 'vauto'
        #     AND {vauto_date_clause}
        #     {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
        #     {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
        #     {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
        # )
        # SELECT * FROM x WHERE rn = 1
        # """

        vauto_unique_stock_ids_query = f"""
            SELECT DISTINCT stock_id
            FROM {self.athena_vauto_table}
            WHERE platform_name = 'vauto'
            AND {vauto_date_clause}
            {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
            {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
            {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
            AND stock_id IS NOT NULL
        """

        vauto_results = await self._execute_query(vauto_unique_stock_ids_query)
        logger.info(f"vauto_results_unique_stock_ids: {len(vauto_results)}")

        # vauto_results = await self._execute_query(vauto_query)
        # logger.info(f"CTE vauto_results: {len(vauto_results)}")

        if not vauto_results:
            return self._build_empty_response()
            
        stock_ids = list({item.get("stock_id") for item in vauto_results if item.get("stock_id")})
        logger.info(f"Extracted {len(stock_ids)} unique stock IDs")

        if not stock_ids:
            return self._build_empty_response()

        sanitized_stocks = "', '".join([self._sanitize(s) for s in stock_ids])

        drivecentric_query = (
            f"SELECT vehicle_1_stock_number, deal_sales_1, current_stage, year, month, day "
            f"FROM {self.athena_drivecentric_table} "
            f"WHERE platform_name = 'drive_centric' "
            f"AND vehicle_1_stock_number IN ('{sanitized_stocks}') "
            f"AND {drive_date_clause}"
        )

        drive_results = await self._execute_query(drivecentric_query)
        logger.info(f"Fetched {len(drive_results)} DriveCentric rows")

        def parse_row_date(row):
            try:
                return datetime(int(row["year"]), int(row["month"]), int(row["day"]))
            except Exception:
                return datetime.min

        processed_rows = []
        for row in drive_results:
            d = parse_row_date(row)
            processed_rows.append(
                {
                    "stock": row.get("vehicle_1_stock_number"),
                    "stage": str(row.get("current_stage", "")).lower(),
                    "user": row.get("deal_sales_1"),
                    "date": d,
                    "is_current_week": d >= start_of_current_week,
                    "is_last_week": start_of_last_week <= d < start_of_current_week
                }
            )

        def calculate_metrics(rows: List[Dict], denom_days: int) -> Tuple[int, float]:
            if not rows or denom_days <= 0:
                return 0, 0.0
            rows.sort(key=lambda x: x["date"])
            total = sum(1 for r in rows if r["stage"] == "lead")
            avg = round(total / float(denom_days), 1)
            return total, avg

        # def calculate_metrics(rows: List[Dict], denom_days: int) -> Tuple[int, float]:
        #     if not rows or denom_days <= 0:
        #         return 0, 0.0

        #     total = sum(1 for r in rows if r["stage"] == "lead")
        #     avg = round(total / float(denom_days), 1)
        #     return total, avg


        current_week_data = [r for r in processed_rows if r["is_current_week"]]
        last_week_data = [r for r in processed_rows if r["is_last_week"]]
        logger.info(f"Current week data: {len(current_week_data)}")
        logger.info(f"Last week data: {len(last_week_data)}")
        days_so_far = min(today.weekday() + 1, 7) 
        logger.info(f"Days so far: {days_so_far}")
        cur_total, cur_avg= calculate_metrics(current_week_data, days_so_far)
        last_total, last_avg= calculate_metrics(last_week_data,7)
        # cur_total, cur_avg= calculate_metrics(current_week_data, 7)
        # last_total, last_avg= calculate_metrics(last_week_data, 7)

        def calc_pct(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return round(((curr - prev) / prev) * 100, 1)
        
        logger.info(f"Total Leads current Week: {cur_total}")
        logger.info(f"Avg Leads current Day: {cur_avg}")
        logger.info(f"Total Leads last Week: {last_total}")
        logger.info(f"Avg Leads last Day: {last_avg}")
        logger.info(f"percentage change in total leads: {calc_pct(cur_total, last_total)}")
        logger.info(f"percentage change in avg leads: {calc_pct(cur_avg, last_avg)}")

        # --- Graph Data Removed from here ---

        # --- NEW: Total Unsold Cars Metrics (vAuto) ---
        cur_tuples = self._get_date_tuples_str(start_of_current_week, 7)
        last_tuples = self._get_date_tuples_str(start_of_last_week, 7)

        count_query = f"""
        SELECT 
            COUNT(DISTINCT CASE WHEN (year, month, day) IN ({cur_tuples}) THEN stock_id END) as cur_cnt,
            COUNT(DISTINCT CASE WHEN (year, month, day) IN ({last_tuples}) THEN stock_id END) as last_cnt
        FROM {self.athena_vauto_table}
        WHERE platform_name = 'vauto'
          AND (year, month, day) IN ({cur_tuples}, {last_tuples})
          {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
          {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
          {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
        """
        
        unsold_results = await self._execute_query(count_query)
        unsold_cur = 0
        unsold_last = 0
        if unsold_results:
             row = unsold_results[0]
             unsold_cur = int(row.get('cur_cnt', 0))
             unsold_last = int(row.get('last_cnt', 0))

        total_unsold_pct = calc_pct(unsold_cur, unsold_last)
        logger.info(f"Unsold Cars: Current={unsold_cur}, Last={unsold_last}, Pct={total_unsold_pct}%")

        return {
            # "data": vauto_results,
            "metrics": {
                "total_leads_per_week": cur_total,
                "avg_leads_per_day": cur_avg,
                "total_leads_pct_compared_to_last_week": calc_pct(cur_total, last_total),
                "avg_leads_pct_compared_to_last_week": calc_pct(cur_avg, last_avg),
                "total_unsold_cars": unsold_cur,
                "total_unsold_cars_pct_compared_to_last_week": total_unsold_pct
            },
        }

    async def get_lead_performance_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # Same logic for dates and stock ID retrieval
        today = datetime.now()
        days_so_far_current_week = min(today.weekday() + 1, 7)  # Mon=1 ... Sun=7
        logger.info(f"days_so_far_current_week: {days_so_far_current_week}")
        start_of_current_week = (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_of_last_week = start_of_current_week - timedelta(days=7)
        vauto_date_clause = self._generate_partition_clause(start_of_last_week, 14)
        
        # For Graph: Fetch 8 weeks of history
        start_of_graph_period = start_of_current_week - timedelta(weeks=7)
        drive_date_clause = self._generate_partition_clause(start_of_graph_period, 56)

        query_filters = {
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin"),
        }

        # vauto_query = f"""
        # WITH x AS (
        #   SELECT
        #     *,
        #     row_number() OVER (
        #       PARTITION BY stock_id
        #       ORDER BY year DESC, month DESC, day DESC
        #     ) AS rn
        #   FROM {self.athena_vauto_table}
        #   WHERE platform_name = 'vauto'
        #     AND {vauto_date_clause}
        #     {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
        #     {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
        #     {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
        # )
        # SELECT * FROM x WHERE rn = 1
        # """

        vauto_unique_stock_ids_query = f"""
            SELECT DISTINCT stock_id
            FROM {self.athena_vauto_table}
            WHERE platform_name = 'vauto'
            AND {vauto_date_clause}
            {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
            {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
            {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
            AND stock_id IS NOT NULL
        """

        vauto_results = await self._execute_query(vauto_unique_stock_ids_query)
        logger.info(f"vauto_results_unique_stock_ids: {len(vauto_results)}")

        if not vauto_results:
            return {"graph_data": []}
            
        stock_ids = list({item.get("stock_id") for item in vauto_results if item.get("stock_id")})

        if not stock_ids:
            return {"graph_data": []}

        sanitized_stocks = "', '".join([self._sanitize(s) for s in stock_ids])

        drivecentric_query = (
            f"SELECT vehicle_1_stock_number, current_stage, year, month, day "
            f"FROM {self.athena_drivecentric_table} "
            f"WHERE platform_name = 'drive_centric' "
            f"AND vehicle_1_stock_number IN ('{sanitized_stocks}') "
            f"AND {drive_date_clause}"
        )

        drive_results = await self._execute_query(drivecentric_query)
        logger.info(f"drive_results: {len(drive_results)}")

        def parse_row_date(row):
            try:
                return datetime(int(row["year"]), int(row["month"]), int(row["day"]))
            except Exception:
                return datetime.min

        processed_rows = []
        for row in drive_results:
            d = parse_row_date(row)
            processed_rows.append(
                {
                    "stock": row.get("vehicle_1_stock_number"),
                    "stage": str(row.get("current_stage", "")).lower(),
                    "date": d,
                }
            )

        def calculate_metrics(rows: List[Dict], days_so_far: int) -> Tuple[int, float]:
            if not rows:
                return 0, 0.0
            rows.sort(key=lambda x: x["date"])
            total = sum(1 for r in rows if r["stage"] == "lead")
            avg = round(total / days_so_far, 1)
            return total, avg

        # --- Graph Data Aggregation ---
        weekly_buckets = {}
        for i in range(8):
            week_start = start_of_current_week - timedelta(weeks=i)
            weekly_buckets[week_start] = []

        for row in processed_rows:
            r_date = row["date"]
            r_week_start = (r_date - timedelta(days=r_date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            if r_week_start in weekly_buckets:
                weekly_buckets[r_week_start].append(row)
        
        graph_data = []
        sorted_weeks = sorted(weekly_buckets.keys())
        
        for w_start in sorted_weeks:
            w_rows = weekly_buckets[w_start]
            # days_so_far = min(today.weekday() + 1, 7) 
            denom_days = days_so_far_current_week if w_start == start_of_current_week else 7
            logger.info(f"denom_days: {denom_days}")
            _, w_avg = calculate_metrics(w_rows, denom_days)
            
            month_name = w_start.strftime("%B")
            week_num = 1 + (w_start.day - 1) // 7
            label = f"{month_name} Week {week_num}"
            logger.info(f"Label: {label}, Value: {w_avg}")
            
            graph_data.append({
                "label": label,
                "value": w_avg,
                "date": w_start.strftime("%Y-%m-%d")
            })

        return {"graph_data": graph_data}


    def _build_empty_response(self):
        return {
            "data": [],
            "metrics": {
                "total_leads_per_week": 0,
                "avg_leads_per_day": 0,
                "total_leads_pct_compared_to_last_week": 0,
                "avg_leads_pct_compared_to_last_week": 0,
                "total_unsold_cars": 0,
                "total_unsold_cars_pct_compared_to_last_week": 0
            }
        }










