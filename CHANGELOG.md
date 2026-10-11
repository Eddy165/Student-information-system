# Changelog

## V2.0.0 - Engineering Upgrade

### Added
- `sis/` support package for database, migrations, API, and admin tooling.
- Versioned migration history with `schema_migrations`.
- Revocable bearer API tokens.
- REST API under `/api/v1`.
- API attendance and marks write endpoints.
- Admin analytics dashboard.
- Admin audit-log dashboard.
- OpenAPI 3 documentation.
- Dockerfile and PostgreSQL Docker Compose setup.
- GitHub Actions CI.
- PostgreSQL smoke/integration test.

### Improved
- PostgreSQL initialization and migrations are part of the application deployment path.
- Browser CSRF protection remains enabled while bearer-authenticated API writes use API authentication.
- Documentation now distinguishes academic/demo readiness from real institutional production readiness.

### Preserved
- Existing role model: Administrator, Faculty, Student.
- Existing academic workflows and templates.
- Existing security headers, password hashing, login throttling, session invalidation, and audit recording.
