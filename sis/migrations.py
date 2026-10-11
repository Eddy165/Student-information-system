"""Lightweight, versioned migrations for the SIS without hiding schema changes."""
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
MIGRATION_DIR = BASE / 'sis' / 'migrations'


def _statements(path):
    return [part.strip() for part in path.read_text(encoding='utf-8').split(';') if part.strip()]


def apply_migrations(database, postgres=False):
    """Apply pending numbered SQL migrations and record their versions.

    The initial schema is treated as migration 001 (baseline). This lets existing
    installations upgrade safely while fresh installations receive the same history.
    """
    applied_at_type = 'TIMESTAMPTZ' if postgres else 'TEXT'
    database.execute(f'CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at {applied_at_type} NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    database.commit()
    current = database.execute('SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations').fetchone()['version']
    if current == 0:
        with database:
            database.execute('INSERT INTO schema_migrations(version,name) VALUES(?,?)', (1, '001_baseline_schema'))
        current = 1
    pattern = '[0-9][0-9][0-9]_*.sql'
    files = []
    for path in sorted(MIGRATION_DIR.glob(pattern)):
        if path.name.startswith('001_') or path.name.endswith('_postgres.sql'):
            continue
        if postgres:
            pg = path.with_name(path.stem + '_postgres.sql')
            if pg.exists():
                path = pg
        files.append(path)
    for path in files:
        version = int(path.name[:3])
        if version <= current:
            continue
        with database:
            for statement in _statements(path):
                database.execute(statement)
            database.execute('INSERT INTO schema_migrations(version,name) VALUES(?,?)', (version, path.stem))
    return database.execute('SELECT version,name,applied_at FROM schema_migrations ORDER BY version').fetchall()
