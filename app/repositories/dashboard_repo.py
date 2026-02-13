from utils.athena import run_athena_query, wait_for_query, get_query_results
import os
from core.logging import logger
from sqlalchemy.ext.asyncio import AsyncSession

class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.athena_db = os.getenv("ATHENA_DB", "leadboost_db")
        self.s3_bucket = os.getenv("S3_BUCKET", "taverna-auto-job")
        self.s3_project_name = os.getenv("S3_PROJECT_NAME", "leadBoostAI")
        self.athena_output = f"s3://{self.s3_bucket}/{self.s3_project_name}/output/"
        self.athena_vauto_table = os.getenv("ATHENA_VAUTO_TABLE", "vauto_inventry")
        self.athena_carguru_table = os.getenv("ATHENA_CARGURU_TABLE", "carguru_inventry")
        self.athena_drivecentric_table = os.getenv("ATHENA_DRIVECENTRIC_TABLE", "drivecentric_inventry")
        
    async def get_data(self):
        # Placeholder for data fetching logic
        return {}

    async def get_vauto_body_details(self):
        query = f"SELECT DISTINCT body FROM {self.athena_vauto_table} WHERE platform_name = 'vauto'"
        logger.info(f"Running Athena query: {query}")
        
        try:
            execution_id = run_athena_query(query, self.athena_db, self.athena_output)
            state = wait_for_query(execution_id)
            
            if state == "SUCCEEDED":
                results = get_query_results(execution_id)
                # Extract just the body names for a cleaner list, or return as is
                # Returning list of strings for "body"
                bodies = [item.get("body") for item in results if item.get("body")]
                return sorted(bodies)
            else:
                logger.error(f"Athena query failed with state: {state}")
                return []
        except Exception as e:
            logger.error(f"Error fetching vauto body details: {str(e)}")
            return []

    async def get_vauto_store_details(self):
        # query = f"SELECT DISTINCT store FROM {self.athena_vauto_table} WHERE platform_name = 'vauto'"
        query = f"SELECT DISTINCT store FROM {self.athena_vauto_table}"
        logger.info(f"Running Athena query: {query}")
        
        try:
            execution_id = run_athena_query(query, self.athena_db, self.athena_output)
            state = wait_for_query(execution_id)
            
            if state == "SUCCEEDED":
                results = get_query_results(execution_id)
                stores = [item.get("store") for item in results if item.get("store")]
                return sorted(stores)
            else:
                logger.error(f"Athena query failed with state: {state}")
                return []
        except Exception as e:
            logger.error(f"Error fetching vauto store details: {str(e)}")
            return []

    async def get_filtered_data(self, filters: dict):
        base_query = f"SELECT * FROM {self.athena_vauto_table} WHERE day = '13'"
        conditions = []
        
        # Mapping: Schema Field -> Athena Column
        # body_type -> body
        if filters.get("body_type") != "":
            conditions.append(f"body = '{filters['body_type']}'")
        
        # store -> store
        if filters.get("store") != "":
             conditions.append(f"store = '{filters['store']}'")
             
        # vin -> vin
        if filters.get("vin") != "":
            conditions.append(f"vin = '{filters['vin']}'")
            
        # demand_level -> Skipped for now
        # leads_per_day -> Skipped for now
        
        if conditions:
            base_query += " AND " + " AND ".join(conditions)
            
        logger.info(f"Running Athena query: {base_query}")
        
        try:
            execution_id = run_athena_query(base_query, self.athena_db, self.athena_output)
            state = wait_for_query(execution_id)
            
            if state == "SUCCEEDED":
                results = get_query_results(execution_id)
                return results
            else:
                logger.error(f"Athena query failed with state: {state}")
                return []
        except Exception as e:
            logger.error(f"Error fetching filtered data: {str(e)}")
            return []

