import asyncio

from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn

from opaque_registry.routes import ROUTERS

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI()

for router in ROUTERS.values():
    app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app)
