import asyncio
import os
from dotenv import load_dotenv
from services.scrape_service import ScrapeService

load_dotenv()

async def run_vauto():
    username = os.getenv("VAUTO_USERNAME")
    password = os.getenv("VAUTO_PASSWORD")
    report_name = os.getenv(
        "VAUTO_REPORT_NAME",
        "Taverna Inventory IRECON PHOTOS3"
    )

    if not username or not password:
        raise Exception("VAUTO_USERNAME or VAUTO_PASSWORD missing")

    service = ScrapeService()

    result = await service.start_login_flow(
        username=username,
        password=password,
        report_name=report_name
    )

    print("VAuto result:", result)

if __name__ == "__main__":
    asyncio.run(run_vauto())
