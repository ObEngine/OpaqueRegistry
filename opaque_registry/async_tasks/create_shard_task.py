from sqlalchemy import select

from opaque_registry.celery_app import celery_app
from opaque_registry.database.connector import create_sync_sessionmaker
from opaque_registry.database.models.functions import string_to_shard_id


@celery_app.task
def create_shard_task(shard_id: int):
    async_sessionmaker = create_sync_sessionmaker()
    with async_sessionmaker() as session:
        select(string_to_shard_id(db_models.Package.id, 16))
