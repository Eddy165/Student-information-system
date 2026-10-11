"""Database adapter shared by the web application and API blueprints."""
import sqlite3


class Database:
    """Small parameterized query adapter for SQLite and PostgreSQL."""
    def __init__(self, connection, postgres=False):
        self.connection = connection
        self.postgres = postgres

    def execute(self, sql, params=()):
        return self.connection.execute(sql.replace('?', '%s') if self.postgres else sql, params)

    def executemany(self, sql, values):
        if self.postgres:
            return self.connection.cursor().executemany(sql.replace('?', '%s'), values)
        return self.connection.executemany(sql, values)

    def executescript(self, sql):
        if self.postgres:
            raise RuntimeError('PostgreSQL schema must be applied statement-by-statement.')
        return self.connection.executescript(sql)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, _exc, _tb):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()
