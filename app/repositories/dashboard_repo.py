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
from datetime import datetime

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
            conditions = []
            for col, val in filters.items():
                if val is not None and val != "":
                    # Sanitize and quote the value
                    clean_val = self._sanitize(val)
                    conditions.append(f"{col} = '{clean_val}'")
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        # 3. Execute
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
        # Key = DB Column, Value = Filter Value
        query_filters = {
            "day": "17",  # Hardcoded default from your original code
            # "day": str(datetime.now().day),
            "body": filters.get("body_type"),
            "store": filters.get("store"),
            "vin": filters.get("vin")
        }
        def alter_table():
            query = f"""
            ALTER TABLE {self.athena_vauto_table}
            ADD COLUMNS (
                carfax_has_report string,
                carfax_has_manufacturer_recall string,
                carfax_has_warnings string,
                carfax_has_problems string
            )
            """
            try:
                execution_id = run_athena_query(query, self.athena_db, self.athena_output)
                wait_for_query(execution_id)
                logger.info("UAM data seeded successfully")
            except Exception as e:
                logger.error(f"Error seeding UAM data: {str(e)}")


        alter_table()
        print("---------------------", query_filters)
        logger.info("Fetching filtered data with payload: {}".format(query_filters))
        # 2. Call the generic function
        results = await self.fetch_dynamic_data(
            table=self.athena_vauto_table,
            columns=["*"],
            filters=query_filters
        )
        return results
