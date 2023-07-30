import asyncio

import uvicorn
from fastapi import Depends, FastAPI

from opaque_registry.api.routes import load_routers

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

load_routers(app=app)


if __name__ == "__main__":
    uvicorn.run(app)
