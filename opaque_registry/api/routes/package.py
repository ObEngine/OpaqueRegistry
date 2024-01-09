from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

import opaque_registry.services.package as package_service
from opaque_registry.api.errors.packages import PackageNotFoundError
from opaque_registry.api.schemas.package import (
    NewPackage,
    NewPackageVersion,
    Package,
    PackageList,
    PackageVersion,
    PackageVersionList,
)
from opaque_registry.database.connector import get_db_session

router = APIRouter(prefix="/packages", tags=["packages"])


@router.get("/", response_model=PackageList)
async def get_all_packages(db_session: AsyncSession = Depends(get_db_session)):
    packages = await package_service.get_all_packages(db_session=db_session)
    return PackageList(packages=packages)


@router.get("/{package_id}", response_model=Package)
async def get_package_by_id(
    package_id: str, db_session: AsyncSession = Depends(get_db_session)
):
    package = await package_service.get_package_by_id(
        db_session=db_session, package_id=package_id
    )
    return package


@router.get("/{package_id}/versions", response_model=PackageVersionList)
async def get_package_versions(
    package_id: str, db_session: AsyncSession = Depends(get_db_session)
):
    package_versions = await package_service.get_package_versions(
        db_session=db_session, package_id=package_id
    )
    return PackageVersionList(package_id=package_id, versions=package_versions)


@router.post("/", response_model=Package)
async def create_package(
    package: NewPackage, db_session: AsyncSession = Depends(get_db_session)
):
    return await package_service.create_package(db_session=db_session, package=package)


@router.post("/{package_id}/versions", response_model=PackageVersion)
async def create_package_version(
    package_id: str,
    package_version: NewPackageVersion,
    db_session: AsyncSession = Depends(get_db_session),
):
    return await package_service.create_package_version(
        db_session=db_session, package_id=package_id, package_version=package_version
    )
