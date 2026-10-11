"""Student Information System: Flask + SQLite, role-enforced academic workflows."""
import csv
import io
import os
import hashlib
import secrets
import sqlite3
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import click
from flask import Flask, Response, abort, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from psycopg import IntegrityError as PGIntegrityError
except ImportError:
    PGIntegrityError = sqlite3.IntegrityError

BASE = Path(__file__).resolve().parent


from sis.db import Database
from sis.migrations import apply_migrations
from sis.api import api as api_blueprint
from sis.admin import admin as admin_blueprint


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    production = os.getenv('SIS_ENV', 'demo').lower() == 'production'
    if production:
        required = ('SIS_SECRET_KEY', 'DATABASE_URL', 'SIS_ALLOWED_HOSTS', 'SIS_ORG_NAME', 'SIS_CONTACT_EMAIL', 'SIS_LEGAL_ENTITY', 'SIS_POLICY_EFFECTIVE_DATE', 'SIS_CUSTOM_DOMAIN_VERIFIED', 'SIS_PRIVACY_FILE', 'SIS_TERMS_FILE', 'SIS_POLICIES_APPROVED')
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError('Production configuration is incomplete: ' + ', '.join(missing))
        if os.environ['SIS_CUSTOM_DOMAIN_VERIFIED'] != 'yes':
            raise RuntimeError('Custom domain verification must be completed before production mode.')
        if os.environ['SIS_POLICIES_APPROVED'] != 'yes':
            raise RuntimeError('Institution-approved Privacy Policy and Terms are required before production mode.')
        legal_texts = []
        for key in ('SIS_PRIVACY_FILE', 'SIS_TERMS_FILE'):
            path = Path(os.environ[key])
            if not path.is_file() or len(path.read_text(encoding='utf-8').strip()) < 200:
                raise RuntimeError(key + ' must point to a completed policy document.')
            legal_texts.append(path.read_text(encoding='utf-8').strip())
        if not os.environ['DATABASE_URL'].startswith(('postgres://', 'postgresql://')):
            raise RuntimeError('Production mode requires PostgreSQL.')
        if len(os.environ['SIS_SECRET_KEY']) < 32:
            raise RuntimeError('SIS_SECRET_KEY must contain at least 32 characters.')
        secret = os.environ['SIS_SECRET_KEY']
    else:
        secret_file = Path(app.instance_path) / 'secret.key'
        if not secret_file.exists():
            secret_file.write_text(secrets.token_hex(32), encoding='utf-8')
            try:
                secret_file.chmod(0o600)
            except OSError:
                pass
        secret = secret_file.read_text().strip()
        legal_texts = ('Draft policy. The institution must provide and approve its actual data-use, retention, contact and rights information before launch.', 'Draft terms. The institution must define permitted use, account responsibilities and support procedures before launch.')
    app.config.update(SECRET_KEY=secret, DATABASE=str(Path(app.instance_path) / 'sis.sqlite3'), DATABASE_URL=os.getenv('DATABASE_URL') if production else None, PRODUCTION=production, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=production, PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=64*1024, TRUSTED_HOSTS=[h.strip() for h in os.getenv('SIS_ALLOWED_HOSTS','localhost,127.0.0.1').split(',')] if production else None, ORG_NAME=os.getenv('SIS_ORG_NAME','Student Information System'), CONTACT_EMAIL=os.getenv('SIS_CONTACT_EMAIL',''), LEGAL_ENTITY=os.getenv('SIS_LEGAL_ENTITY',''), POLICY_EFFECTIVE_DATE=os.getenv('SIS_POLICY_EFFECTIVE_DATE',''), PRIVACY_TEXT=legal_texts[0], TERMS_TEXT=legal_texts[1])
    if test_config:
        app.config.update(test_config)

    app.register_blueprint(api_blueprint)
    app.register_blueprint(admin_blueprint)

    def db():
        if 'db' not in g:
            if app.config['DATABASE_URL']:
                import psycopg
                from psycopg.rows import dict_row
                g.db = Database(psycopg.connect(app.config['DATABASE_URL'], row_factory=dict_row), postgres=True)
            else:
                conn = sqlite3.connect(app.config['DATABASE'])
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA foreign_keys = ON')
                conn.execute('PRAGMA busy_timeout = 5000')
                g.db = Database(conn)
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        connection = g.pop('db', None)
        if connection is not None:
            connection.close()

    @app.before_request
    def load_user():
        if session.get('user_id'):
            g.user = db().execute('SELECT * FROM users WHERE id=?', (session.get('user_id'),)).fetchone()
        else:
            g.user = None
            if request.path.startswith('/api/') and request.headers.get('Authorization', '').startswith('Bearer '):
                db()  # Bearer-token authentication needs a database connection without a browser session.
        if g.user and session.get('session_version') != g.user['session_version']:
            session.clear()
            g.user = None
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        is_bearer_api = request.path.startswith('/api/') and request.headers.get('Authorization', '').startswith('Bearer ')
        if request.method == 'POST' and not is_bearer_api:
            submitted_csrf = request.form.get('csrf', '') or request.headers.get('X-CSRF-Token', '')
            if not secrets.compare_digest(session['csrf'], submitted_csrf):
                abort(400, description='Invalid form token. Reload the page and try again.')

    @app.after_request
    def security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
        response.headers['Cache-Control'] = 'no-store' if g.get('user') else 'private, no-cache'
        if app.config['PRODUCTION']:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    @app.context_processor
    def helpers():
        return {'csrf': lambda: session.get('csrf', ''), 'today': date.today().isoformat(), 'org_name': app.config['ORG_NAME']}

    def rows(sql, params=()):
        return db().execute(sql, params).fetchall()

    def one(sql, params=()):
        return db().execute(sql, params).fetchone()

    def gate(*roles):
        def decorate(fn):
            @wraps(fn)
            def inner(*args, **kwargs):
                if not g.user:
                    return redirect(url_for('login'))
                if roles and g.user['role'] not in roles:
                    abort(403)
                return fn(*args, **kwargs)
            return inner
        return decorate

    def owned_course(course_id):
        course = one('SELECT * FROM courses WHERE id=?', (course_id,))
        if not course or (g.user['role'] == 'faculty' and course['faculty_id'] != g.user['linked_id']):
            abort(403)
        return course

    def safe_int(value, minimum, maximum):
        try:
            n = int(value)
            if minimum <= n <= maximum:
                return n
        except (TypeError, ValueError):
            pass
        raise ValueError(f'Enter a number between {minimum} and {maximum}.')

    def audit(action, object_type, object_id):
        db().execute('INSERT INTO audit_log(actor_id,action,object_type,object_id) VALUES(?,?,?,?)',(g.user['id'],action,object_type,str(object_id)))

    def initialize():
        if app.config['DATABASE_URL']:
            schema = (BASE / 'schema_postgres.sql').read_text(encoding='utf-8')
            statements = [part.strip() for part in schema.split(';') if part.strip()]
            with db():
                for statement in statements:
                    db().execute(statement)
                apply_migrations(db(), postgres=True)
            one('SELECT id FROM users LIMIT 1')
            return
        db().executescript((BASE / 'schema.sql').read_text(encoding='utf-8'))
        apply_migrations(db(), postgres=False)
        if 'session_version' not in [col['name'] for col in db().execute('PRAGMA table_info(users)').fetchall()]:
            db().execute('ALTER TABLE users ADD COLUMN session_version INTEGER NOT NULL DEFAULT 0')
        if one('SELECT id FROM users LIMIT 1'):
            db().commit()
            return
        db().executemany('INSERT INTO faculty VALUES(?,?,?,?)', [('FAC101', 'Faculty Demo One', 'Information Technology', 'faculty.one@example.test'), ('FAC102', 'Faculty Demo Two', 'Information Technology', 'faculty.two@example.test')])
        db().executemany('INSERT INTO students VALUES(?,?,?,?,?,?)', [('IT24018','Demo Student One','Information Technology',4,'student.one@example.test','9000000001'),('IT24027','Demo Student Two','Information Technology',4,'student.two@example.test','9000000002'),('IT24044','Demo Student Three','Information Technology',4,'student.three@example.test','9000000003'),('CS24006','Demo Student Four','Computer Science',4,'student.four@example.test','9000000004')])
        db().executemany('INSERT INTO courses VALUES(?,?,?,?,?)', [('IT24501','Computer Networks','Information Technology',4,'FAC101'),('IT24502','Database Systems','Information Technology',4,'FAC102'),('IT24503','Operating Systems','Information Technology',4,'FAC101')])
        db().executemany('INSERT INTO enrollments VALUES(?,?)', [(sid,cid) for sid in ['IT24018','IT24027','IT24044'] for cid in ['IT24501','IT24502','IT24503']])
        db().executemany('INSERT INTO fees(student_id,semester,amount,due_date,status) VALUES(?,?,?,?,?)', [(sid,4,45000,'2026-09-15',status) for sid,status in [('IT24018','Paid'),('IT24027','Pending'),('IT24044','Paid')]])
        db().executemany('INSERT INTO timetable(course_id,day,start_time,end_time,room) VALUES(?,?,?,?,?)', [('IT24501','Monday','09:00','10:00','A21'),('IT24502','Monday','11:00','12:00','B14'),('IT24503','Tuesday','10:00','11:00','A21')])
        demo_users=[('admin','admin123','admin',None),('faculty','faculty123','faculty','FAC101'),('student','student123','student','IT24044')]
        db().executemany('INSERT INTO users(username,password_hash,role,linked_id) VALUES(?,?,?,?)', [(u,generate_password_hash(p),role,linked) for u,p,role,linked in demo_users])
        db().commit()

    with app.app_context():
        initialize()

    @app.route('/')
    def index():
        return redirect(url_for('dashboard') if g.user else url_for('login'))

    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'POST':
            username=request.form.get('username','').strip().lower()
            source_hash=hashlib.sha256((request.remote_addr or 'unknown').encode()).hexdigest()
            window_dt=datetime.now(timezone.utc)-timedelta(minutes=15)
            window=window_dt if app.config['DATABASE_URL'] else window_dt.strftime('%Y-%m-%d %H:%M:%S')
            attempts=one('SELECT COUNT(*) n FROM login_attempts WHERE username=? AND source_hash=? AND attempted_at>?',(username,source_hash,window))['n']
            source_attempts=one('SELECT COUNT(*) n FROM login_attempts WHERE source_hash=? AND attempted_at>?',(source_hash,window))['n']
            if attempts >= 5 or source_attempts >= 20:
                flash('Too many attempts. Try again later.','error')
                return render_template('login.html'),429
            user=one('SELECT * FROM users WHERE username=?', (username,))
            if user and check_password_hash(user['password_hash'],request.form.get('password','')):
                with db():db().execute('DELETE FROM login_attempts WHERE username=? AND source_hash=?',(username,source_hash))
                session.clear()
                session['user_id']=user['id']
                session['session_version']=user['session_version']
                session['csrf']=secrets.token_urlsafe(32)
                session.permanent=True
                return redirect(url_for('portal'))
            with db():
                old_dt=datetime.now(timezone.utc)-timedelta(days=1)
                old=old_dt if app.config['DATABASE_URL'] else old_dt.strftime('%Y-%m-%d %H:%M:%S')
                db().execute('DELETE FROM login_attempts WHERE attempted_at<?',(old,))
                db().execute('INSERT INTO login_attempts(username,source_hash) VALUES(?,?)',(username,source_hash))
            flash('Invalid username or password.', 'error')
        return render_template('login.html')

    @app.post('/logout')
    @gate()
    def logout():
        session.clear()
        return redirect(url_for('login'))

    @app.route('/account/password', methods=['GET', 'POST'])
    @gate()
    def change_password():
        if request.method == 'POST':
            current = request.form.get('current_password','')
            new = request.form.get('new_password','')
            if not check_password_hash(g.user['password_hash'], current):
                flash('Current password is incorrect.','error')
            elif len(new) < 12:
                flash('Use a new password of at least 12 characters.','error')
            elif new == current:
                flash('Choose a different password.','error')
            else:
                with db():db().execute('UPDATE users SET password_hash=?,session_version=session_version+1 WHERE id=?',(generate_password_hash(new),g.user['id']))
                session.clear()
                flash('Password changed. Sign in again.','success')
                return redirect(url_for('login'))
        return render_template('password.html')

    @app.get('/privacy')
    def privacy():return render_template('legal.html',kind='privacy',content=app.config['PRIVACY_TEXT'])

    @app.get('/terms')
    def terms():return render_template('legal.html',kind='terms',content=app.config['TERMS_TEXT'])

    @app.get('/health')
    def health():
        try:one('SELECT id FROM users LIMIT 1')
        except Exception:
            return {'status':'unavailable'},503
        return {'status':'ok'}

    @app.get('/portal')
    @gate()
    def portal():
        portal_index = BASE / 'static' / 'portal' / 'index.html'
        if not portal_index.is_file():
            return redirect(url_for('dashboard'))
        from flask import send_file
        return send_file(portal_index)

    @app.route('/dashboard')
    @gate()
    def dashboard():
        role=g.user['role']
        if role=='admin':
            metrics=[('Students',one('SELECT COUNT(*) n FROM students')['n']),('Faculty',one('SELECT COUNT(*) n FROM faculty')['n']),('Courses',one('SELECT COUNT(*) n FROM courses')['n']),('Pending fees',one("SELECT COUNT(*) n FROM fees WHERE status!='Paid'")['n'])]
        elif role=='faculty':
            metrics=[('My courses',one('SELECT COUNT(*) n FROM courses WHERE faculty_id=?',(g.user['linked_id'],))['n']),('My students',one('SELECT COUNT(DISTINCT student_id) n FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE c.faculty_id=?',(g.user['linked_id'],))['n']),('Attendance entries',one('SELECT COUNT(*) n FROM attendance a JOIN courses c ON c.id=a.course_id WHERE c.faculty_id=?',(g.user['linked_id'],))['n'])]
        else:
            sid=g.user['linked_id'];metrics=[('My courses',one('SELECT COUNT(*) n FROM enrollments WHERE student_id=?',(sid,))['n']),('Attendance entries',one('SELECT COUNT(*) n FROM attendance WHERE student_id=?',(sid,))['n']),('Results published',one('SELECT COUNT(*) n FROM marks WHERE student_id=?',(sid,))['n']),('Pending fees',one("SELECT COUNT(*) n FROM fees WHERE student_id=? AND status!='Paid'",(sid,))['n'])]
        return render_template('dashboard.html',metrics=metrics)

    @app.route('/students')
    @gate('admin','faculty')
    def students():
        q=request.args.get('q','').strip()
        if g.user['role']=='faculty':
            sql='SELECT DISTINCT s.* FROM students s JOIN enrollments e ON e.student_id=s.id JOIN courses c ON c.id=e.course_id WHERE c.faculty_id=? AND (s.name LIKE ? OR s.id LIKE ?) ORDER BY s.name';params=(g.user['linked_id'],f'%{q}%',f'%{q}%')
        else:
            sql='SELECT * FROM students WHERE name LIKE ? OR id LIKE ? ORDER BY name';params=(f'%{q}%',f'%{q}%')
        return render_template('list.html',kind='students',items=rows(sql,params),search=q)

    @app.route('/students/new',methods=['GET','POST'])
    @app.route('/students/<student_id>/edit',methods=['GET','POST'])
    @gate('admin')
    def student_form(student_id=None):
        item=one('SELECT * FROM students WHERE id=?',(student_id,)) if student_id else None
        if student_id and not item:abort(404)
        if request.method=='POST':
            f=request.form
            try:
                values=(f['id'].strip().upper(),f['name'].strip(),f['department'].strip(),safe_int(f.get('semester'),1,12),f['email'].strip(),f.get('phone','').strip())
                if not all(values[:3]) or not values[4]:raise ValueError('Complete all required fields.')
                with db():
                    if item:
                        if values[0]!=student_id:raise ValueError('Student ID cannot be changed after creation.')
                        db().execute('UPDATE students SET name=?,department=?,semester=?,email=?,phone=? WHERE id=?',values[1:]+(student_id,))
                    else:db().execute('INSERT INTO students VALUES(?,?,?,?,?,?)',values)
                    audit('update' if item else 'create','student',values[0])
                    if not item:
                        password=f.get('initial_password','')
                        if len(password)<(12 if app.config['PRODUCTION'] else 8):raise ValueError('An initial password of at least 12 characters is required in production.')
                        db().execute('INSERT INTO users(username,password_hash,role,linked_id) VALUES(?,?,?,?)',(values[0].lower(),generate_password_hash(password),'student',values[0]))
                flash('Student record saved.','success');return redirect(url_for('students'))
            except (ValueError,sqlite3.IntegrityError,PGIntegrityError) as exc:flash(str(exc),'error')
        return render_template('form.html',kind='student',item=item)

    @app.post('/students/<student_id>/delete')
    @gate('admin')
    def delete_student(student_id):
        with db():
            db().execute("DELETE FROM users WHERE role='student' AND linked_id=?",(student_id,))
            db().execute('DELETE FROM students WHERE id=?',(student_id,))
            audit('delete','student',student_id)
        flash('Student deleted.','success');return redirect(url_for('students'))

    @app.route('/faculty')
    @gate('admin')
    def faculty():return render_template('list.html',kind='faculty',items=rows('SELECT * FROM faculty ORDER BY name'),search='')

    @app.route('/faculty/new',methods=['GET','POST'])
    @app.route('/faculty/<faculty_id>/edit',methods=['GET','POST'])
    @gate('admin')
    def faculty_form(faculty_id=None):
        item=one('SELECT * FROM faculty WHERE id=?',(faculty_id,)) if faculty_id else None
        if faculty_id and not item:abort(404)
        if request.method=='POST':
            f=request.form;values=(f['id'].strip().upper(),f['name'].strip(),f['department'].strip(),f['email'].strip())
            try:
                if not all(values):raise ValueError('Complete all fields.')
                with db():
                    if item:
                        if values[0]!=faculty_id:raise ValueError('Faculty ID cannot be changed after creation.')
                        db().execute('UPDATE faculty SET name=?,department=?,email=? WHERE id=?',values[1:]+(faculty_id,))
                    else:db().execute('INSERT INTO faculty VALUES(?,?,?,?)',values)
                    audit('update' if item else 'create','faculty',values[0])
                    if not item:
                        password=f.get('initial_password','')
                        if len(password)<(12 if app.config['PRODUCTION'] else 8):raise ValueError('An initial password of at least 12 characters is required in production.')
                        db().execute('INSERT INTO users(username,password_hash,role,linked_id) VALUES(?,?,?,?)',(values[0].lower(),generate_password_hash(password),'faculty',values[0]))
                flash('Faculty saved.','success');return redirect(url_for('faculty'))
            except (ValueError,sqlite3.IntegrityError,PGIntegrityError) as exc:flash(str(exc),'error')
        return render_template('form.html',kind='faculty',item=item)

    @app.post('/faculty/<faculty_id>/delete')
    @gate('admin')
    def delete_faculty(faculty_id):
        with db():
            db().execute("DELETE FROM users WHERE role='faculty' AND linked_id=?",(faculty_id,))
            db().execute('DELETE FROM faculty WHERE id=?',(faculty_id,))
            audit('delete','faculty',faculty_id)
        flash('Faculty deleted.','success');return redirect(url_for('faculty'))

    @app.route('/courses')
    @gate()
    def courses():
        sql='SELECT c.*,f.name faculty_name FROM courses c LEFT JOIN faculty f ON f.id=c.faculty_id'
        if g.user['role']=='faculty':sql+=' WHERE c.faculty_id=?';params=(g.user['linked_id'],)
        elif g.user['role']=='student':sql+=' JOIN enrollments e ON e.course_id=c.id WHERE e.student_id=?';params=(g.user['linked_id'],)
        else:params=()
        return render_template('list.html',kind='courses',items=rows(sql+' ORDER BY c.name',params),search='')

    @app.route('/courses/new',methods=['GET','POST'])
    @app.route('/courses/<course_id>/edit',methods=['GET','POST'])
    @gate('admin')
    def course_form(course_id=None):
        item=one('SELECT * FROM courses WHERE id=?',(course_id,)) if course_id else None
        if course_id and not item:abort(404)
        if request.method=='POST':
            f=request.form
            try:
                values=(f['id'].strip().upper(),f['name'].strip(),f['department'].strip(),safe_int(f.get('semester'),1,12),f.get('faculty_id') or None)
                if not all(values[:3]):raise ValueError('Complete all required fields.')
                with db():
                    if item:
                        if values[0]!=course_id:raise ValueError('Course ID cannot be changed after creation.')
                        db().execute('UPDATE courses SET name=?,department=?,semester=?,faculty_id=? WHERE id=?',values[1:]+(course_id,))
                    else:db().execute('INSERT INTO courses VALUES(?,?,?,?,?)',values)
                    audit('update' if item else 'create','course',values[0])
                flash('Course saved.','success');return redirect(url_for('courses'))
            except (ValueError,sqlite3.IntegrityError,PGIntegrityError) as exc:flash(str(exc),'error')
        return render_template('form.html',kind='course',item=item,faculty=rows('SELECT * FROM faculty ORDER BY name'))

    @app.post('/courses/<course_id>/delete')
    @gate('admin')
    def delete_course(course_id):
        with db():
            db().execute('DELETE FROM courses WHERE id=?',(course_id,))
            audit('delete','course',course_id)
        flash('Course deleted.','success');return redirect(url_for('courses'))

    @app.route('/enrollments',methods=['GET','POST'])
    @gate('admin')
    def enrollments():
        if request.method=='POST':
            try:
                with db():
                    db().execute('INSERT INTO enrollments VALUES(?,?)',(request.form['student_id'],request.form['course_id']))
                    audit('create','enrollment',request.form['student_id']+':'+request.form['course_id'])
                flash('Student enrolled.','success')
            except (sqlite3.IntegrityError,PGIntegrityError):flash('Enrollment already exists or IDs are invalid.','error')
            return redirect(url_for('enrollments'))
        return render_template('enrollments.html',items=rows('SELECT e.*,s.name student_name,c.name course_name FROM enrollments e JOIN students s ON s.id=e.student_id JOIN courses c ON c.id=e.course_id ORDER BY s.name'),students=rows('SELECT * FROM students ORDER BY name'),courses=rows('SELECT * FROM courses ORDER BY name'))

    @app.post('/enrollments/remove')
    @gate('admin')
    def remove_enrollment():
        with db():
            db().execute('DELETE FROM enrollments WHERE student_id=? AND course_id=?',(request.form['student_id'],request.form['course_id']))
            audit('delete','enrollment',request.form['student_id']+':'+request.form['course_id'])
        flash('Enrollment removed.','success');return redirect(url_for('enrollments'))

    @app.route('/attendance',methods=['GET','POST'])
    @gate()
    def attendance():
        if g.user['role']=='student':
            if request.method=='POST':abort(403)
            records=rows("SELECT c.name,COUNT(a.class_date) total,SUM(CASE WHEN a.status='Present' THEN 1 ELSE 0 END) present FROM enrollments e JOIN courses c ON c.id=e.course_id LEFT JOIN attendance a ON a.student_id=e.student_id AND a.course_id=e.course_id WHERE e.student_id=? GROUP BY c.id ORDER BY c.name",(g.user['linked_id'],))
            return render_template('attendance.html',records=records,student_view=True)
        courses_list=rows('SELECT * FROM courses WHERE faculty_id=? ORDER BY name',(g.user['linked_id'],)) if g.user['role']=='faculty' else rows('SELECT * FROM courses ORDER BY name')
        cid=request.values.get('course_id') or (courses_list[0]['id'] if courses_list else '')
        class_date=request.values.get('class_date') or date.today().isoformat()
        if cid:owned_course(cid)
        roster=rows('SELECT s.*,a.status FROM enrollments e JOIN students s ON s.id=e.student_id LEFT JOIN attendance a ON a.student_id=s.id AND a.course_id=e.course_id AND a.class_date=? WHERE e.course_id=? ORDER BY s.name',(class_date,cid)) if cid else []
        if request.method=='POST':
            try:date.fromisoformat(class_date)
            except ValueError:abort(400)
            if not roster:flash('No enrolled students for this course.','error')
            elif any(request.form.get('status_'+s['id']) not in ('Present','Absent') for s in roster):flash('Mark every student.','error')
            else:
                with db():
                    db().executemany('INSERT INTO attendance(student_id,course_id,class_date,status) VALUES(?,?,?,?) ON CONFLICT(student_id,course_id,class_date) DO UPDATE SET status=excluded.status',[(s['id'],cid,class_date,request.form['status_'+s['id']]) for s in roster])
                    audit('record','attendance',cid+':'+class_date)
                flash('Attendance saved.','success')
            return redirect(url_for('attendance',course_id=cid,class_date=class_date))
        return render_template('attendance.html',courses=courses_list,cid=cid,class_date=class_date,roster=roster,student_view=False)

    @app.route('/marks',methods=['GET','POST'])
    @gate()
    def marks():
        if g.user['role']=='student':
            if request.method=='POST':abort(403)
            records=rows('SELECT c.name,m.internal,m.external,m.assessment FROM enrollments e JOIN courses c ON c.id=e.course_id LEFT JOIN marks m ON m.student_id=e.student_id AND m.course_id=e.course_id WHERE e.student_id=? ORDER BY c.name',(g.user['linked_id'],))
            return render_template('marks.html',records=records,student_view=True)
        courses_list=rows('SELECT * FROM courses WHERE faculty_id=? ORDER BY name',(g.user['linked_id'],)) if g.user['role']=='faculty' else rows('SELECT * FROM courses ORDER BY name')
        cid=request.values.get('course_id') or (courses_list[0]['id'] if courses_list else '')
        if cid:owned_course(cid)
        roster=rows('SELECT s.*,m.internal,m.external FROM enrollments e JOIN students s ON s.id=e.student_id LEFT JOIN marks m ON m.student_id=s.id AND m.course_id=e.course_id AND m.assessment=? WHERE e.course_id=? ORDER BY s.name',('End Semester',cid)) if cid else []
        if request.method=='POST':
            try:
                values=[(s['id'],cid,'End Semester',safe_int(request.form.get('internal_'+s['id']),0,40),safe_int(request.form.get('external_'+s['id']),0,60)) for s in roster]
                if not values:raise ValueError('No enrolled students for this course.')
                with db():
                    db().executemany('INSERT INTO marks VALUES(?,?,?,?,?) ON CONFLICT(student_id,course_id,assessment) DO UPDATE SET internal=excluded.internal,external=excluded.external',values)
                    audit('record','marks',cid+':End Semester')
                flash('Marks saved.','success')
            except ValueError as exc:flash(str(exc),'error')
            return redirect(url_for('marks',course_id=cid))
        return render_template('marks.html',courses=courses_list,cid=cid,roster=roster,student_view=False)

    @app.route('/fees',methods=['GET','POST'])
    @gate('admin','student')
    def fees():
        if request.method=='POST':
            if g.user['role']!='admin':abort(403)
            if request.form.get('status') not in ('Paid','Pending','Overdue'):abort(400)
            with db():
                db().execute('UPDATE fees SET status=? WHERE id=?',(request.form['status'],request.form['fee_id']))
                audit('update','fee',request.form['fee_id'])
            flash('Fee status saved.','success');return redirect(url_for('fees'))
        clause=' WHERE f.student_id=?' if g.user['role']=='student' else ''
        return render_template('fees.html',items=rows('SELECT f.*,s.name FROM fees f JOIN students s ON s.id=f.student_id'+clause+' ORDER BY f.due_date DESC',(g.user['linked_id'],) if clause else ()))

    @app.route('/timetable',methods=['GET','POST'])
    @gate()
    def timetable():
        if request.method=='POST':
            if g.user['role']!='admin':abort(403)
            if request.form.get('action')=='delete':
                with db():db().execute('DELETE FROM timetable WHERE id=?',(request.form['id'],))
            else:
                try:
                    with db():db().execute('INSERT INTO timetable(course_id,day,start_time,end_time,room) VALUES(?,?,?,?,?)',(request.form['course_id'],request.form['day'],request.form['start_time'],request.form['end_time'],request.form['room']))
                except (sqlite3.IntegrityError,PGIntegrityError):flash('Choose a valid course.','error')
            return redirect(url_for('timetable'))
        sql='SELECT t.*,c.name course_name,f.name faculty_name FROM timetable t JOIN courses c ON c.id=t.course_id LEFT JOIN faculty f ON f.id=c.faculty_id'
        if g.user['role']=='faculty':sql+=' WHERE c.faculty_id=?';params=(g.user['linked_id'],)
        elif g.user['role']=='student':sql+=' JOIN enrollments e ON e.course_id=c.id WHERE e.student_id=?';params=(g.user['linked_id'],)
        else:params=()
        return render_template('timetable.html',items=rows(sql+' ORDER BY CASE t.day WHEN "Monday" THEN 1 WHEN "Tuesday" THEN 2 WHEN "Wednesday" THEN 3 WHEN "Thursday" THEN 4 WHEN "Friday" THEN 5 ELSE 6 END,t.start_time',params),courses=rows('SELECT * FROM courses ORDER BY name'))

    @app.route('/profile')
    @gate('student')
    def profile():return render_template('profile.html',item=one('SELECT * FROM students WHERE id=?',(g.user['linked_id'],)))

    @app.route('/reports')
    @gate('admin')
    def reports():
        kind=request.args.get('type','students')
        if kind not in ('students','attendance','marks','fees'):abort(400)
        sql={'students':'SELECT id,name,department,semester,email FROM students ORDER BY name','attendance':'SELECT a.class_date,s.id student_id,s.name,c.name course,a.status FROM attendance a JOIN students s ON s.id=a.student_id JOIN courses c ON c.id=a.course_id ORDER BY a.class_date DESC','marks':'SELECT s.id student_id,s.name,c.name course,m.internal,m.external,(m.internal+m.external) total FROM marks m JOIN students s ON s.id=m.student_id JOIN courses c ON c.id=m.course_id ORDER BY s.name','fees':'SELECT s.id student_id,s.name,f.semester,f.amount,f.due_date,f.status FROM fees f JOIN students s ON s.id=f.student_id ORDER BY s.name'}[kind]
        values=[dict(r) for r in rows(sql)]
        if request.args.get('export')=='csv':
            output=io.StringIO();writer=csv.DictWriter(output,fieldnames=list(values[0]) if values else [])
            if values:writer.writeheader();writer.writerows(values)
            return Response(output.getvalue(),mimetype='text/csv',headers={'Content-Disposition':f'attachment; filename={kind}-report.csv'})
        return render_template('reports.html',kind=kind,items=values)

    @app.errorhandler(403)
    def forbidden(_error):return render_template('error.html',title='Access denied',message='Your account does not have permission to open this page.'),403

    @app.errorhandler(404)
    def missing(_error):return render_template('error.html',title='Page not found',message='The requested record could not be found.'),404

    @app.cli.command('create-api-token')
    @click.option('--username', prompt=True, help='Existing SIS username that will own the token.')
    @click.option('--name', prompt='Token name')
    def create_api_token(username, name):
        """Create a revocable bearer token for the API. The raw token is shown once."""
        user = one('SELECT id,username FROM users WHERE username=?', (username.strip().lower(),))
        if not user:
            raise click.ClickException('User not found.')
        raw = secrets.token_urlsafe(36)
        token_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        with db():
            db().execute('INSERT INTO api_tokens(token_hash,name,user_id) VALUES(?,?,?)', (token_hash, name.strip() or 'integration', user['id']))
        click.echo('API token created. Store it securely; it will not be shown again.')
        click.echo(raw)

    @app.cli.command('revoke-api-token')
    @click.argument('token_id', type=int)
    def revoke_api_token(token_id):
        """Revoke an API token by its database ID."""
        with db():
            cursor = db().execute('UPDATE api_tokens SET revoked_at=CURRENT_TIMESTAMP WHERE id=? AND revoked_at IS NULL', (token_id,))
        if cursor.rowcount != 1:
            raise click.ClickException('Active token not found.')
        click.echo('API token revoked.')

    @app.cli.command('create-admin')
    @click.option('--username', prompt=True)
    @click.password_option(confirmation_prompt=True)
    def create_admin(username, password):
        """Create the first administrator after applying the database schema."""
        if len(password) < 12:
            raise click.ClickException('Password must contain at least 12 characters.')
        try:
            with db():db().execute('INSERT INTO users(username,password_hash,role,linked_id) VALUES(?,?,?,?)',(username.strip().lower(),generate_password_hash(password),'admin',None))
        except Exception as exc:
            raise click.ClickException('Could not create admin. Check username and database readiness.') from exc
        click.echo('Administrator created.')

    return app


app=create_app()

if __name__=='__main__':
    app.run(debug=False)
