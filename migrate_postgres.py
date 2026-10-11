"""Initialize or upgrade the PostgreSQL database used by production SIS."""
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from sis.db import Database
from sis.migrations import apply_migrations

BASE = Path(__file__).resolve().parent


def main():
    if os.getenv('SIS_ENV') != 'production':
        raise SystemExit('Set SIS_ENV=production only after deployment configuration is reviewed.')
    url = os.getenv('DATABASE_URL')
    if not url or not url.startswith(('postgres://', 'postgresql://')):
        raise SystemExit('DATABASE_URL must point to a PostgreSQL database.')
    schema = (BASE / 'schema_postgres.sql').read_text(encoding='utf-8')
    statements = [part.strip() for part in schema.split(';') if part.strip()]
    with psycopg.connect(url, row_factory=dict_row) as connection:
        db = Database(connection, postgres=True)
        for statement in statements:
            db.execute(statement)
        applied = apply_migrations(db, postgres=True)
    print(f'Applied/verified {len(statements)} base schema statements; migration version {applied[-1]["version"]}.')


if __name__ == '__main__':
    main()
