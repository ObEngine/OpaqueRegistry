from sqlalchemy import ForeignKey, ForeignKeyConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from opaque_registry.database.models.base import Base


class Package(Base):
    __tablename__ = "package"

    id: Mapped[str] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(nullable=True)

    versions: Mapped[list["PackageVersion"]] = relationship("PackageVersion")
    tags_relationship: Mapped[list["PackageTag"]] = relationship(lazy="selectin")
    meta: Mapped[bool] = mapped_column(nullable=False, default=False)

    @hybrid_property
    def tags(self) -> list[str]:
        return [tag.tag for tag in self.tags_relationship]


class PackageTag(Base):
    __tablename__ = "package_tag"

    package_id: Mapped[str] = mapped_column(ForeignKey(Package.id), primary_key=True)
    tag: Mapped[str] = mapped_column(primary_key=True)


class PackageVersion(Base):
    __tablename__ = "package_version"

    package_id: Mapped[str] = mapped_column(ForeignKey(Package.id), primary_key=True)
    version: Mapped[str] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(nullable=False)


class PackageVersionDependency(Base):
    __tablename__ = "package_version_dependency"

    package_id: Mapped[str] = mapped_column(primary_key=True)
    version: Mapped[str] = mapped_column(primary_key=True)
    dependency: Mapped[str] = mapped_column(primary_key=True)
    dependency_version: Mapped[str] = mapped_column(primary_key=True)

    package_version: Mapped[PackageVersion] = relationship(
        foreign_keys=[package_id, version],
    )
    dependency_package_version: Mapped[PackageVersion] = relationship(
        foreign_keys=[dependency, dependency_version],
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["package_id", "version"],
            ["package_version.package_id", "package_version.version"],
        ),
        ForeignKeyConstraint(
            ["dependency", "dependency_version"],
            ["package_version.package_id", "package_version.version"],
        ),
    )
