"""added package_version.published and shard.generation

Revision ID: c2f749b4f233
Revises: 118927438150
Create Date: 2023-09-14 02:09:06.905313

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c2f749b4f233"
down_revision = "118927438150"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "package_version",
        sa.Column("published", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "shard",
        sa.Column("generation", sa.Integer(), nullable=False, server_default="0"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("shard", "generation")
    op.drop_column("package_version", "published")
    # ### end Alembic commands ###