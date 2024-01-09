import hashlib

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import opaque_registry.database.models as db_models


def derive_shard_id_from_package_id(package_id: str, shard_count: int) -> int:
    # use sha256 to get a 256 bit hash of the package_id
    # then convert that to an integer
    # then modulo that integer by the number of shards

    package_id_bytes = package_id.encode("utf-8")
    package_id_hash = hashlib.sha256(package_id_bytes).digest()
    package_id_int = int.from_bytes(package_id_hash, "big")
    shard_id = package_id_int % shard_count
    return shard_id


async def get_shard_count(db_session: AsyncSession) -> int:
    return await db_session.scalar(select(func.count()).select_from(db_models.Shard))
