"""Create users table manually

Revision ID: 10e5fb446bf6
Revises: 31e991d7aca4
Create Date: 2025-09-20 13:35:14.420460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10e5fb446bf6'
down_revision: Union[str, Sequence[str], None] = '31e991d7aca4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
