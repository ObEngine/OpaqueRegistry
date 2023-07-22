from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from opaque_registry.database.connector import get_db_session
from opaque_registry.schemas.package import NewPackage, Package, PackageList
import opaque_registry.services.package as package_service


router = APIRouter(prefix="/packages")


@router.get("/", response_model=PackageList)
async def get_all_packages(db_session: AsyncSession = Depends(get_db_session)):
    packages = await package_service.get_all_packages(db_session=db_session)
    return PackageList(packages=packages)


@router.post("/", response_model=Package)
async def create_package(
    package: NewPackage, db_session: AsyncSession = Depends(get_db_session)
):
    return await package_service.create_package(db_session=db_session, package=package)
