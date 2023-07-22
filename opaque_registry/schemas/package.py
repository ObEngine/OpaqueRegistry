from pydantic import BaseModel


class Package(BaseModel):
    id: str


class NewPackage(BaseModel):
    id: str


class PackageList(BaseModel):
    packages: list[Package]
