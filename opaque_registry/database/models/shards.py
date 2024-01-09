from sqlalchemy.orm import Mapped, mapped_column

from opaque_registry.database.models.base import Base


class Shard(Base):
    __tablename__ = "shard"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    location: Mapped[str] = mapped_column(nullable=False)
    generation: Mapped[int] = mapped_column(nullable=False, default=0)
