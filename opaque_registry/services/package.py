from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

import opaque_registry.database.models as db_models
from opaque_registry.api.errors.packages import (
    PackageAlreadyExistsError,
    PackageVersionAlreadyExistsError,
)
from opaque_registry.api.schemas.package import NewPackage, NewPackageVersion


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
    return db_package


async def get_package_versions(
    db_session: AsyncSession, package_id: str
) -> db_models.Package | None:
    package_versions_query = select(db_models.PackageVersion).where(
        db_models.PackageVersion.package_id == package_id
    )
    db_package_versions = (
        (await db_session.execute(package_versions_query)).scalars().all()
    )
    return db_package_versions


async def create_package(
    db_session: AsyncSession, package: NewPackage
) -> db_models.Package:
    db_package = db_models.Package(id=package.id)
    db_session.add(db_package)
    try:
        await db_session.flush()
    except IntegrityError as exc:
        raise PackageAlreadyExistsError(package_name=package.id) from exc
    return db_package


async def create_package_version(
    db_session: AsyncSession, package_id: str, package_version: NewPackageVersion
) -> db_models.Package:
    db_package_version = db_models.PackageVersion(
        package_id=package_id, version=package_version.version, url=package_version.url
    )
    db_session.add(db_package_version)
    try:
        await db_session.flush()
    except IntegrityError as exc:
        raise PackageVersionAlreadyExistsError(
            package_id=package_id, version=package_version.version
        ) from exc
    return db_package_version
