"""initial

Revision ID: 118927438150
Revises: 
Create Date: 2023-08-23 23:37:37.902413

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '118927438150'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('shard',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('location', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('package',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('meta', sa.Boolean(), nullable=False),
    sa.Column('shard_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['shard_id'], ['shard.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('package_tag',
    sa.Column('package_id', sa.String(), nullable=False),
    sa.Column('tag', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('package_id', 'tag')
    )
    op.create_table('package_version',
    sa.Column('package_id', sa.String(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('package_id', 'version')
    )
    op.create_table('package_version_dependency',
    sa.Column('package_id', sa.String(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('dependency', sa.String(), nullable=False),
    sa.Column('dependency_version', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['dependency', 'dependency_version'], ['package_version.package_id', 'package_version.version'], ),
    sa.ForeignKeyConstraint(['package_id', 'version'], ['package_version.package_id', 'package_version.version'], ),
    sa.PrimaryKeyConstraint('package_id', 'version', 'dependency', 'dependency_version')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('package_version_dependency')
    op.drop_table('package_version')
    op.drop_table('package_tag')
    op.drop_table('package')
    op.drop_table('shard')
    # ### end Alembic commands ###