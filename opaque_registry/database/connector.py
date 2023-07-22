import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from opaque_registry.database.utils import inject_psycopg_dialect


DB_URL = inject_psycopg_dialect(os.environ.get("OPAQUE_REGISTRY_DB_URL"))

ENGINE = create_async_engine(DB_URL, future=True)


async def get_db_session() -> AsyncSession:
    async_session = async_sessionmaker(
        ENGINE, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await session.close()
