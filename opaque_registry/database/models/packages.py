from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from opaque_registry.database.models.base import Base


class Package(Base):
    __tablename__ = "package"

    id: Mapped[str] = mapped_column(primary_key=True)


class PackageVersion(Base):
    __tablename__ = "package_version"

    package_id: Mapped[str] = mapped_column(ForeignKey(Package.id), primary_key=True)
    version: Mapped[str] = mapped_column(primary_key=True)
    url: Mapped[str]
