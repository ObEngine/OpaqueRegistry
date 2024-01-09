import asyncio

import uvicorn
from fastapi import Depends, FastAPI

from opaque_registry.api.routes import load_routers
from opaque_registry.database.connector import init_async_db_engine

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

init_async_db_engine()

app = FastAPI()

load_routers(app=app)


if __name__ == "__main__":
    uvicorn.run(app)
