from pydantic import BaseModel

from opaque_registry.api.schemas.helpers.semver import SemVer


class Package(BaseModel):
    id: str
    description: str | None = None
    tags: list[str] | None = None
    meta: bool = False

    class Config:
        orm_mode = True


class NewPackage(BaseModel):
    id: str
    description: str | None = None
    tags: list[str] | None = None
    meta: bool = False


class PackageVersion(BaseModel):
    version: SemVer
    url: str

    class Config:
        orm_mode = True


class Dependency(BaseModel):
    package_id: str
    version: SemVer


class NewPackageVersion(BaseModel):
    version: SemVer
    url: str
    dependencies: list[Dependency] = []


class PackageVersionList(BaseModel):
    package_id: str
    versions: list[PackageVersion]


class PackageList(BaseModel):
    packages: list[Package]
