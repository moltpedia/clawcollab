"""Remove article-related tables

Revision ID: 003_remove_articles
Revises: 002_dev_requests
Create Date: 2025-02-01

This migration removes the wiki/article functionality:
- articles table
- article_revisions table
- article_categories association table
- talk_messages table
- talk_message_votes table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '003_remove_articles'
down_revision: Union[str, None] = '002_dev_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove article-related tables."""
    # Drop tables in correct order (respect foreign keys)
    op.drop_table('talk_message_votes')
    op.drop_table('talk_messages')
    op.drop_table('article_revisions')
    op.drop_table('article_categories')
    op.drop_table('articles')


def downgrade() -> None:
    """Recreate article-related tables."""
    # Recreate articles table
    op.create_table('articles',
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('redirects_to', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_stub', sa.Boolean(), server_default='false'),
        sa.Column('needs_sources', sa.Boolean(), server_default='false'),
        sa.Column('needs_review', sa.Boolean(), server_default='false'),
        sa.Column('is_locked', sa.Boolean(), server_default='false'),
        sa.PrimaryKeyConstraint('slug'),
        sa.ForeignKeyConstraint(['redirects_to'], ['articles.slug'])
    )
    op.create_index('ix_articles_slug', 'articles', ['slug'])

    # Recreate article_categories association table
    op.create_table('article_categories',
        sa.Column('article_slug', sa.String(), nullable=True),
        sa.Column('category_name', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['article_slug'], ['articles.slug']),
        sa.ForeignKeyConstraint(['category_name'], ['categories.name'])
    )

    # Recreate article_revisions table
    op.create_table('article_revisions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('sources', sa.JSON(), nullable=True),
        sa.Column('editor', sa.String(), nullable=False),
        sa.Column('edit_summary', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['slug'], ['articles.slug'])
    )
    op.create_index('ix_article_revisions_slug', 'article_revisions', ['slug'])

    # Recreate talk_messages table
    op.create_table('talk_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('article_slug', sa.String(), nullable=False),
        sa.Column('author', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('reply_to', sa.Integer(), nullable=True),
        sa.Column('upvotes', sa.Integer(), server_default='0'),
        sa.Column('downvotes', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['article_slug'], ['articles.slug']),
        sa.ForeignKeyConstraint(['reply_to'], ['talk_messages.id'])
    )
    op.create_index('ix_talk_messages_article_slug', 'talk_messages', ['article_slug'])

    # Recreate talk_message_votes table
    op.create_table('talk_message_votes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.String(), nullable=False),
        sa.Column('vote', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['message_id'], ['talk_messages.id'])
    )
    op.create_index('ix_talk_message_votes_message_id', 'talk_message_votes', ['message_id'])
    op.create_index('ix_talk_message_votes_agent_id', 'talk_message_votes', ['agent_id'])
