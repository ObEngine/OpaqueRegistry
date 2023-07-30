import asyncio

import opaque_registry.database.models as db_models
from opaque_registry.database.connector import ENGINE


async def init_models():
    async with ENGINE.begin() as conn:
        await conn.run_sync(db_models.Base.metadata.drop_all)
        await conn.run_sync(db_models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(init_models())
