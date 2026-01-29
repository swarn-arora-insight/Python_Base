import asyncio
import os
from dotenv import load_dotenv
from services.scrape_service import ScrapeService

load_dotenv()

async def run_cargurus():
    username = os.getenv("CARGURUS_USERNAME")
    password = os.getenv("CARGURUS_PASSWORD")

    if not username or not password:
        raise Exception("CARGURUS_USERNAME or CARGURUS_PASSWORD missing")

    service = ScrapeService()

    result = await service.start_cargurus_login_flow(
        username=username,
        password=password
    )

    print("CarGurus result:", result)

if __name__ == "__main__":
    asyncio.run(run_cargurus())
