"""phase3_extraction_tables

Revision ID: cf1856199a65
Revises: 972b65bd67fa
Create Date: 2026-07-30 22:50:23.049095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cf1856199a65'
down_revision: Union[str, Sequence[str], None] = '972b65bd67fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Declare the enum separately so we can CREATE TYPE before the table references it
# and DROP TYPE in downgrade after tables are removed.
extraction_status_enum = postgresql.ENUM(
    'PENDING', 'SUCCESS', 'FAILED',
    name='extraction_status_enum',
    create_type=False,   # we manage creation/deletion ourselves below
)


def upgrade() -> None:
    """Upgrade schema: create extraction_status_enum type, then both tables."""

    # Step 1: create the Postgres enum type
    extraction_status_enum.create(op.get_bind(), checkfirst=True)

    # Step 2: extracted_quotations (1:1 with quotations)
    op.create_table(
        'extracted_quotations',
        sa.Column('quotation_id', sa.UUID(), nullable=False),
        sa.Column('vendor_name', sa.String(length=512), nullable=True),
        sa.Column('vendor_address', sa.Text(), nullable=True),
        sa.Column('vendor_email', sa.String(length=320), nullable=True),
        sa.Column('vendor_phone', sa.String(length=50), nullable=True),
        sa.Column('vendor_gst_number', sa.String(length=100), nullable=True),
        sa.Column('quotation_number', sa.String(length=256), nullable=True),
        sa.Column('quotation_date', sa.String(length=100), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('valid_until', sa.String(length=100), nullable=True),
        sa.Column('subtotal', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('discount', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('shipping_cost', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('tax', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('grand_total', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('delivery_time', sa.String(length=256), nullable=True),
        sa.Column('warranty', sa.String(length=512), nullable=True),
        sa.Column('incoterms', sa.String(length=100), nullable=True),
        sa.Column(
            'extraction_status',
            postgresql.ENUM(
                'PENDING', 'SUCCESS', 'FAILED',
                name='extraction_status_enum',
                create_type=False,
            ),
            server_default='PENDING',   # uppercase — matches Postgres enum label
            nullable=False,
        ),
        sa.Column('extraction_model', sa.String(length=128), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['quotation_id'], ['quotations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_extracted_quotations_quotation_id',
        'extracted_quotations', ['quotation_id'], unique=True,
    )
    op.create_index(
        'ix_extracted_quotations_extraction_status',
        'extracted_quotations', ['extraction_status'], unique=False,
    )

    # Step 3: extracted_quotation_items (1:N with extracted_quotations)
    op.create_table(
        'extracted_quotation_items',
        sa.Column('extracted_quotation_id', sa.UUID(), nullable=False),
        sa.Column('item_name', sa.String(length=512), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('unit', sa.String(length=100), nullable=True),
        sa.Column('unit_price', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ['extracted_quotation_id'], ['extracted_quotations.id'], ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_extracted_quotation_items_extracted_quotation_id',
        'extracted_quotation_items', ['extracted_quotation_id'], unique=False,
    )


def downgrade() -> None:
    """Downgrade schema: remove both tables then the custom enum type."""
    op.drop_index('ix_extracted_quotation_items_extracted_quotation_id', table_name='extracted_quotation_items')
    op.drop_table('extracted_quotation_items')
    op.drop_index('ix_extracted_quotations_extraction_status', table_name='extracted_quotations')
    op.drop_index('ix_extracted_quotations_quotation_id', table_name='extracted_quotations')
    op.drop_table('extracted_quotations')
    # Drop enum type only after all referencing tables are gone
    extraction_status_enum.drop(op.get_bind(), checkfirst=True)
