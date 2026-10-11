
import os
import unittest

import psycopg
from psycopg.rows import dict_row


class PostgreSQLSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.getenv("SIS_TEST_DATABASE_URL")

        if not cls.url:
            raise unittest.SkipTest(
                "SIS_TEST_DATABASE_URL is not configured"
            )

        from app import create_app

        cls.app = create_app({
            "TESTING": True,
            "DATABASE_URL": cls.url,
            "PRODUCTION": True,
            "SECRET_KEY": "test-postgres-secret-key-32-characters-long",
        })

    def test_health_and_migration_history(self):
        client = self.app.test_client()

        response = client.get("/health")
        self.assertEqual(response.status_code, 200)

        with psycopg.connect(
            self.url, row_factory=dict_row
        ) as connection:
            migrations = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()

            self.assertEqual(
                [row["version"] for row in migrations], [1, 2]
            )

            table = connection.execute(
                "SELECT to_regclass('api_tokens') AS table_name"
            ).fetchone()

            self.assertIsNotNone(table["table_name"])


if __name__ == "__main__":
    unittest.main()