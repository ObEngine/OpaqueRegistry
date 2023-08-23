import os

import boto3
import msgpack
from sqlalchemy import select

import opaque_registry.database.models as db_models
from opaque_registry.celery_app import celery_app
from opaque_registry.database.connector import create_sync_sessionmaker

OBJECT_STORAGE_REGION = os.getenv("OBJECT_STORAGE_REGION", "fra1")
OBJECT_STORAGE_BUCKET = os.getenv("OBJECT_STORAGE_BUCKET", "obengine-packages")
OBJECT_STORAGE_KEY = os.environ["OBJECT_STORAGE_KEY"]
OBJECT_STORAGE_SECRET = os.environ["OBJECT_STORAGE_SECRET"]


def upload_to_s3(data: bytes, key: str):
    s3config = {
        "region_name": OBJECT_STORAGE_REGION,
        "endpoint_url": "https://{}.digitaloceanspaces.com".format(
            OBJECT_STORAGE_REGION
        ),
        "aws_access_key_id": OBJECT_STORAGE_KEY,
        "aws_secret_access_key": OBJECT_STORAGE_SECRET,
    }

    # Initializing S3.ServiceResource object - http://boto3.readthedocs.io/en/latest/reference/services/s3.html#service-resource
    s3resource = boto3.resource("s3", **s3config)
    s3client = boto3.client("s3", **s3config)

    for bucket in s3resource.buckets.all():
        print(bucket)

    s3object = s3resource.Bucket(OBJECT_STORAGE_BUCKET).put_object(Key=key, Body=data)
    object_url = s3client.generate_presigned_url(
        "get_object",
        Params={"Bucket": OBJECT_STORAGE_BUCKET, "Key": s3object.key},
        ExpiresIn=60 * 60,
    )


@celery_app.task
def create_shard_task(shard_id: int):
    async_sessionmaker = create_sync_sessionmaker()
    shard_packages = {}
    with async_sessionmaker() as session:
        shard_infos = session.execute(
            select(db_models.Shard).filter_by(id=shard_id)
        ).scalar_one_or_none()
        db_packages_on_selected_shard = session.execute(
            select(db_models.Package).filter_by(shard_id=shard_id, meta=False)
        )

        for db_package in db_packages_on_selected_shard.scalars().all():
            shard_packages[db_package.id] = [
                {
                    "version": package_version.version,
                    "url": package_version.url,
                }
                for package_version in db_package.versions
            ]

    msgpack_bytes = msgpack.packb(shard_packages)
    with open(f"shard_{shard_id}.msgpack", "wb") as f:
        f.write(msgpack_bytes)

    # upload to s3 based on shard location
    s3 = boto3.client("s3")


upload_to_s3(b"hello", f"shard_1")
