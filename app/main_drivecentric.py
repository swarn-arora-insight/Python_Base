import asyncio
import os
from dotenv import load_dotenv
from services.scrape_service import ScrapeService

load_dotenv()

async def run_drivecentric():
    username = str(os.getenv("DRIVECENTRIC_USERNAME"))
    password = str(os.getenv("DRIVECENTRIC_PASSWORD"))

    if not username or not password:
        raise Exception("DRIVECENTRIC_USERNAME or DRIVECENTRIC_PASSWORD missing")

    service = ScrapeService()

    result = await service.start_drivecentric_login_flow(
        username=username,
        password=password,
    )

    print("Drivecentric result:", result)

if __name__ == "__main__":
    asyncio.run(run_drivecentric())
