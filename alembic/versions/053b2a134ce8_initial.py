"""initial

Revision ID: 053b2a134ce8
Revises: 
Create Date: 2023-06-28 12:50:26.838772

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '053b2a134ce8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('package',
    sa.Column('id', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('package_version',
    sa.Column('package_id', sa.String(), nullable=False),
    sa.Column('version', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['package_id'], ['package.id'], ),
    sa.PrimaryKeyConstraint('package_id', 'version')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('package_version')
    op.drop_table('package')
    # ### end Alembic commands ###