from psycopg.errors import UniqueViolation
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import opaque_registry.database.models as db_models
from opaque_registry.api.errors.packages import (
    PackageAlreadyExistsError,
    PackageNotFoundError,
    PackageVersionAlreadyExistsError,
    PackageVersionNotYetPublished,
    SelfReferencingPackageError,
)
from opaque_registry.api.schemas.package import NewPackage, NewPackageVersion
from opaque_registry.async_tasks.shards.tasks import (
    create_shard_task,
    create_whole_index_task,
)
from opaque_registry.services.shards import (
    derive_shard_id_from_package_id,
    get_shard_count,
)


async def get_all_packages(db_session: AsyncSession) -> list[db_models.Package]:
    result = await db_session.execute(
        select(db_models.Package).options(
            joinedload(db_models.Package.tags_relationship)
        )
    )
    return result.scalars().unique().all()


async def get_package_by_id(
    db_session: AsyncSession, package_id: str
) -> db_models.Package | None:
    package_query = (
        select(db_models.Package)
        .where(db_models.Package.id == package_id)
        .options(joinedload(db_models.Package.tags_relationship))
    )
    db_package = (await db_session.execute(package_query)).unique().scalar_one_or_none()
    if db_package is None:
        raise PackageNotFoundError(package_id=package_id)
    return db_package


async def get_package_versions(
    db_session: AsyncSession, package_id: str
) -> db_models.Package | None:
    # ensures package exists
    package = await get_package_by_id(db_session=db_session, package_id=package_id)
    package_versions_query = select(db_models.PackageVersion).where(
        db_models.PackageVersion.package_id == package.id
    )
    db_package_versions = (
        (await db_session.execute(package_versions_query)).scalars().all()
    )
    return db_package_versions


async def create_package(
    db_session: AsyncSession, package: NewPackage
) -> db_models.Package:
    shard_id = derive_shard_id_from_package_id(
        package_id=package.id,
        shard_count=(await get_shard_count(db_session=db_session)),
    )
    db_package = db_models.Package(id=package.id, shard_id=shard_id)
    db_session.add(db_package)
    try:
        await db_session.flush()
    except IntegrityError as exc:
        # if isinstance(exc.orig, Non)
        if exc.orig is not None and isinstance(exc.orig, UniqueViolation):
            raise PackageAlreadyExistsError(package_id=package.id) from exc
        raise exc
    db_session.add_all(
        [
            db_models.PackageTag(package_id=db_package.id, tag=tag)
            for tag in (package.tags or [])
        ]
    )
    await db_session.refresh(db_package)
    return db_package


async def create_package_version(
    db_session: AsyncSession, package_id: str, package_version: NewPackageVersion
) -> db_models.Package:
    # check if all dependencies are published
    # use in_ for optimization
    dependencies_where_clauses = [
        and_(
            db_models.PackageVersion.package_id == dependency.package_id,
            db_models.PackageVersion.version == dependency.version,
        )
        for dependency in package_version.dependencies
    ]
    dependencies_versions_query = select(db_models.PackageVersion).where(
        *dependencies_where_clauses
    )
    dependencies_versions = (
        ((await db_session.execute(dependencies_versions_query)).scalars().all())
        if dependencies_where_clauses
        else []
    )
    # ensures package exists
    _package = await get_package_by_id(db_session=db_session, package_id=package_id)

    for dependency_version in dependencies_versions:
        if dependency_version.package_id == package_id:
            raise SelfReferencingPackageError(
                package_id=package_id,
                package_version=package_version.version,
                dependency=f"{dependency_version.package_id}=={dependency_version.version}",
            )
        if not dependency_version.published:
            raise PackageVersionNotYetPublished(
                package_id=dependency_version.package_id,
                package_version=dependency_version.version,
            )

    db_package_version = db_models.PackageVersion(
        package_id=package_id, version=package_version.version, url=package_version.url
    )
    db_session.add(db_package_version)
    try:
        await db_session.flush()
    except IntegrityError as exc:
        if exc.orig is not None and isinstance(exc.orig, UniqueViolation):
            raise PackageVersionAlreadyExistsError(
                package_id=package_id, package_version=package_version.version
            ) from exc
        raise exc
    shard_id = derive_shard_id_from_package_id(
        package_id=package_id,
        shard_count=(await get_shard_count(db_session=db_session)),
    )
    create_shard_task.delay(shard_id=shard_id)
    create_whole_index_task.delay()
    return db_package_version
