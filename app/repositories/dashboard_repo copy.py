# from utils.athena import run_athena_query, wait_for_query, get_query_results
# import os
# from core.logging import logger
# from sqlalchemy.ext.asyncio import AsyncSession
# from datetime import datetime

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


from utils.athena import run_athena_query, wait_for_query, get_query_results
import os
from core.logging import logger
# import datetime
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

class DashboardRepository:
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
        """Helper to escape single quotes to prevent SQL syntax errors."""
        if isinstance(value, str):
            return value.replace("'", "''")
        return value

    async def _execute_query(self, query):
        """
        Centralized method to run, wait, and fetch Athena results.
        Handles all logging and error catching here.
        """
        logger.info(f"Running Athena query: {query}")
        try:
            execution_id = run_athena_query(query, self.athena_db, self.athena_output)
            state = wait_for_query(execution_id)

            if state == "SUCCEEDED":
                return get_query_results(execution_id)
            else:
                logger.error(f"Athena query failed with state: {state}")
                return []
        except Exception as e:
            logger.error(f"Athena Execution Error: {str(e)} | Query: {query}")
            return []

    async def fetch_dynamic_data(self, table: str, columns: list, filters: dict = None, distinct: bool = False):
        """
        Dynamically builds and executes a query.
        
        Args:
            table (str): The table name.
            columns (list): List of column names to select (e.g. ['body', 'store']).
            filters (dict): Key-value pairs for WHERE clause (e.g. {'store': 'ABC'}).
            distinct (bool): Whether to use SELECT DISTINCT.
        """
        # 1. Build SELECT clause
        col_str = ", ".join(columns)
        select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
        query = f"{select_prefix} {col_str} FROM {table}"

        # 2. Build WHERE clause
        if filters:
            conditions = ["platform_name = 'vauto'"]
            for col, val in filters.items():
                if val is not None and val != "":
                    # Sanitize and quote the value
                    clean_val = self._sanitize(val)
                    conditions.append(f"{col} = '{clean_val}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        # 3. Execute
        return await self._execute_query(query)


    async def fetch_dynamic_data2(self, table: str, columns: list, filters: dict = None, distinct: bool = False, extra_conditions: list = None):
        """
        Dynamically builds and executes a query.
        
        Args:
            table (str): The table name.
            columns (list): List of column names to select (e.g. ['body', 'store']).
            filters (dict): Key-value pairs for WHERE clause (e.g. {'store': 'ABC'}).
            distinct (bool): Whether to use SELECT DISTINCT.
            extra_conditions (list): List of raw SQL condition strings to append.
        """
        # 1. Build SELECT clause
        col_str = ", ".join(columns)
        select_prefix = "SELECT DISTINCT" if distinct else "SELECT"
        query = f"{select_prefix} {col_str} FROM {table}"

        # 2. Build WHERE clause
        conditions = ["platform_name = 'vauto'"]
        
        if filters:
            for col, val in filters.items():
                if val is not None and val != "":
                    # Sanitize and quote the value
                    clean_val = self._sanitize(val)
                    conditions.append(f"{col} = '{clean_val}'")
        # extra_conditions = [f"(year = '2026' AND month = '02' AND day = '13')"]
        if extra_conditions:
            conditions.extend(extra_conditions)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        # 3. Execute
        logger.info(f"Executing query: {query}")
        return await self._execute_query(query)



    async def get_data(self):
        # Placeholder
        return {}

    async def get_body_types(self):
        # Reuses the generic function
        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["body"],
            filters={"platform_name": "vauto"}, # Optional: Keep if you need this filter
            distinct=True
        )
        # Flatten list: [{'body': 'SUV'}, {'body': 'Sedan'}] -> ['SUV', 'Sedan']
        bodies = [item.get("body") for item in results if item.get("body")]
        return sorted(bodies)

    async def get_stores(self):
        # Reuses the generic function
        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["store"],
            distinct=True
        )
        stores = [item.get("store") for item in results if item.get("store")]
        return sorted(stores)

    async def get_filtered_data(self, filters: dict):
        # 1. Map frontend filter keys to Database Column names
        today = datetime.now()
        # Testing: last week
        start_of_week = today - timedelta(days=today.weekday())  # Monday of last week
        date_conditions = []
        
        # Generate date conditions for the whole week (Mon-Sun)

        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            y = str(day_date.year)
            m = day_date.strftime('%m')
            d = day_date.strftime('%d')
            date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")


        date_query_part = " OR ".join(date_conditions)
        logger.info(f"Date query part: {date_query_part}")

        # Key = DB Column, Value = Filter Value
        query_filters = {
            # "day": date_query_part,  <-- REMOVED, handled via extra_conditions
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin")
        }
        
        # 2. Call the generic function to get vAuto data
        vauto_results = await self.fetch_dynamic_data2(
            table=self.athena_vauto_table,
            columns=["*"],
            filters=query_filters,
            extra_conditions=[f"({date_query_part})"]
        )
        
        # 3. Extract stock IDs
        stock_ids = [item.get("stock_id") for item in vauto_results if item.get("stock_id")]
        logger.info(f"Extracted stock IDs: {len(stock_ids)}")
        # 4. If we have stock IDs, fetch DriveCentric data
        if stock_ids:
            logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks")
            # Format stock IDs for SQL IN clause: 'stock1', 'stock2', ...
            # sanitize just in case
            sanitized_stocks = [self._sanitize(s) for s in stock_ids]
            stock_list_str = "', '".join(sanitized_stocks)
            
            # Calculate start (Monday) and end (Sunday) of the current week
            # today = datetime.now()
            # start_of_week = today - timedelta(days=today.weekday())  # Monday
            # date_conditions = []
            
            # # Generate date conditions for the whole week (Mon-Sun)
            # for i in range(7):
            #     day_date = start_of_week + timedelta(days=i)
            #     # Athena partitions are usually strings, ensure format matches (e.g., '2024', '10', '13')
            #     # Assuming single digit days/months might need leading zero depending on Athena data. 
            #     # Based on previous code `day='13'`, it seems just string.
            #     # Let's assume standard zero-padded might be safer, but '13' implies 2 digits.
            #     # If existing data uses '1', '2', etc., straight str(int) is safer?
            #     # The previous code used `str(datetime.now().day)` which gives '1', '10'.
            #     # Let's use str(day_date.day), str(day_date.month), etc.
            #     y = str(day_date.year)
            #     m = str(day_date.month)
            #     d = str(day_date.day)
            #     date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

            # date_query_part = " OR ".join(date_conditions)

            drivecentric_query = f"""
                SELECT vehicle_1_stock_number, current_stage, year, month, day
                FROM {self.athena_drivecentric_table} 
                WHERE vehicle_1_stock_number IN ('{stock_list_str}') 
                AND platform_name = 'drive_centric' 
                AND ({date_query_part})
            """
            logger.info(f"DriveCentric query: {drivecentric_query}")
            logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks (Weekly)")
            drivecentric_results = await self._execute_query(drivecentric_query)
            logger.info(f"DriveCentric results count: {len(drivecentric_results)}")

            # Helper to parse date from row
            def get_date(row):
                try:
                    return datetime(int(row.get('year', 0)), int(row.get('month', 1)), int(row.get('day', 1)))
                except:
                    return datetime.min
            
            # 1. Calculate Daily Lead Counts for Avg Metric
            # Count how many leads existed on each day
            daily_leads_sum = 0
            for item in drivecentric_results:
                stage = str(item.get("current_stage", "")).lower()
                if stage == "lead":
                    daily_leads_sum += 1
            logger.info(f"Daily Leads Sum: {daily_leads_sum}")

            # Avg Leads / Day = Total Leads Sum / 7
            avg_leads = round(daily_leads_sum / 7, 1)
            logger.info(f"Average Leads per Day: {avg_leads}")

            # 2. Process for Snapshot (Latest Status)
            # Sort by date ASC so latest date is last
            sorted_results = sorted(drivecentric_results, key=get_date)

            # Create a lookup dictionary: stock -> current_stage (Latest wins)
            dc_lookup = {item.get("vehicle_1_stock_number"): item.get("current_stage") for item in sorted_results if item.get("vehicle_1_stock_number")}
            
            # Total Leads (Snapshot) based on unique latest status
            total_leads = sum(1 for stage in dc_lookup.values() if str(stage).lower() == "lead")
            
            # 5. Merge current_stage into vauto_results
            for item in vauto_results:
                stock = item.get("stock_id")
                # logger.info(f"Merging current_stage for stock: {stock}")
                if stock in dc_lookup:
                    item["current_stage"] = dc_lookup[stock]
                    # logger.info(f"Merged current_stage for stock: {stock}")
                else:
                    item["current_stage"] = None # Or "Unknown"
                    # logger.info(f"Merged current_stage for stock: {stock}")
        else:
             total_leads = 0
             avg_leads = 0
             
        return {
            "data": vauto_results,
            "metrics": {
                "total_leads": total_leads,
                "avg_leads": avg_leads
            }
        }






    async def get_filtered_data_backup(self, filters: dict):
        # 1. Map frontend filter keys to Database Column names
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        date_conditions = []
        
        # Generate date conditions for the whole week (Mon-Sun)
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            # Athena partitions are usually strings, ensure format matches (e.g., '2024', '10', '13')
            # Assuming single digit days/months might need leading zero depending on Athena data. 
            # Based on previous code `day='13'`, it seems just string.
            # Let's assume standard zero-padded might be safer, but '13' implies 2 digits.
            # If existing data uses '1', '2', etc., straight str(int) is safer?
            # The previous code used `str(datetime.now().day)` which gives '1', '10'.
            # Let's use str(day_date.day), str(day_date.month), etc.
            y = str(day_date.year)
            m = str(day_date.month)
            d = str(day_date.day)
            date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

        date_query_part = " OR ".join(date_conditions)
        logger.info(f"Date query part: {date_query_part}")

        # Key = DB Column, Value = Filter Value
        query_filters = {
            # "day": date_query_part,  <-- REMOVED, handled via extra_conditions
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin")
        }
        
        # 2. Call the generic function to get vAuto data
        vauto_results = await self.fetch_dynamic_data2(
            table=self.athena_vauto_table,
            columns=["*"],
            filters=query_filters,
            extra_conditions=[f"({date_query_part})"]
        )
        
        # 3. Extract stock IDs
        stock_ids = [item.get("stock_id") for item in vauto_results if item.get("stock_id")]
        logger.info(f"Extracted stock IDs: {len(stock_ids)}")
        # 4. If we have stock IDs, fetch DriveCentric data
        if stock_ids:
            logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks")
            # Format stock IDs for SQL IN clause: 'stock1', 'stock2', ...
            # sanitize just in case
            sanitized_stocks = [self._sanitize(s) for s in stock_ids]
            stock_list_str = "', '".join(sanitized_stocks)
            
            # Calculate start (Monday) and end (Sunday) of the current week
            # today = datetime.now()
            # start_of_week = today - timedelta(days=today.weekday())  # Monday
            # date_conditions = []
            
            # # Generate date conditions for the whole week (Mon-Sun)
            # for i in range(7):
            #     day_date = start_of_week + timedelta(days=i)
            #     # Athena partitions are usually strings, ensure format matches (e.g., '2024', '10', '13')
            #     # Assuming single digit days/months might need leading zero depending on Athena data. 
            #     # Based on previous code `day='13'`, it seems just string.
            #     # Let's assume standard zero-padded might be safer, but '13' implies 2 digits.
            #     # If existing data uses '1', '2', etc., straight str(int) is safer?
            #     # The previous code used `str(datetime.now().day)` which gives '1', '10'.
            #     # Let's use str(day_date.day), str(day_date.month), etc.
            #     y = str(day_date.year)
            #     m = str(day_date.month)
            #     d = str(day_date.day)
            #     date_conditions.append(f"(year = '{y}' AND month = '{m}' AND day = '{d}')")

            # date_query_part = " OR ".join(date_conditions)

            drivecentric_query = f"""
                SELECT vehicle_1_stock_number, current_stage, year, month, day
                FROM {self.athena_drivecentric_table} 
                WHERE vehicle_1_stock_number IN ('{stock_list_str}') 
                AND platform_name = 'drive_centric' 
                AND ({date_query_part})
            """
            logger.info(f"DriveCentric query: {drivecentric_query}")
            logger.info(f"Fetching DriveCentric data for {len(stock_ids)} stocks (Weekly)")
            drivecentric_results = await self._execute_query(drivecentric_query)
            logger.info(f"DriveCentric results count: {len(drivecentric_results)}")

            # Helper to parse date from row
            def get_date(row):
                try:
                    return datetime(int(row.get('year', 0)), int(row.get('month', 1)), int(row.get('day', 1)))
                except:
                    return datetime.min
            
            # 1. Calculate Daily Lead Counts for Avg Metric
            # Count how many leads existed on each day
            daily_leads_sum = 0
            for item in drivecentric_results:
                stage = str(item.get("current_stage", "")).lower()
                if stage == "lead":
                    daily_leads_sum += 1
            logger.info(f"Daily Leads Sum: {daily_leads_sum}")

            # Avg Leads / Day = Total Leads Sum / 7
            avg_leads = round(daily_leads_sum / 7, 1)
            logger.info(f"Average Leads per Day: {avg_leads}")

            # 2. Process for Snapshot (Latest Status)
            # Sort by date ASC so latest date is last
            sorted_results = sorted(drivecentric_results, key=get_date)

            # Create a lookup dictionary: stock -> current_stage (Latest wins)
            dc_lookup = {item.get("vehicle_1_stock_number"): item.get("current_stage") for item in sorted_results if item.get("vehicle_1_stock_number")}
            
            # Total Leads (Snapshot) based on unique latest status
            total_leads = sum(1 for stage in dc_lookup.values() if str(stage).lower() == "lead")
            
            # 5. Merge current_stage into vauto_results
            for item in vauto_results:
                stock = item.get("stock_id")
                logger.info(f"Merging current_stage for stock: {stock}")
                if stock in dc_lookup:
                    item["current_stage"] = dc_lookup[stock]
                    logger.info(f"Merged current_stage for stock: {stock}")
                else:
                    item["current_stage"] = None # Or "Unknown"
                    logger.info(f"Merged current_stage for stock: {stock}")
        else:
             total_leads = 0
             avg_leads = 0
             
        return {
            "data": vauto_results,
            "metrics": {
                "total_leads": total_leads,
                "avg_leads": avg_leads
            }
        }
