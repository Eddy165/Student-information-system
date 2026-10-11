<div align="center">

# 🎓 Student Information System

**A role-based academic management system for administrators, faculty, and students.**

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square\&logo=python\&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-000000?style=flat-square\&logo=flask\&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Local%20Database-003B57?style=flat-square\&logo=sqlite\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Production%20Target-4169E1?style=flat-square\&logo=postgresql\&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Templates-E34F26?style=flat-square\&logo=html5\&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Responsive%20UI-1572B6?style=flat-square\&logo=css3\&logoColor=white)

> **A software engineering mini project implementing a complete academic workflow across Administrator, Faculty, and Student roles.**

> Built as a functioning implementation of the academic management workflows and UI prototype developed across Experiments 1–10.

</div>

---

## 📋 Table of Contents

* [Overview](#-overview)
* [Why This System?](#-why-this-system)
* [V2 Engineering Improvements](#-v2-engineering-improvements)
* [Key Features](#-key-features)
* [Role-Based Access](#-role-based-access)
* [System Architecture](#-system-architecture)
* [Academic Workflow](#-academic-workflow)
* [Tech Stack](#-tech-stack)
* [Repository Structure](#-repository-structure)
* [Database Design](#-database-design)
* [Authentication and Accounts](#-authentication-and-accounts)
* [Attendance Management](#-attendance-management)
* [Marks and Results](#-marks-and-results)
* [Timetable and Fees](#-timetable-and-fees)
* [Reports](#-reports)
* [REST API](#-rest-api)
* [Security Controls](#-security-controls)
* [Admin Analytics and Audit Log](#-admin-analytics-and-audit-log)
* [Environment and Configuration](#-environment-and-configuration)
* [Local Development](#-local-development)
* [Demo Accounts](#-demo-accounts)
* [Suggested Live Demonstration](#-suggested-live-demonstration)
* [Testing](#-testing)
* [Docker and PostgreSQL](#-docker-and-postgresql)
* [Production Configuration](#-production-configuration)
* [Project Boundaries](#-project-boundaries)
* [Experiment Alignment](#-experiment-alignment)
* [Design Principles](#-design-principles)
* [Future Improvements](#-future-improvements)
* [Git Workflow](#-git-workflow)
* [License](#-license)

---

# 🎯 Overview

The **Student Information System (SIS)** is a role-based academic management application designed to manage core academic activities within an educational institution.

The system provides separate workflows for:

* **Administrators**
* **Faculty**
* **Students**

The local application is implemented using **Flask and SQLite**, with server-rendered role-specific pages and a responsive interface based on the project's navy, teal, and white visual design.

A separate **production configuration targets PostgreSQL** and intentionally refuses startup when critical launch settings are missing. This keeps the local academic demonstration separate from a potentially live institutional deployment.

> **Important:** The earlier browser-only hosted prototype is **not** this application. This repository contains the functioning Flask-based Student Information System.

---

# 🎯 Why This System?

Academic information is commonly distributed across multiple systems, spreadsheets, forms, and manual processes.

A centralized Student Information System brings the core academic workflows into one application.

| Academic Requirement | SIS Solution                                                |
| -------------------- | ----------------------------------------------------------- |
| Student management   | Administrator can create and manage student records         |
| Faculty management   | Administrator maintains faculty records and assignments     |
| Course management    | Courses can be created and managed centrally                |
| Enrollment           | Students can be enrolled into courses                       |
| Attendance           | Faculty can record attendance by course and date            |
| Internal marks       | Faculty can enter and update internal assessment marks      |
| External marks       | Faculty can record external marks                           |
| Timetable            | Administrator can maintain academic schedules               |
| Fee tracking         | Payment status can be maintained for students               |
| Academic reports     | CSV reports can be previewed and downloaded                 |
| Role separation      | Administrator, Faculty, and Student workflows are separated |

The project focuses on the **core academic information workflow required for a Software Engineering mini project**.

It is not intended to be a payment platform or a complete enterprise ERP.

---

# 🚀 V2 Engineering Improvements

Version 2 keeps the original academic workflows and visual language while addressing several engineering weaknesses from the earlier version.

### Major improvements

* Extracted database, migration, API, and administrator tooling into a package structure.
* Added versioned database migrations.
* Added a baseline migration and API-token migration.
* PostgreSQL can be initialized and upgraded through the application deployment path.
* Added a versioned REST API under `/api/v1`.
* Added revocable bearer-token authentication.
* Added role-scoped API authorization.
* Added API write endpoints for attendance and marks.
* Added administrator analytics.
* Added an administrator audit-log dashboard.
* Added OpenAPI documentation in `docs/openapi.yaml`.
* Added Docker and PostgreSQL development deployment.
* Added GitHub Actions CI.
* Expanded automated tests for API authentication, authorization scoping, and attendance writes.

> **Project status:** This is a strong academic and portfolio project, but it is **not automatically a production institutional deployment**. Real deployment still requires institution-approved policies, secrets management, backups, monitoring, HTTPS, PostgreSQL operations, and security review.

---

# ✨ Key Features

## 👨‍💼 Administrator

Administrators provide centralized academic management.

* Manage students
* Manage faculty
* Manage courses
* Manage enrollments
* Maintain timetable information
* Maintain fee payment statuses
* Preview CSV reports
* Download attendance reports
* Download marks reports
* Create student accounts
* Create faculty accounts
* View analytics
* View audit logs

---

## 👨‍🏫 Faculty

Faculty members work with courses assigned to them.

* View assigned courses
* View students enrolled in assigned courses
* Select a course and attendance date
* Record attendance
* Correct attendance for an existing student/course/date combination
* Enter internal assessment marks
* Enter external marks
* Update existing assessment marks

---

## 👨‍🎓 Student

Students receive a read-only academic view of their information.

* View personal profile
* View enrolled courses
* View attendance
* View academic results
* View timetable
* View fee status

---

# 🔐 Role-Based Access

The application separates functionality according to the authenticated user's role.

```text
                         ┌─────────────────────────┐
                         │ STUDENT INFORMATION      │
                         │ SYSTEM                   │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
              ▼                       ▼                       ▼
      ┌────────────────┐      ┌────────────────┐      ┌────────────────┐
      │ Administrator  │      │    Faculty     │      │    Student     │
      └───────┬────────┘      └───────┬────────┘      └───────┬────────┘
              │                       │                       │
              ▼                       ▼                       ▼
       Manage academic         Attendance & marks        Read-only
           records                 management             information
```

## Permission Matrix

| Capability            | Administrator | Faculty | Student |
| --------------------- | :-----------: | :-----: | :-----: |
| Manage Students       |       ✅       |    ❌    |    ❌    |
| Manage Faculty        |       ✅       |    ❌    |    ❌    |
| Manage Courses        |       ✅       |    ❌    |    ❌    |
| Manage Enrollment     |       ✅       |    ❌    |    ❌    |
| Maintain Timetable    |       ✅       |    ❌    |    ❌    |
| Maintain Fee Status   |       ✅       |    ❌    |    ❌    |
| View Assigned Courses |       ❌       |    ✅    |    ❌    |
| View Course Students  |       ❌       |    ✅    |    ❌    |
| Record Attendance     |       ❌       |    ✅    |    ❌    |
| Update Attendance     |       ❌       |    ✅    |    ❌    |
| Enter Internal Marks  |       ❌       |    ✅    |    ❌    |
| Enter External Marks  |       ❌       |    ✅    |    ❌    |
| View Profile          |       ✅       |    ✅    |    ✅    |
| View Attendance       |       ✅       |    ✅    |    ✅    |
| View Results          |       ✅       |    ✅    |    ✅    |
| Download Reports      |       ✅       |    ❌    |    ❌    |
| View Analytics        |       ✅       |    ❌    |    ❌    |
| View Audit Log        |       ✅       |    ❌    |    ❌    |

---

# 🏗️ System Architecture

The application follows a lightweight server-rendered architecture for the local academic workflow.

```text
┌──────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                          │
│                                                              │
│                        Web Browser                            │
│                                                              │
│       Administrator       Faculty          Student            │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ HTTP
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                        │
│                                                              │
│                           Flask                              │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │ Authentication │  │ Role / Access  │  │ Academic       │ │
│  │                │  │ Control        │  │ Operations     │ │
│  └────────────────┘  └────────────────┘  └────────────────┘ │
│                                                              │
│ Students │ Faculty │ Courses │ Enrollment │ Attendance        │
│ Marks │ Timetable │ Fees │ Reports │ API │ Analytics         │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             │ Database Access
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                          │
│                                                              │
│                 SQLite — Local Demo                          │
│                 PostgreSQL — Deployment                      │
└──────────────────────────────────────────────────────────────┘
```

## Production Architecture

```text
                 ┌────────────────────┐
                 │      Browser       │
                 └─────────┬──────────┘
                           │ HTTPS
                           ▼
                 ┌────────────────────┐
                 │ Production Flask   │
                 │ Application        │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │    PostgreSQL      │
                 │  Production DB     │
                 └────────────────────┘
```

Production launch additionally requires institution-specific configuration and operational review.

---

# 🔄 Academic Workflow

The primary academic workflow is:

```text
                    ADMINISTRATOR
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Students        Faculty        Courses
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                     Enrollment
                         │
                         ▼
                  Assigned Faculty
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
         Attendance               Marks
              │                     │
              └──────────┬──────────┘
                         │
                         ▼
                       Student
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
      Attendance       Results      Timetable
                                       │
                                       ▼
                                   Fee Status
```

## Typical Demonstration Flow

1. Administrator signs in.
2. Administrator adds a student.
3. Administrator enrolls the student in a course.
4. Faculty signs in.
5. Faculty selects an assigned course.
6. Faculty records attendance.
7. Faculty enters internal and external marks.
8. Student signs in.
9. Student views attendance and results.
10. Administrator generates an academic CSV report.

---

# ⚙️ Tech Stack

## Backend

| Technology   | Purpose                                 |
| ------------ | --------------------------------------- |
| Python 3.10+ | Application runtime                     |
| Flask        | Web framework                           |
| SQLite       | Local demonstration database            |
| PostgreSQL   | Production database target              |
| Gunicorn     | Production/development container server |

## Frontend

| Technology      | Purpose                    |
| --------------- | -------------------------- |
| HTML            | Page structure             |
| CSS             | Responsive visual design   |
| Flask Templates | Server-side page rendering |
| Browser         | Application client         |

The visual system follows the project's **navy, teal, and white** design direction.

## Data and Reporting

| Component           | Purpose                        |
| ------------------- | ------------------------------ |
| Relational database | Store academic information     |
| SQLite              | Local persistence              |
| PostgreSQL          | Production database target     |
| CSV                 | Attendance and marks reporting |

---

# 📂 Repository Structure

The current repository is organized to separate application functionality, database tooling, API functionality, documentation, and tests.

```text
Student-information-system/
│
├── app.py
│
├── sis/
│   ├── __init__.py
│   ├── db.py
│   ├── migrations.py
│   ├── api.py
│   ├── admin.py
│   │
│   └── migrations/
│       ├── 002_api_tokens.sql
│       └── 002_api_tokens_postgres.sql
│
├── templates/
│   └── Server-rendered HTML templates
│
├── static/
│   └── CSS and frontend assets
│
├── tests/
│   └── Automated tests
│
├── docs/
│   └── openapi.yaml
│
├── schema.sql
├── schema_postgres.sql
├── migrate_postgres.py
│
├── Dockerfile
├── docker-compose.yml
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── requirements.txt
├── requirements-dev.txt
│
└── README.md
```

> Do not commit the `instance/` directory when it contains personal data, credentials, local databases, or secret keys.

---

# 🗄️ Database Design

The system uses a relational database structure to represent major academic entities and their relationships.

Conceptually:

```text
┌──────────────┐
│   STUDENT    │
└──────┬───────┘
       │
       │ Enrollment
       ▼
┌──────────────┐       ┌──────────────┐
│    COURSE    │◄──────│   FACULTY    │
└──────┬───────┘       └──────────────┘
       │
       ├─────────────────┐
       │                 │
       ▼                 ▼
┌──────────────┐   ┌──────────────┐
│  ATTENDANCE  │   │    MARKS     │
└──────────────┘   └──────────────┘

┌──────────────┐
│  TIMETABLE   │
└──────────────┘

┌──────────────┐
│ FEE STATUS   │
└──────────────┘
```

The relational schema and indexes are defined in:

```text
schema.sql
```

A PostgreSQL-specific schema is provided in:

```text
schema_postgres.sql
```

The local SQLite database is initialized automatically when the application is first run.

---

# 🔄 Database Migrations

Version 2 introduces versioned migration management.

The migration history is maintained in:

```text
schema_migrations
```

The initial schema is treated as:

```text
001_baseline_schema
```

The current migration includes:

```text
002_api_tokens
```

PostgreSQL also has:

```text
002_api_tokens_postgres.sql
```

### Migration principle

Do not modify an already-applied migration.

Instead:

```text
Existing migration
       ↓
Keep unchanged
       ↓
Create new numbered migration
       ↓
Apply migration
```

The application automatically applies pending migrations during startup.

---

# 👤 Authentication and Accounts

The application supports separate accounts for:

* Administrators
* Faculty
* Students

## Account Creation

Student and faculty accounts are created when an administrator adds their corresponding records.

The username follows the institutional ID:

```text
Student ID → lowercase username
Faculty ID  → lowercase username
```

Example:

```text
Student ID:
IT24044

Username:
it24044
```

Passwords are stored as **password hashes**, rather than plaintext passwords.

---

# 📊 Attendance Management

Faculty can record attendance for students belonging to their assigned courses.

Attendance is identified using:

```text
Student
   +
Course
   +
Date
```

This prevents accidental duplicate attendance records.

## Correction Workflow

If an attendance record already exists for:

```text
Student + Course + Date
```

the existing record can be corrected rather than creating another entry.

This allows faculty to fix data-entry mistakes.

---

# 📝 Marks and Results

Faculty can enter academic assessment marks for students in their assigned courses.

The system supports:

* Internal marks
* External marks
* Updating existing assessments

An assessment can therefore be corrected without creating duplicate records.

Students receive a read-only view of their resulting academic information.

---

# 🗓️ Timetable and Fees

## Timetable

Administrators maintain timetable information used by the academic workflow.

Students can view their timetable through their dashboard.

## Fee Status

The system maintains the **status** of fee payments.

Example conceptual states include:

```text
Paid
Pending
```

> The project does **not** connect to a payment gateway or process actual online payments.

It is an academic fee-status management feature rather than a payment platform.

---

# 📑 Reports

Administrators can generate academic reports in CSV format.

The reporting workflow is:

```text
Database
   │
   ▼
Report Preview
   │
   ▼
CSV Generation
   │
   ▼
Download
```

Current reporting areas include:

* Attendance
* Marks

CSV files can be opened using spreadsheet applications such as Microsoft Excel or LibreOffice Calc.

---

# 🌐 REST API

Version 2 introduces a versioned REST API under:

```text
/api/v1
```

API authentication uses **revocable bearer tokens**.

## Create an API Token

```powershell
flask --app app create-api-token
```

The raw token is displayed once.

> Store the token securely. The raw token is not stored by the application.

## Revoke an API Token

```powershell
flask --app app revoke-api-token TOKEN_ID
```

## Example API Request

```powershell
$headers = @{ Authorization = "Bearer YOUR_TOKEN" }

Invoke-RestMethod http://127.0.0.1:5000/api/v1/me -Headers $headers

Invoke-RestMethod http://127.0.0.1:5000/api/v1/courses -Headers $headers
```

## Available Endpoints

```text
GET  /api/v1/me
GET  /api/v1/dashboard
GET  /api/v1/students?q=...
GET  /api/v1/courses
GET  /api/v1/attendance?student_id=...
POST /api/v1/attendance
GET  /api/v1/marks?student_id=...
POST /api/v1/marks
```

Complete API documentation is available in:

```text
docs/openapi.yaml
```

---

# 🧾 API Examples

## Record Attendance

```json
{
  "course_id": "IT24501",
  "class_date": "2026-10-01",
  "entries": [
    {
      "student_id": "IT24018",
      "status": "Present"
    },
    {
      "student_id": "IT24027",
      "status": "Absent"
    }
  ]
}
```

## Record Marks

```json
{
  "course_id": "IT24501",
  "entries": [
    {
      "student_id": "IT24018",
      "internal": 36,
      "external": 54
    }
  ]
}
```

### API Authorization

Faculty tokens are restricted to their assigned courses.

Student API access is read-only and scoped to the student's own records.

Administrators have broader access according to their role.

---

# 🔒 Security Controls

The project includes several security-oriented controls.

| Security Area            | Implementation               |
| ------------------------ | ---------------------------- |
| Password storage         | Werkzeug password hashing    |
| Browser authentication   | Session-based authentication |
| Authorization            | Role-based access control    |
| Browser forms            | CSRF protection              |
| API authentication       | Bearer tokens                |
| API token storage        | SHA-256 hashes               |
| Token management         | Token revocation             |
| Login protection         | Login attempt throttling     |
| Password changes         | Session version invalidation |
| SQL security             | Parameterized SQL            |
| Database integrity       | Foreign keys and constraints |
| HTTP security            | Security response headers    |
| Production transport     | HTTPS/HSTS expectations      |
| Accountability           | Audit logging                |
| Production configuration | Fail-closed validation       |

### API Token Security

Raw API tokens are not stored.

The flow is:

```text
Client
  │
  │ Raw token
  ▼
Application
  │
  │ SHA-256
  ▼
Stored token hash
```

Tokens can also be revoked without deleting the complete API authentication system.

---

# 📈 Admin Analytics and Audit Log

Version 2 introduces administrator-specific operational views.

## Analytics

Available at:

```text
/admin/analytics
```

Analytics includes:

* Number of students
* Number of faculty
* Number of courses
* Number of enrollments
* Attendance entries
* Marks entries
* Pending fees
* Attendance distribution
* Fee status distribution

## Audit Log

Available at:

```text
/admin/audit
```

The audit log shows the latest recorded events with information such as:

* Actor
* Action
* Object type
* Object ID
* Timestamp

This provides additional accountability for important academic changes.

---

# 🔧 Environment and Configuration

## Local Demonstration

The local application uses:

```text
Flask
  +
SQLite
```

The database is stored at:

```text
instance/sis.sqlite3
```

A local secret is generated separately in:

```text
instance/secret.key
```

These files should remain private when they contain credentials, secrets, or personal data.

---

# 🚀 Local Development

## Prerequisites

| Requirement      | Version / Requirement            |
| ---------------- | -------------------------------- |
| Python           | 3.10 or newer                    |
| Browser          | Any modern browser               |
| Internet         | Required to install dependencies |
| Operating System | Windows, macOS, or Linux         |

---

## Windows PowerShell

Open PowerShell in the project directory containing:

```text
app.py
requirements.txt
```

### 1. Create a virtual environment

```powershell
py -3.12 -m venv .venv
```

### 2. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Run the application

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

> Do **not** type the PowerShell prompt itself.

Correct:

```powershell
python app.py
```

Not:

```text
PS C:\...\Student-information-system> python app.py
```

---

## macOS / Linux

From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

# 🧪 First Run

On the first local run:

1. Flask starts the application.
2. The SQLite database is initialized.
3. Required database structures are created.
4. The migration baseline is recorded.
5. Pending migrations are applied.
6. Demo data is seeded when the database is empty.
7. The application becomes available through the local browser.

The local database is stored at:

```text
instance/sis.sqlite3
```

---

# 🔑 Demo Accounts

The application includes local demonstration accounts.

| Role          | Username  | Password     |
| ------------- | --------- | ------------ |
| Administrator | `admin`   | `admin123`   |
| Faculty       | `faculty` | `faculty123` |
| Student       | `student` | `student123` |

> ⚠️ These credentials are intended **only for local academic demonstration**.

Before using the application on a shared server, seeded credentials should be changed or removed.

For creating an administrator account:

```powershell
flask --app app create-admin
```

---

# 🎬 Suggested Live Demonstration

A complete demonstration can be performed using the following sequence.

## 1. Administrator

Sign in using:

```text
Username: admin
Password: admin123
```

Demonstrate:

* Add a student
* Enroll the student in a course
* Review academic records
* Maintain timetable information
* Maintain fee status
* Access reporting
* View analytics
* View audit logs

---

## 2. Faculty

Sign out and sign in as Faculty.

Demonstrate:

* Open an assigned course
* View enrolled students
* Select an attendance date
* Record attendance
* Correct an attendance entry
* Enter internal marks
* Enter external marks
* Update assessment information

---

## 3. Student

Sign out and sign in as Student.

Demonstrate:

* Student profile
* Enrolled courses
* Attendance
* Results
* Timetable
* Fee status

---

## 4. Administrator Reports

Return to Administrator and demonstrate:

```text
Attendance Report
        ↓
Preview
        ↓
CSV Download
```

and/or:

```text
Marks Report
        ↓
Preview
        ↓
CSV Download
```

---

# 👥 Sample Academic Data

The built-in sample student account belongs to:

```text
IT24044
```

The sample faculty account belongs to:

```text
FAC101
```

with assigned academic areas including:

```text
Computer Networks
Operating Systems
```

To demonstrate an account created through the administrator workflow:

```text
Student ID
    ↓
Lowercase username
    ↓
Password entered during creation
```

---

# 🧪 Testing

The project includes automated tests.

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

## Compile Check

Run:

```powershell
python -m compileall -q app.py sis tests
```

## Optional Development Linting

Install development dependencies:

```powershell
pip install -r requirements-dev.txt
```

Then run:

```powershell
ruff check app.py sis tests
```

## Continuous Integration

GitHub Actions automatically performs project checks on pushes and pull requests.

The CI workflow covers:

* Automated tests
* Python syntax/compile checks
* Linting

---

# Docker local demo

The included Compose configuration runs the local demo with SQLite and Gunicorn, and binds to loopback (`127.0.0.1`) only.

```powershell
docker compose up --build
```

Open `http://127.0.0.1:8000`. The local demo uses seeded demo accounts and synthetic records. Do not expose this configuration to the public internet or use it with real student data.

Production requires a separately provisioned PostgreSQL database, a secret manager, institution-approved policy files, a verified HTTPS domain, and a manually provisioned administrator. Follow `DEPLOYMENT.md` and `SECURITY.md`; the local Compose configuration is not a production deployment.

---

# 🗄️ PostgreSQL Deployment

Production mode requires PostgreSQL and refuses to start when required operational configuration is missing.

The production database configuration uses:

```text
SIS_ENV=production
DATABASE_URL=postgresql://...
```

A PostgreSQL migration can be executed explicitly using:

```powershell
$env:SIS_ENV="production"
$env:DATABASE_URL="postgresql://user:password@host:5432/sis"
python migrate_postgres.py
```

---

# ⚙️ Production Configuration

Production requires institution-specific configuration.

Required configuration includes:

```text
SIS_ENV=production
DATABASE_URL=postgresql://...
SIS_SECRET_KEY=<32+ character secret>
SIS_ALLOWED_HOSTS=example.edu
SIS_ORG_NAME=Institution name
SIS_CONTACT_EMAIL=admin@example.edu
SIS_LEGAL_ENTITY=Institution legal entity
SIS_POLICY_EFFECTIVE_DATE=YYYY-MM-DD
SIS_CUSTOM_DOMAIN_VERIFIED=yes
SIS_POLICIES_APPROVED=yes
SIS_PRIVACY_FILE=/path/to/privacy-policy.txt
SIS_TERMS_FILE=/path/to/terms.txt
```

> **Never commit real secrets, production credentials, or institution policy files to Git.**

The production configuration intentionally fails closed when required launch settings are missing.

---

# ⚠️ Production Boundary

A successful local SQLite run does **not** mean the system is ready for institutional deployment.

Before real deployment, the following areas must be added, configured, tested, or reviewed:

* Managed PostgreSQL
* Tested database backups
* Database restore testing
* HTTPS
* Certificate management
* Secret management
* Institution-approved Privacy Policy
* Institution-approved Terms
* Email/password recovery workflow
* MFA or institutional SSO
* Monitoring and alerting
* Structured application logging
* Vulnerability scanning
* Load and concurrency testing
* Data retention and deletion procedures
* Institutional security review
* Production account management

The application should therefore be described as an **academic and portfolio implementation with a production-oriented architecture**, rather than as a ready-to-run institutional SIS.

---

# 🛡️ Project Boundaries

The project intentionally has a defined scope.

## Fee Management

The fee module records payment **status**.

It does not:

* Process online payments
* Connect to a payment gateway
* Store payment card information

---

## Database

The local demonstration uses:

```text
SQLite
```

The production configuration targets:

```text
PostgreSQL
```

PostgreSQL is intended for deployments requiring a stronger multi-user database environment.

---

## Deployment

The application is primarily structured as an academic Software Engineering mini project.

A live institutional deployment additionally requires:

* Production hosting
* HTTPS
* Database backups
* Account recovery
* Administrative password management
* Institutional policies
* Operational review
* Security review
* Monitoring

---

## Data

The demonstration data is fictional.

The local database can be reset by stopping the application and deleting:

```text
instance/sis.sqlite3
```

The application will initialize the database again on the next run.

---

# 🎓 Experiment Alignment

The Student Information System connects the Software Engineering experiments into one functioning application.

| Experiment Area | SIS Implementation                                       |
| --------------- | -------------------------------------------------------- |
| Experiments 1–3 | Requirements, roles, and system functionality            |
| Experiments 6–9 | Use cases, entities, and system modelling                |
| Experiment 10   | Figma-based interface implemented as functioning screens |
| Database Design | Relational schema and indexes                            |
| Implementation  | Flask-based role-specific application                    |
| Testing         | Integration and automated tests                          |
| Reporting       | CSV preview and download                                 |
| Security        | Authentication, authorization, CSRF, API tokens          |
| Deployment      | SQLite local environment and PostgreSQL target           |
| API             | Versioned `/api/v1` REST API                             |

The project connects:

```text
Requirements
      ↓
Use Cases
      ↓
Entities / Data Model
      ↓
UI Prototype
      ↓
Working Application
      ↓
Database
      ↓
Testing
      ↓
Deployment Configuration
```

This makes the application suitable as a **Software Engineering mini project submission and portfolio project**.

---

# 🧩 Design Principles

## 1. Role Separation

Each role receives only the workflows relevant to its responsibilities.

## 2. Centralized Academic Data

Students, faculty, courses, enrollments, attendance, marks, timetable information, and fee statuses are managed through a common relational system.

## 3. Correctable Academic Records

Attendance and assessment records can be updated rather than duplicated.

## 4. Local-First Demonstration

SQLite makes the project straightforward to run during demonstrations without requiring a separately hosted database.

## 5. Production Separation

The production PostgreSQL configuration is kept distinct from the local demonstration environment.

## 6. Versioned Database Evolution

Database changes are handled through numbered migrations rather than manually rebuilding the database schema.

## 7. API-Based Integration

The `/api/v1` interface provides a controlled integration layer for clients and academic operations.

## 8. Auditable Academic Changes

Important academic operations can be recorded in the administrator audit log.

---

# 🔮 Future Improvements

Potential extensions for a larger institutional deployment include:

* Password reset and account recovery
* Email notifications
* Student profile document management
* Advanced attendance analytics
* Grade calculation
* GPA/CGPA processing
* Faculty timetable view
* Student notifications
* Expanded administrative dashboards
* Database backup and restore tooling
* More comprehensive automated testing
* Production monitoring and logging
* MFA or institutional SSO
* Institution-wide deployment

These are **future improvements** and should not be interpreted as currently implemented features unless they are explicitly listed in the implemented feature sections above.

---

# 🔄 Git Workflow

A typical development workflow is:

```text
Create / modify feature
        ↓
Run application locally
        ↓
Run automated tests
        ↓
Run compile check
        ↓
Run linting
        ↓
Review changes
        ↓
Git commit
        ↓
Push to GitHub
        ↓
GitHub Actions CI
        ↓
Review / merge
```

Before committing, check that sensitive files are not included:

```text
instance/
.env
production credentials
database files containing personal data
secret keys
```

---

# 🧹 Resetting the Local Environment

To reset the local demonstration database:

1. Stop Flask.
2. Delete:

```text
instance/sis.sqlite3
```

3. Restart:

```powershell
python app.py
```

The application will initialize the database again and seed the demonstration data when appropriate.

---

# 📌 Important Notes

### Local Demo

Recommended command:

```powershell
python app.py
```

Application URL:

```text
http://127.0.0.1:5000/
```

### Production

Before attempting deployment, review:

```text
DEPLOYMENT.md
```

### Credentials

Never use the demonstration passwords on a real institutional server.

### Sensitive Files

Do not push an `instance/` directory containing:

* Personal data
* Credentials
* Database files
* Secret keys

### API

Store API tokens securely and revoke them when they are no longer required.

---

# 📜 License

This project is intended as an academic Software Engineering mini project.

Add an explicit license file to the repository if the project is intended to be distributed or reused outside the academic submission.

---

<div align="center">

# 🎓 Student Information System

*Connecting students, faculty, courses, and academic workflows in one system.*

**Flask · SQLite · PostgreSQL · REST API · HTML · CSS · Docker · CI**

</div>


## portal and secure workflows

The authenticated `/portal` route serves the responsive CampusOS workspace. It reads role-scoped data from the versioned `/api/v1` API and includes an overview, searchable student/course/attendance/results/fees/timetable tables, session-aware sign-out, and account settings. The portal assets are served locally without a frontend build step or third-party runtime CDN.

### Run with Docker (local demo)

```bash
docker compose up --build
```

Open `http://127.0.0.1:8000`. Local demo credentials are `admin / admin123`, `faculty / faculty123`, and `student / student123`. These credentials and the seeded records are for local demonstration only. Never deploy them to a shared server. The Compose file binds to loopback by default.

### Run directly on Windows PowerShell

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SIS_ENV = "demo"
python -m flask --app app run --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Sign in with a demo account above; successful sign-in opens `/portal`.

### Production provisioning

Production must use PostgreSQL and institution-approved legal policy documents. Configure the required variables in `.env.production.example` through your deployment secret manager, complete domain verification and policy approval, and then provision the first administrator with `flask --app app create-admin`. See [SECURITY.md](SECURITY.md) and [DEPLOYMENT.md](DEPLOYMENT.md). The supplied Compose configuration is for local demo use only.
