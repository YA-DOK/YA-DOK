"""auto create user profiles

Revision ID: abbade5daee8
Revises: 794ab74c275c
Create Date: 2026-10-08 02:27:02.813018

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'abbade5daee8'
down_revision: str | Sequence[str] | None = '794ab74c275c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None



def upgrade() -> None:
    # Create a profile automatically when a new user signs up
    op.execute("""
        CREATE FUNCTION public.handle_new_user()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        SET search_path = ''
        AS $$
        BEGIN
            INSERT INTO public.profiles (
                id,
                full_name,
                avatar_url
            )
            VALUES (
                NEW.id,
                LEFT(NEW.raw_user_meta_data ->> 'full_name', 255),
                NEW.raw_user_meta_data ->> 'avatar_url'
            )
            ON CONFLICT (id) DO NOTHING;

            RETURN NEW;
        END;
        $$;
    """)

    # Run the function whenever Supabase creates a user
    op.execute("""
        CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW
        EXECUTE FUNCTION public.handle_new_user();
    """)

    # Create profiles for users registered before this migration
    op.execute("""
        INSERT INTO public.profiles (
            id,
            full_name,
            avatar_url
        )
        SELECT
            id,
            LEFT(raw_user_meta_data ->> 'full_name', 255),
            raw_user_meta_data ->> 'avatar_url'
        FROM auth.users
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TRIGGER IF EXISTS on_auth_user_created
        ON auth.users;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS public.handle_new_user();
    """)
