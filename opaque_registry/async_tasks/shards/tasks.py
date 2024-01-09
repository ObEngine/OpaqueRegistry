import logging
import os
import time

import boto3
import msgpack
import redis
from sqlalchemy import and_, func, select, update

import opaque_registry.database.models as db_models
from opaque_registry.async_tasks.utils.redis_lock import RedisLock
from opaque_registry.celery_app import celery_app
from opaque_registry.database.connector import (
    create_sync_db_sessionmaker,
    init_sync_db_engine,
)

logger = logging.getLogger(__name__)

OBJECT_STORAGE_REGION = os.getenv("OBJECT_STORAGE_REGION", "fra1")
OBJECT_STORAGE_BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "obengine-packages")
OBJECT_STORAGE_KEY = os.getenv("OBJECT_STORAGE_KEY")
OBJECT_STORAGE_SECRET = os.getenv("OBJECT_STORAGE_SECRET")

SHARDS_PREFIX = "shards"

redis_client = redis.from_url(url=os.getenv("CELERY_BROKER_URL"))


def get_s3_config():
    return {
        "region_name": OBJECT_STORAGE_REGION,
        "endpoint_url": "https://{}.digitaloceanspaces.com".format(
            OBJECT_STORAGE_REGION
        ),
        "aws_access_key_id": OBJECT_STORAGE_KEY,
        "aws_secret_access_key": OBJECT_STORAGE_SECRET,
    }


def upload_to_s3(data: bytes, key: str):
    if OBJECT_STORAGE_KEY is None or OBJECT_STORAGE_SECRET is None:
        raise RuntimeError(
            "OBJECT_STORAGE_KEY or OBJECT_STORAGE_SECRET environment variables are not set"
        )
    s3config = get_s3_config()

    # Initializing S3.ServiceResource object - http://boto3.readthedocs.io/en/latest/reference/services/s3.html#service-resource
    s3resource = boto3.resource("s3", **s3config)
    s3client = boto3.client("s3", **s3config)

    for bucket in s3resource.buckets.all():
        print(bucket)

    s3object = s3resource.Bucket(OBJECT_STORAGE_BUCKET).put_object(Key=key, Body=data)
    s3resource.ObjectAcl(OBJECT_STORAGE_BUCKET, key).put(ACL="public-read")
    object_url = f"https://{OBJECT_STORAGE_BUCKET}.{OBJECT_STORAGE_REGION}.cdn.digitaloceanspaces.com/{key}"
    return object_url


@celery_app.task(bind=True)
def create_whole_index_task(self):
    logger.info(f"[IndexGen Task] Waiting for Task lock")
    with RedisLock(
        client=redis_client, lock_name=f"create_index_lock", expire=60 * 60
    ) as _lock:
        logger.info(f"[IndexGen Task] Task lock acquired")
        init_sync_db_engine()
        async_sessionmaker = create_sync_db_sessionmaker()
        all_packages = {}
        with async_sessionmaker() as session:
            # use db to retrieve time
            db_time = session.execute(select(func.now())).scalar_one_or_none()
            db_packages = session.execute(
                select(db_models.Package).filter_by(meta=False)
            )
            for package in db_packages.scalars().all():
                all_packages[package.id] = [
                    {
                        "version": package_version.version,
                        "url": package_version.url,
                    }
                    for package_version in package.versions
                ]
                for version in package.versions:
                    version.published = True
        logger.info(f"[IndexGen Task] Building binary index")
        msgpack_bytes = msgpack.packb(all_packages)
        logger.info(f"[IndexGen Task] Uploading index")
        upload_to_s3(data=msgpack_bytes, key=f"index_{db_time}")


@celery_app.task(bind=True)
def create_shard_task(self, shard_id: int):
    logger.info(f"[Shard {shard_id}] received task")
    shard_x_lock = RedisLock(
        client=redis_client, lock_name=f"shard_{shard_id}_lock", expire=60 * 5
    )
    shard_x_next_lock = RedisLock(
        client=redis_client, lock_name=f"shard_{shard_id}_lock_next", expire=60
    )
    if not shard_x_lock.acquire(blocking=False):
        if not shard_x_next_lock.acquire(blocking=False):
            logger.info(f"[Shard {shard_id}] already next task in queue, exiting...")
            return
        logger.info(f"[Shard {shard_id}] waiting for current generation completion")
        if not shard_x_lock.acquire(blocking=True, timeout=60):
            return

    if shard_x_next_lock.locked():
        shard_x_next_lock.release()
    logger.info(f"[Shard {shard_id}] starting generation")
    init_sync_db_engine()
    async_sessionmaker = create_sync_db_sessionmaker()
    shard_packages = {}
    with async_sessionmaker() as session:
        logger.info(f"[Shard {shard_id}] retrieving infos")
        shard_infos = session.execute(
            select(db_models.Shard).filter_by(id=shard_id)
        ).scalar_one_or_none()
        logger.info(f"[Shard {shard_id}] retrieving packages")
        db_packages_on_selected_shard = session.execute(
            select(db_models.Package).filter_by(shard_id=shard_id, meta=False)
        )
        shard_db_packages = {
            package.id: package
            for package in db_packages_on_selected_shard.scalars().all()
        }
        for package_id, package_data in shard_db_packages.items():
            shard_packages[package_id] = [
                {
                    "version": package_version.version,
                    "url": package_version.url,
                }
                for package_version in package_data.versions
            ]

    logger.info(f"[Shard {shard_id}] building binary shard generation")
    msgpack_bytes = msgpack.packb(shard_packages)
    logger.info(f"[Shard {shard_id}] uploading generation {shard_infos.generation}")
    shard_generation_url = upload_to_s3(
        data=msgpack_bytes,
        key=f"{SHARDS_PREFIX}/{shard_id}_{shard_infos.generation}",
    )
    with async_sessionmaker() as session:
        logger.info(f"[Shard {shard_id}] updating generation count")
        session.execute(
            update(db_models.Shard)
            .where(db_models.Shard.id == shard_id)
            .values(
                generation=shard_infos.generation + 1, location=shard_generation_url
            )
        )
        package_versions_where_clauses = [
            and_(
                db_models.PackageVersion.package_id == package_id,
                db_models.PackageVersion.version == package_version.version,
            )
            for package_id, package_data in shard_db_packages.items()
            for package_version in package_data.versions
        ]
        logger.info(f"[Shard {shard_id}] updating packages published field")
        if package_versions_where_clauses:
            session.execute(
                update(db_models.PackageVersion)
                .where(*package_versions_where_clauses)
                .values(published=True)
            )
        session.commit()
    logger.info(f"[Shard {shard_id}] sleeping...")
    time.sleep(60)  # packages can't be published again before 60 seconds
    shard_x_lock.keep_alive_until_expiration()  # todo: implement this instead of sleep


def clean_old_shards_generations():
    init_sync_db_engine()
    async_sessionmaker = create_sync_db_sessionmaker()
