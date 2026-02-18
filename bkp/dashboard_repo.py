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

    # def _sanitize(self, value):
    #     """Helper to escape single quotes to prevent SQL syntax errors."""
    #     if isinstance(value, str):
    #         return value.replace("'", "''")
    #     return value

    # async def _execute_query(self, query):
    #     """
    #     Centralized method to run, wait, and fetch Athena results.
    #     Handles all logging and error catching here.
    #     """
    #     logger.info(f"Running Athena query: {query}")
    #     try:
    #         execution_id = run_athena_query(query, self.athena_db, self.athena_output)
    #         state = wait_for_query(execution_id)

    #         if state == "SUCCEEDED":
    #             return get_query_results(execution_id)
    #         else:
    #             logger.error(f"Athena query failed with state: {state}")
    #             return []
    #     except Exception as e:
    #         logger.error(f"Athena Execution Error: {str(e)} | Query: {query}")
    #         return []
    
    
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
    
    # async def fetch_dynamic_data(
    #     self, 
    #     table: str, 
    #     columns: List[str], 
    #     filters: Optional[Dict[str, Any]] = None, 
    #     distinct: bool = False, 
    #     custom_where: Optional[str] = None
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Unified query builder and executor.
        
    #     Args:
    #         table: Table name.
    #         columns: List of columns to select.
    #         filters: Dictionary of equality filters (e.g. {'store': 'ABC'}).
    #         distinct: Boolean to apply SELECT DISTINCT.
    #         custom_where: Raw SQL string for complex conditions (e.g. date ranges).
    #     """
    #     # 1. Build SELECT
    #     col_str = ", ".join(columns)
    #     select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
    #     query_parts = [f"{select_prefix} {col_str} FROM {table}"]
        
    #     # 2. Build WHERE conditions
    #     conditions = ["platform_name = 'vauto'"] # Default constraint
        
    #     if filters:
    #         for col, val in filters.items():
    #             if val is not None and val != "":
    #                 # PRODUCTION NOTE: Ideally, use bind parameters (e.g., %s or ?) 
    #                 # in _execute_query instead of f-string formatting to prevent SQL injection.
    #                 clean_val = self._sanitize(val)
    #                 conditions.append(f"{col} = '{clean_val}'")
        
    #     if custom_where:
    #         conditions.append(custom_where)
            
    #     if conditions:
    #         query_parts.append("WHERE " + " AND ".join(conditions))
            
    #     final_query = " ".join(query_parts)
        
    #     # Debug log for dev, reduce to DEBUG level in prod
    #     logger.debug(f"Generated SQL: {final_query}")
        
    #     return await self._execute_query(final_query)

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
        logger.debug(f"Generated SQL: {final_query}")
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

    # def _generate_partition_clause(self, start_date: datetime, days: int) -> str:
    #     """
    #     Generates an optimized SQL WHERE clause for Athena partitioned dates.
    #     Uses the IN syntax for better readability and performance.
    #     """
    #     date_tuples = []
    #     for i in range(days):
    #         current = start_date + timedelta(days=i)
    #         # Ensure zero-padding matches DB schema (e.g. '02' vs '2')
    #         y, m, d = current.strftime("%Y"), current.strftime("%m"), current.strftime("%d")
    #         date_tuples.append(f"('{y}', '{m}', '{d}')")
            
    #     # Generates: (year, month, day) IN (('2025','02','01'), ('2025','02','02')...)
    #     # This is standard SQL standard and works on Presto/Trino/Athena
    #     return f"(year, month, day) IN ({', '.join(date_tuples)})"

    # async def get_filtered_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
    #     # --- 1. Date Calculation ---
    #     today = datetime.now()
    #     # Start of current week (Monday)
    #     start_of_current_week = (today - timedelta(days=today.weekday()+7)).replace(hour=0, minute=0, second=0, microsecond=0)
    #     start_of_last_week = start_of_current_week - timedelta(days=7)
        
    #     # Generate date clause for 14 days (Last week + Current week)
    #     date_clause = self._generate_partition_clause(start_of_last_week, 14)

    #     # --- 2. Fetch vAuto Data ---
    #     query_filters = {
    #         "body": filters.get("body_type"),
    #         "store": filters.get("store"),
    #         "vin": filters.get("vin")
    #     }
        
    #     vauto_results = await self.fetch_dynamic_data(
    #         table=self.athena_vauto_table,
    #         columns=["*"],
    #         filters=query_filters,
    #         custom_where=date_clause,
    #         distinct=True 
    #     )
        
    #     if not vauto_results:
    #         return self._build_empty_response()

    #     # Extract unique stock IDs to prevent redundant checks
    #     stock_ids = list({item.get("stock_id") for item in vauto_results if item.get("stock_id")})
    #     logger.info(f"Extracted {len(stock_ids)} unique stock IDs")

    #     # --- 3. Fetch DriveCentric Data ---
    #     # Optimization: Only fetch if we have stocks. 
    #     # Batch large lists to prevent query length limits if necessary (omitted for brevity).
        
    #     sanitized_stocks = "', '".join([self._sanitize(s) for s in stock_ids])
        
    #     drivecentric_query = (
    #         f"SELECT vehicle_1_stock_number, current_stage, year, month, day "
    #         f"FROM {self.athena_drivecentric_table} "
    #         f"WHERE platform_name = 'drive_centric' "
    #         f"AND vehicle_1_stock_number IN ('{sanitized_stocks}') "
    #         f"AND {date_clause}"
    #     )
        
    #     drive_results = await self._execute_query(drivecentric_query)
    #     logger.info(f"Fetched {len(drive_results)} DriveCentric rows")

    #     # --- 4. Process Metrics in Memory (Optimized) ---
        
    #     # Helper to convert row to date object once
    #     def parse_row_date(row):
    #         try:
    #             return datetime(int(row['year']), int(row['month']), int(row['day']))
    #         except (ValueError, KeyError):
    #             return datetime.min

    #     # Pre-process drive_results into a cleaner structure with parsed dates
    #     processed_rows = []
    #     for row in drive_results:
    #         d = parse_row_date(row)
    #         processed_rows.append({
    #             'stock': row.get('vehicle_1_stock_number'),
    #             'stage': str(row.get('current_stage', '')).lower(),
    #             'date': d,
    #             'is_current_week': d >= start_of_current_week
    #         })
    #     logger.info(f"Processed {len(processed_rows)} DriveCentric rows")
        
    #     # Calculate metrics for a specific subset
    #     def calculate_metrics(rows: List[Dict]) -> Tuple[int, float, Dict[str, str]]:
    #         if not rows:
    #             return 0, 0.0, {}

    #         # Avg Leads: Sum of all 'lead' occurrences / 7 days
    #         lead_count = sum(1 for r in rows if r['stage'] == 'lead')
    #         avg = round(lead_count / 7.0, 1)
    #         logger.info(f"Avg Leads: {avg}")
    #         # Total Leads: Count 'lead' based on the LATEST status per stock
    #         logger.info(f"Total Leads: {lead_count}")
    #         # Sort by date ascending
    #         rows.sort(key=lambda x: x['date'])
            
    #         # Dict comprehension overwrites previous keys, leaving only the latest status
    #         latest_status_map = {r['stock']: r['stage'] for r in rows}
    #         total = sum(1 for status in latest_status_map.values() if status == 'lead')
            
    #         return total, avg, latest_status_map

    #     # Split data using boolean flag (faster than re-parsing dates)
    #     current_week_data = [r for r in processed_rows if r['is_current_week']]
    #     last_week_data = [r for r in processed_rows if not r['is_current_week']]
    #     logger.info(f"Current week data: {len(current_week_data)}")
    #     logger.info(f"Last week data: {len(last_week_data)}")
    #     cur_total, cur_avg, cur_lookup = calculate_metrics(current_week_data)
    #     last_total, last_avg, _ = calculate_metrics(last_week_data)
    #     logger.info(f"Current week total: {cur_total}")
    #     logger.info(f"Last week total: {last_total}")
    #     logger.info(f"Current week avg: {cur_avg}")
    #     logger.info(f"Last week avg: {last_avg}")

    #     # --- 5. Merge Status back to vAuto (Optional) ---
    #     for item in vauto_results:
    #         stock = item.get("stock_id")
    #         item["current_stage"] = cur_lookup.get(stock)

    #     # --- 6. Calculate Percentages ---
    #     def calc_pct(curr, prev):
    #         if prev == 0:
    #             return 100.0 if curr > 0 else 0.0
    #         return round(((curr - prev) / prev) * 100, 1)

    #     return {
    #         "data": vauto_results, # Uncommented as usually required
    #         "metrics": {
    #             "total_leads_per_week": cur_total,
    #             "avg_leads_per_day": cur_avg,
    #             "total_leads_pct_compared_to_last_week": calc_pct(cur_total, last_total),
    #             "avg_leads_pct_compared_to_last_week": calc_pct(cur_avg, last_avg)
    #         }
    #     }

    # def _build_empty_response(self):
    #     return {
    #         "data": [],
    #         "metrics": {
    #             "total_leads_per_week": 0,
    #             "avg_leads_per_day": 0,
    #             "total_leads_pct_compared_to_last_week": 0,
    #             "avg_leads_pct_compared_to_last_week": 0
    #         }
    #     }


    def _generate_partition_clause(self, start_date: datetime, days: int) -> str:
        date_tuples = []
        for i in range(days):
            current = start_date + timedelta(days=i)
            y, m, d = current.strftime("%Y"), current.strftime("%m"), current.strftime("%d")
            date_tuples.append(f"('{y}', '{m}', '{d}')")
        return f"(year, month, day) IN ({', '.join(date_tuples)})"

    async def get_filtered_data(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # ✅ FIXED week math (current week Monday 00:00)
        today = datetime.now()
        start_of_current_week = (today - timedelta(days=today.weekday()+7)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_of_last_week = start_of_current_week - timedelta(days=7)

        date_clause = self._generate_partition_clause(start_of_last_week, 14)

        query_filters = {
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin"),
        }

        # ✅ STABLE vAuto: latest row per stock_id (instead of DISTINCT *)
        vauto_query = f"""
        WITH x AS (
          SELECT
            *,
            row_number() OVER (
              PARTITION BY stock_id
              ORDER BY year DESC, month DESC, day DESC
            ) AS rn
          FROM {self.athena_vauto_table}
          WHERE platform_name = 'vauto'
            AND {date_clause}
            {"AND body = '" + self._sanitize(query_filters['body']) + "'" if query_filters.get("body") else ""}
            {"AND store = '" + self._sanitize(query_filters['store']) + "'" if query_filters.get("store") else ""}
            {"AND vin = '" + self._sanitize(query_filters['vin']) + "'" if query_filters.get("vin") else ""}
        )
        SELECT * FROM x WHERE rn = 1
        """

        vauto_results = await self._execute_query(vauto_query)
        if not vauto_results:
            return self._build_empty_response()

        stock_ids = list({item.get("stock_id") for item in vauto_results if item.get("stock_id")})
        logger.info(f"Extracted {len(stock_ids)} unique stock IDs")

        if not stock_ids:
            return self._build_empty_response()

        sanitized_stocks = "', '".join([self._sanitize(s) for s in stock_ids])

        drivecentric_query = (
            f"SELECT vehicle_1_stock_number, current_stage, year, month, day "
            f"FROM {self.athena_drivecentric_table} "
            f"WHERE platform_name = 'drive_centric' "
            f"AND vehicle_1_stock_number IN ('{sanitized_stocks}') "
            f"AND {date_clause}"
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
                    "date": d,
                    "is_current_week": d >= start_of_current_week,
                }
            )

        def calculate_metrics(rows: List[Dict]) -> Tuple[int, float, Dict[str, str]]:
            if not rows:
                return 0, 0.0, {}

            rows.sort(key=lambda x: x["date"])
            latest_status_map = {r["stock"]: r["stage"] for r in rows}
            total = sum(1 for s in latest_status_map.values() if s == "lead")

            # avg per day in a 7-day week bucket
            avg = round(total / 7.0, 1)
            return total, avg, latest_status_map

        current_week_data = [r for r in processed_rows if r["is_current_week"]]
        last_week_data = [r for r in processed_rows if not r["is_current_week"]]

        cur_total, cur_avg, cur_lookup = calculate_metrics(current_week_data)
        last_total, last_avg, _ = calculate_metrics(last_week_data)

        for item in vauto_results:
            stock = item.get("stock_id")
            item["current_stage"] = cur_lookup.get(stock)

        def calc_pct(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return round(((curr - prev) / prev) * 100, 1)
        logger.info(f"Total Leads Per Week: {cur_total}")
        logger.info(f"Avg Leads Per Day: {cur_avg}")
        logger.info(f"Total Leads Pct Compared To Last Week: {calc_pct(cur_total, last_total)}")
        logger.info(f"Avg Leads Pct Compared To Last Week: {calc_pct(cur_avg, last_avg)}")
        return {
            "data": vauto_results,
            "metrics": {
                "total_leads_per_week": cur_total,
                "avg_leads_per_day": cur_avg,
                "total_leads_pct_compared_to_last_week": calc_pct(cur_total, last_total),
                "avg_leads_pct_compared_to_last_week": calc_pct(cur_avg, last_avg),
            },
        }

































# import re
# from dataclasses import dataclass
# from datetime import datetime, timedelta
# from typing import Any, Optional

# from core.logging import logger


# # =========================
# #   SAFE SQL BUILDING
# # =========================

# IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# def _validate_ident(name: str) -> str:
#     """Allow only simple SQL identifiers: letters/numbers/underscore, not starting with number."""
#     if not name or not IDENT_RE.match(name):
#         raise ValueError(f"Invalid identifier: {name!r}")
#     return name


# def _validate_table(table: str) -> str:
#     """
#     Supports: table OR db.table
#     """
#     parts = table.split(".")
#     if len(parts) == 1:
#         return _validate_ident(parts[0])
#     if len(parts) == 2:
#         return f"{_validate_ident(parts[0])}.{_validate_ident(parts[1])}"
#     raise ValueError(f"Invalid table format: {table!r}")


# def _escape_sql_literal(val: Any) -> str:
#     """
#     Escape for SQL string literal '...'
#     Athena/Presto escapes single quote by doubling it.
#     """
#     return str(val).replace("'", "''")


# def _chunk_list(items: list[str], chunk_size: int) -> list[list[str]]:
#     if chunk_size <= 0:
#         raise ValueError("chunk_size must be > 0")
#     return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


# def _build_last_14_days_partition_or(start_date: datetime) -> str:
#     """
#     Builds:
#       ( (year='2026' AND month='02' AND day='10') OR ... ) for 14 days
#     NOTE: Uses %m and %d (zero padded) - must match your Athena partitions.
#     """
#     conds = []
#     for i in range(14):
#         d = start_date + timedelta(days=i)
#         y = str(d.year)
#         m = d.strftime("%m")
#         day = d.strftime("%d")
#         conds.append(f"(year='{y}' AND month='{m}' AND day='{day}')")
#     return "(" + " OR ".join(conds) + ")"


# @dataclass(frozen=True)
# class SQL:
#     text: str


# class AthenaQueryBuilder:
#     """
#     Builds SELECT queries with:
#       - identifier validation for table/columns
#       - safe literal escaping for values
#       - optional default_conditions, so you don't repeat platform_name everywhere
#     """

#     def __init__(self, default_conditions: Optional[list[str]] = None):
#         self.default_conditions = default_conditions or []

#     def select(
#         self,
#         *,
#         table: str,
#         columns: list[str],
#         filters: Optional[dict[str, Any]] = None,
#         where: Optional[list[str]] = None,
#         distinct: bool = False,
#         limit: Optional[int] = None,
#     ) -> SQL:
#         table_sql = _validate_table(table)

#         if not columns:
#             raise ValueError("columns cannot be empty")

#         col_sql = ", ".join("*" if c == "*" else _validate_ident(c) for c in columns)
#         select_prefix = "SELECT DISTINCT" if distinct else "SELECT"

#         conditions: list[str] = []
#         conditions.extend(self.default_conditions)

#         if filters:
#             for k, v in filters.items():
#                 if v is None or v == "":
#                     continue
#                 col = _validate_ident(k)
#                 conditions.append(f"{col} = '{_escape_sql_literal(v)}'")

#         if where:
#             # Only pass internally-constructed strings here
#             conditions.extend(where)

#         q = f"{select_prefix} {col_sql} FROM {table_sql}"
#         if conditions:
#             q += " WHERE " + " AND ".join(conditions)

#         if limit is not None:
#             if int(limit) <= 0:
#                 raise ValueError("limit must be > 0")
#             q += f" LIMIT {int(limit)}"

#         return SQL(q)
































# # =========================
# #   YOUR REPO METHODS
# # =========================
# # NOTE:
# # - This code assumes you already have:
# #     self.athena_vauto_table
# #     self.athena_drivecentric_table
# #     self._execute_query(sql: str) -> awaitable[list[dict]]
# # - Keep your existing __init__ and _execute_query implementation.


# class DashboardRepository:
#     def __init__(self, db):
#         self.db = db

#         # These should already exist in your real __init__ from envs:
#         # self.athena_vauto_table = ...
#         # self.athena_drivecentric_table = ...

#         # Reusable builders with default platform filters
#         self.vauto_qb = AthenaQueryBuilder(default_conditions=["platform_name = 'vauto'"])
#         self.drivecentric_qb = AthenaQueryBuilder(default_conditions=["platform_name = 'drive_centric'"])
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

#     # -------------------------
#     # Replace BOTH old functions
#     # -------------------------
#     async def fetch_vauto(
#         self,
#         *,
#         columns: list[str],
#         filters: Optional[dict[str, Any]] = None,
#         where: Optional[list[str]] = None,
#         distinct: bool = False,
#         limit: Optional[int] = None,
#         log_sql: bool = False,
#     ):
#         sql = self.vauto_qb.select(
#             table=self.athena_vauto_table,
#             columns=columns,
#             filters=filters,
#             where=where,
#             distinct=distinct,
#             limit=limit,
#         ).text

#         if log_sql:
#             logger.info("Executing vAuto query: %s", sql)

#         return await self._execute_query(sql)

#     async def fetch_drivecentric(
#         self,
#         *,
#         columns: list[str],
#         filters: Optional[dict[str, Any]] = None,
#         where: Optional[list[str]] = None,
#         distinct: bool = False,
#         limit: Optional[int] = None,
#         log_sql: bool = False,
#     ):
#         sql = self.drivecentric_qb.select(
#             table=self.athena_drivecentric_table,
#             columns=columns,
#             filters=filters,
#             where=where,
#             distinct=distinct,
#             limit=limit,
#         ).text

#         if log_sql:
#             logger.info("Executing DriveCentric query: %s", sql)

#         return await self._execute_query(sql)

#     # -------------------------
#     # Existing placeholders
#     # -------------------------
#     async def get_data(self):
#         return {}

#     # -------------------------
#     # Optimized small endpoints
#     # -------------------------
#     async def get_body_types(self):
#         rows = await self.fetch_vauto(columns=["body"], distinct=True)
#         return sorted({r.get("body") for r in rows if r.get("body")})

#     async def get_stores(self):
#         rows = await self.fetch_vauto(columns=["store"], distinct=True)
#         return sorted({r.get("store") for r in rows if r.get("store")})

#     # -------------------------
#     # PRODUCTION OPTIMIZED METRICS
#     # -------------------------
#     async def get_filtered_data(self, filters: dict):
#         """
#         Computes your metrics using Athena SQL (fast) instead of Python grouping/sorting (slow).

#         Returns:
#           {
#             "metrics": {
#               "total_leads_per_week": ...,
#               "avg_leads_per_day": ...,
#               "total_leads_pct_compared_to_last_week": ...,
#               "avg_leads_pct_compared_to_last_week": ...
#             }
#           }
#         """

#         # ---- Date ranges (current week + last week = 14 days) ----
#         today = datetime.now()
#         start_of_current_week = (today - timedelta(days=today.weekday())).replace(
#             hour=0, minute=0, second=0, microsecond=0
#         )
#         start_of_last_week = start_of_current_week - timedelta(days=7)

#         date_pred_14 = _build_last_14_days_partition_or(start_of_last_week)

#         # ---- vAuto: fetch only stock_id (not SELECT *) ----
#         query_filters = {
#             "body": filters.get("body_type"),
#             "store": filters.get("store"),
#             "vin": filters.get("vin"),
#         }

#         vauto_rows = await self.fetch_vauto(
#             columns=["stock_id"],
#             filters=query_filters,
#             where=[date_pred_14],
#             distinct=True,
#             log_sql=True,
#         )

#         stock_ids = [r.get("stock_id") for r in vauto_rows if r.get("stock_id")]

#         if not stock_ids:
#             return {
#                 "metrics": {
#                     "total_leads_per_week": 0,
#                     "avg_leads_per_day": 0.0,
#                     "total_leads_pct_compared_to_last_week": 0.0,
#                     "avg_leads_pct_compared_to_last_week": 0.0,
#                 }
#             }

#         # ---- If huge list, batch to avoid query-length issues ----
#         # You can tune this. 500-1000 is usually safe.
#         batches = _chunk_list(stock_ids, chunk_size=800)

#         total_cur = 0
#         total_last = 0
#         avg_cur_sum = 0.0
#         avg_last_sum = 0.0

#         # We sum lead-event counts across batches, and also sum latest-lead counts across batches.
#         # avg per day is (total lead events / 7) across all batches, so summing avg parts works too.
#         for bi, batch in enumerate(batches, start=1):
#             in_list = ", ".join(f"'{_escape_sql_literal(s)}'" for s in batch)

#             metrics_sql = f"""
# WITH dc AS (
#   SELECT
#     vehicle_1_stock_number AS stock_id,
#     lower(coalesce(current_stage,'')) AS stage,
#     date_parse(concat(year,'-',month,'-',day), '%Y-%m-%d') AS dt
#   FROM {_validate_table(self.athena_drivecentric_table)}
#   WHERE platform_name = 'drive_centric'
#     AND vehicle_1_stock_number IN ({in_list})
#     AND {date_pred_14}
# ),
# cur AS (
#   SELECT * FROM dc
#   WHERE dt >= date_parse('{start_of_current_week.strftime("%Y-%m-%d")}', '%Y-%m-%d')
# ),
# prev AS (
#   SELECT * FROM dc
#   WHERE dt >= date_parse('{start_of_last_week.strftime("%Y-%m-%d")}', '%Y-%m-%d')
#     AND dt <  date_parse('{start_of_current_week.strftime("%Y-%m-%d")}', '%Y-%m-%d')
# ),
# cur_latest AS (
#   SELECT stock_id, stage
#   FROM (
#     SELECT stock_id, stage, dt,
#            row_number() OVER (PARTITION BY stock_id ORDER BY dt DESC) AS rn
#     FROM cur
#   ) x
#   WHERE rn = 1
# ),
# prev_latest AS (
#   SELECT stock_id, stage
#   FROM (
#     SELECT stock_id, stage, dt,
#            row_number() OVER (PARTITION BY stock_id ORDER BY dt DESC) AS rn
#     FROM prev
#   ) x
#   WHERE rn = 1
# )
# SELECT
#   (SELECT count(*) FROM cur_latest  WHERE stage = 'lead') AS total_leads_current,
#   (SELECT count(*) FROM prev_latest WHERE stage = 'lead') AS total_leads_last,
#   (SELECT count(*) FROM cur  WHERE stage = 'lead')        AS lead_events_current,
#   (SELECT count(*) FROM prev WHERE stage = 'lead')        AS lead_events_last
# """

#             logger.info("Executing DriveCentric metrics batch %s/%s", bi, len(batches))
#             rows = await self._execute_query(metrics_sql)
#             r = rows[0] if rows else {}

#             total_cur += int(r.get("total_leads_current") or 0)
#             total_last += int(r.get("total_leads_last") or 0)

#             lead_events_cur = int(r.get("lead_events_current") or 0)
#             lead_events_last = int(r.get("lead_events_last") or 0)

#             avg_cur_sum += (lead_events_cur / 7.0)
#             avg_last_sum += (lead_events_last / 7.0)

#         avg_cur = round(avg_cur_sum, 1)
#         avg_last = round(avg_last_sum, 1)

#         def pct(cur: float, last: float) -> float:
#             if last == 0:
#                 return 100.0 if cur > 0 else 0.0
#             return round(((cur - last) / last) * 100.0, 1)

#         return {
#             "metrics": {
#                 "total_leads_per_week": total_cur,
#                 "avg_leads_per_day": avg_cur,
#                 "total_leads_pct_compared_to_last_week": pct(total_cur, total_last),
#                 "avg_leads_pct_compared_to_last_week": pct(avg_cur, avg_last),
#             }
#         }

#     # -------------------------
#     # YOU MUST HAVE THIS METHOD
#     # -------------------------




