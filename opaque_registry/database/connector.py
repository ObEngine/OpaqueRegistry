import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm.session import Session, sessionmaker

from opaque_registry.database.utils import inject_psycopg_dialect

DB_URL = inject_psycopg_dialect(os.environ.get("OPAQUE_REGISTRY_DB_URL"))

ENGINE = create_async_engine(DB_URL, future=True)


def create_async_sessionmaker():
    return async_sessionmaker(ENGINE, class_=AsyncSession, expire_on_commit=False)


def create_sync_sessionmaker():
    return sessionmaker(ENGINE, class_=Session, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    async_sessionmaker = create_async_sessionmaker()
    async with async_sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            raise exc
        finally:
            await session.close()
