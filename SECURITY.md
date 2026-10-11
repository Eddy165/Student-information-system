# Security and production readiness

## Security controls implemented

- Passwords are stored using Werkzeug's password hashing utilities, never plaintext.
- Cookie sessions are HTTP-only, SameSite=Lax, time-limited, and Secure in production.
- CSRF tokens are required for browser state-changing requests, including the portal logout API.
- Login attempts are throttled using username and hashed source address windows.
- Authorization is enforced server-side by role and by course/student ownership checks.
- SQL is parameterized throughout the application.
- API bearer tokens are stored as SHA-256 hashes and can be revoked.
- Security headers include a restrictive Content Security Policy, frame denial, MIME sniffing protection, and referrer policy; HSTS is enabled in production.
- Production startup fails closed if required environment variables, PostgreSQL, verified-domain declaration, or approved policy files are missing.
- Demo records use reserved `.test` email domains and synthetic contact details.

## Before real institutional deployment

This repository is a student project, not a certified or independently audited product. Do not put real student records into a public deployment until the institution completes a security review and privacy/legal review.

1. Set `SIS_ENV=production`; use managed PostgreSQL with TLS verification and least-privilege credentials.
2. Generate a unique secret with `python -c "import secrets; print(secrets.token_urlsafe(48))"` and inject it through a secret manager. Never commit `.env`, keys, database files, or production data.
3. Set a real `SIS_ALLOWED_HOSTS` list and configure HTTPS at a trusted reverse proxy or platform edge.
4. Supply institution-approved Privacy Policy and Terms files and complete domain verification before enabling production mode.
5. Run `flask --app app create-admin` against the production database to provision the first administrator. Do not use demo accounts in production.
6. Apply schema changes through reviewed migrations; test restore procedures and backups before go-live.
7. Add centralized logs/alerts, dependency and container scanning, external penetration testing, data-retention/deletion procedures, incident response, and a documented access review.
8. Configure MFA/SSO, account recovery, email verification, and administrative approval workflows before handling sensitive academic data.

## Report a vulnerability

Do not publish credentials, student records, or exploitable details in public issues. Contact the repository maintainer privately and include reproduction steps and impact.
