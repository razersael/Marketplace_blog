"""init_migration

Revision ID: a408d172a2f1
Revises:
Create Date: 2026-04-17 18:25:32.610749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

# revision identifiers, used by Alembic.
revision: str = 'a408d172a2f1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    """Создаёт все таблицы с полнотекстовым поиском"""

    # 1. Таблица users
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('email', sa.String(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=False),
                    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('email'),
                    sa.UniqueConstraint('username')
                    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'])

    # 2. Таблица categories
    op.create_table('categories',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(), nullable=False),
                    sa.Column('description', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name')
                    )
    op.create_index('ix_categories_id', 'categories', ['id'])
    op.create_index('ix_categories_name', 'categories', ['name'])

    # 3. Таблица posts
    op.create_table('posts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(length=200), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('image_url', sa.String(length=500), nullable=True),
                    sa.Column('category_id', sa.Integer(), nullable=False),
                    sa.Column('author_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                    sa.Column('search_vector', TSVECTOR, nullable=True),
                    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
                    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index('ix_posts_category_id', 'posts', ['category_id'])
    op.create_index('ix_posts_created_at', 'posts', ['created_at'])

    # 4. GIN индекс для полнотекстового поиска
    op.execute("""
               CREATE INDEX posts_search_vector_idx
                ON posts USING GIN (search_vector)
               """)

    # 5. Функция для автоматического обновления вектора
    op.execute("""
               CREATE
               OR REPLACE FUNCTION posts_search_vector_update()
        RETURNS trigger AS $$
               BEGIN
            NEW.search_vector
               :=
                setweight(to_tsvector('russian', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('russian', COALESCE(NEW.content, '')), 'B');
               RETURN NEW;
               END
        $$
               LANGUAGE plpgsql;
               """)

    # 6. Триггер для автоматического обновления
    op.execute("""
               CREATE TRIGGER posts_search_vector_trigger
                   BEFORE INSERT OR
               UPDATE ON posts
                   FOR EACH ROW
                   EXECUTE FUNCTION posts_search_vector_update();
               """)

    # 7. Таблица deleted_posts (для фейкового удаления)
    op.create_table('deleted_posts',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('original_id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(length=200), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('image_url', sa.String(length=500), nullable=True),
                    sa.Column('category_id', sa.Integer(), nullable=False),
                    sa.Column('author_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('deleted_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                    sa.ForeignKeyConstraint(['author_id'], ['users.id']),
                    sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index('ix_deleted_posts_id', 'deleted_posts', ['id'])
    op.create_index('ix_deleted_posts_original_id', 'deleted_posts', ['original_id'])


def downgrade():
    """Удаляет все таблицы (откат миграции)"""

    # Удаляем таблицы в обратном порядке (из-за внешних ключей)
    op.drop_index('ix_deleted_posts_original_id', table_name='deleted_posts')
    op.drop_index('ix_deleted_posts_id', table_name='deleted_posts')
    op.drop_table('deleted_posts')

    # Удаляем триггер и функцию
    op.execute("DROP TRIGGER IF EXISTS posts_search_vector_trigger ON posts")
    op.execute("DROP FUNCTION IF EXISTS posts_search_vector_update()")

    # Удаляем индекс полнотекстового поиска
    op.execute("DROP INDEX IF EXISTS posts_search_vector_idx")

    # Удаляем таблицу posts
    op.drop_index('ix_posts_title', table_name='posts')
    op.drop_index('ix_posts_id', table_name='posts')
    op.drop_index('ix_posts_created_at', table_name='posts')
    op.drop_index('ix_posts_category_id', table_name='posts')
    op.drop_index('ix_posts_author_id', table_name='posts')
    op.drop_table('posts')

    # Удаляем таблицу categories
    op.drop_index('ix_categories_name', table_name='categories')
    op.drop_index('ix_categories_id', table_name='categories')
    op.drop_table('categories')

    # Удаляем таблицу users
    op.drop_index('ix_users_username', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
