from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import opaque_registry.database.models as db_models
from opaque_registry.schemas.package import NewPackage, Package


def package_model_to_schema(db_package: db_models.Package):
    return Package(id=db_package.id)


async def get_all_packages(db_session: AsyncSession):
    result = await db_session.execute(select(db_models.Package))
    return result.all()


async def create_package(db_session: AsyncSession, package: NewPackage):
    db_package = db_models.Package(id=package.id)
    db_session.add(db_package)
    try:
        await db_session.flush()
    except IntegrityError as exc:
        pass
    return package_model_to_schema(db_package=db_package)
