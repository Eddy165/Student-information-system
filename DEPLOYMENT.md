# Deployment preparation and launch gate

This is a **release candidate**, not a launched production service. The application deliberately refuses to start in production mode until required configuration is present. Do not mark the release ready based solely on environment flags. The institution must verify the evidence below.

## 1. Institution decisions needed

- Name and control of the custom domain, such as `sis.example.edu`.
- Hosting provider, PostgreSQL service, database region, retention and backup policy.
- Institution identity owner and procedure for provisioning and removing student/faculty accounts.
- Institution legal name, support and privacy contact, approved Privacy Policy and Terms and Conditions, including effective date.
- Whether data about minors is in scope and which approvals or safeguards are required. Obtain legal review for the applicable jurisdiction and current rules.
- Permission to use the institution name, logo or email domain in the public service.

## 2. Environment and database

Use `.env.production.example` as a field list. Put real values in a secret manager. Never commit a filled `.env`, password, database backup or policy document containing private information. Production requires PostgreSQL; the local demo uses SQLite and seeded accounts. The production database must start empty. Run the initial schema once with `python migrate_postgres.py` after configuring the database. Future schema changes need versioned, reviewed migrations; do not edit the applied initial schema in place.

Create the first administrator interactively after migration:

```bash
flask --app app create-admin
```

Use a unique administrator password of at least 12 characters. Never copy the three local demo accounts to production. Provision faculty and student accounts through the administrator interface after the service is secured.

## 3. Web process and transport

Run with a production WSGI process such as:

```bash
gunicorn 'app:app' --bind 127.0.0.1:8000 --workers 2 --threads 4 --timeout 30
```

Place it behind a maintained HTTPS reverse proxy or hosting gateway. Configure TLS, forwarding, rate limits and request size limits there as well. Never expose Flask's development server or the PostgreSQL port to the public internet. Grant the application database account only the permissions it needs. Monitor `/health` from an internal service monitor. Configure structured logs without credentials, tokens or student record payloads.

## 4. Domain and legal gate

Before changing `SIS_CUSTOM_DOMAIN_VERIFIED` to `yes`, verify that the custom-domain DNS records point to the chosen service, the TLS certificate covers that exact host, HTTPS works end to end, and all other hosts are rejected. Set `SIS_ALLOWED_HOSTS` to that exact hostname.

The application reads institution-approved text files as the Privacy Policy and Terms. It does not generate a legal policy or claim compliance on behalf of the institution. Ensure the actual files describe purposes of processing, categories of data, recipients, retention, contact and rights procedures where applicable. Have the institution's responsible person approve both texts and their effective date before setting `SIS_POLICIES_APPROVED=yes`.

Check the rendered sign-in and footer at the custom domain. The SVG favicon must load, both legal pages must be accessible while signed out, and no platform-added “made with AI” label may be present. The app itself adds no such label; a hosting service may inject one, so inspect the actual deployment.

## 5. Data and operations gate

- Use a managed PostgreSQL backup schedule, encrypted backups and a documented retention period. Perform a restore drill before launch.
- Test admin, faculty and student access against an isolated staging database with non-real data.
- Verify faculty cannot edit a different faculty member's course, students cannot read another student's records, and old sessions stop working after password change.
- Define account recovery and support. The current code has password change for signed-in users, but **no self-service password reset**. The administrator must have an approved, authenticated recovery procedure before use at scale.
- Review logs, uptime alerts, incident contact, access review, dependency updates and a process for removing departed users.
- Run `python -m unittest discover -s tests -v`; perform a separate PostgreSQL integration test in staging. The included automated tests run against SQLite and do not prove the PostgreSQL deployment.
- Check keyboard access, contrast and zoom on the actual browsers used by the institution.

## 6. Known limits of this release candidate

The `/portal` workspace is a responsive JavaScript interface over the versioned REST API; data-entry and management workflows remain available in the authenticated server-rendered routes. Saved records are visible on the next request. It does not push live updates into already-open tabs. Fee records do not process money. There is no institutional SSO, password recovery, export of audit logs or automatic database migration framework. These require institution-specific design and operational review before an actual institutional launch.

## V2 deployment additions

The V2 project adds a versioned migration layer, REST API, API-token management, Docker support, administrator analytics, and GitHub Actions CI.

### Migration workflow

The application treats the existing database schema as migration `001_baseline_schema` and applies numbered migrations after it. Do not edit an already-applied migration; add a new numbered SQL migration instead.

### API tokens

Create a token for an existing user:

```bash
flask --app app create-api-token
```

Revoke it by database ID:

```bash
flask --app app revoke-api-token TOKEN_ID
```

Only the token hash is stored. The raw token is shown once.

### Docker

For a local SQLite demo (the Compose file is not a production deployment):

```bash
docker compose up --build
```

The local Compose file starts the seeded SQLite demo and binds to loopback only. It does not start PostgreSQL and is not a production deployment. For production, provision managed PostgreSQL, apply the schema with `python migrate_postgres.py`, set all required environment variables through a secret manager, and create the first administrator interactively. The included legal documents are development placeholders. They do not satisfy real institutional launch requirements.

### CI

`.github/workflows/ci.yml` runs:

- Python installation
- SQLite integration tests
- PostgreSQL smoke/integration tests
- Python compile checks
- Ruff linting

The production database still requires operational backups, monitoring, HTTPS, secret management, institutional policy approval, and a security review.
