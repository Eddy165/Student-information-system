"""Versioned JSON API for integrations and future mobile clients."""
import hashlib
import secrets
from functools import wraps

from flask import Blueprint, g, jsonify, request

api = Blueprint('api', __name__, url_prefix='/api/v1')


def _row(row):
    return dict(row) if row else None


def _rows(rows):
    return [dict(row) for row in rows]


def _current_api_user():
    # Browser sessions remain valid for API calls, while integrations can use
    # a revocable bearer token created with `flask create-api-token`.
    if g.get('user'):
        return g.user
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        return None
    raw = header[7:].strip()
    if not raw:
        return None
    token_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    token = g.db.execute(
        'SELECT u.*, t.id token_id FROM api_tokens t JOIN users u ON u.id=t.user_id '
        'WHERE t.token_hash=? AND t.revoked_at IS NULL', (token_hash,)
    ).fetchone()
    if token:
        g.db.execute('UPDATE api_tokens SET last_used_at=CURRENT_TIMESTAMP WHERE id=?', (token['token_id'],))
        g.db.commit()
        return token
    return None


def api_auth(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            user = _current_api_user()
            if not user:
                return jsonify(error='authentication_required'), 401
            if roles and user['role'] not in roles:
                return jsonify(error='forbidden'), 403
            g.api_user = user
            return fn(*args, **kwargs)
        return wrapped
    return decorator


@api.get('/auth/csrf')
def csrf_token():
    # Session-bound token for state-changing cookie-authenticated requests.
    from flask import session
    if not session.get('csrf'):
        import secrets
        session['csrf'] = secrets.token_urlsafe(32)
    return jsonify(csrf=session['csrf'])


@api.post('/auth/logout')
def logout():
    from flask import session
    session.clear()
    return jsonify(message='signed_out')


@api.get('/me')
@api_auth()
def me():
    return jsonify(data={k: g.api_user[k] for k in ('id', 'username', 'role', 'linked_id')})


@api.get('/students')
@api_auth('admin', 'faculty')
def students():
    q = request.args.get('q', '').strip()
    if g.api_user['role'] == 'faculty':
        sql = ('SELECT DISTINCT s.id,s.name,s.department,s.semester,s.email,s.phone '
               'FROM students s JOIN enrollments e ON e.student_id=s.id '
               'JOIN courses c ON c.id=e.course_id WHERE c.faculty_id=? '
               'AND (s.name LIKE ? OR s.id LIKE ?) ORDER BY s.name')
        params = (g.api_user['linked_id'], f'%{q}%', f'%{q}%')
    else:
        sql = 'SELECT id,name,department,semester,email,phone FROM students WHERE name LIKE ? OR id LIKE ? ORDER BY name'
        params = (f'%{q}%', f'%{q}%')
    return jsonify(data=_rows(g.db.execute(sql + ' LIMIT 500', params).fetchall()))


@api.get('/courses')
@api_auth()
def courses():
    sql = 'SELECT c.id,c.name,c.department,c.semester,c.faculty_id,f.name faculty_name FROM courses c LEFT JOIN faculty f ON f.id=c.faculty_id'
    params = ()
    if g.api_user['role'] == 'faculty':
        sql += ' WHERE c.faculty_id=?'
        params = (g.api_user['linked_id'],)
    elif g.api_user['role'] == 'student':
        sql += ' JOIN enrollments e ON e.course_id=c.id WHERE e.student_id=?'
        params = (g.api_user['linked_id'],)
    return jsonify(data=_rows(g.db.execute(sql + ' ORDER BY c.name LIMIT 500', params).fetchall()))


@api.get('/timetable')
@api_auth()
def timetable():
    sql = ('SELECT t.id,t.course_id,c.name course,t.day,t.start_time,t.end_time,t.room '
           'FROM timetable t JOIN courses c ON c.id=t.course_id')
    params = ()
    if g.api_user['role'] == 'faculty':
        sql += ' WHERE c.faculty_id=?'; params = (g.api_user['linked_id'],)
    elif g.api_user['role'] == 'student':
        sql += ' JOIN enrollments e ON e.course_id=c.id WHERE e.student_id=?'; params = (g.api_user['linked_id'],)
    ordering = " ORDER BY CASE t.day WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 ELSE 7 END,t.start_time"
    return jsonify(data=_rows(g.db.execute(sql + ordering + ' LIMIT 500', params).fetchall()))


@api.get('/fees')
@api_auth('admin', 'student')
def fees():
    sql = ('SELECT f.id,f.student_id,s.name student_name,f.semester,f.amount,f.due_date,f.status '
           'FROM fees f JOIN students s ON s.id=f.student_id')
    params = ()
    if g.api_user['role'] == 'student':
        sql += ' WHERE f.student_id=?'; params = (g.api_user['linked_id'],)
    return jsonify(data=_rows(g.db.execute(sql + ' ORDER BY f.due_date DESC LIMIT 500', params).fetchall()))


@api.get('/attendance')
@api_auth()
def attendance():
    student_id = request.args.get('student_id') or (g.api_user['linked_id'] if g.api_user['role'] == 'student' else None)
    if g.api_user['role'] == 'student' and student_id != g.api_user['linked_id']:
        return jsonify(error='forbidden'), 403
    if g.api_user['role'] == 'faculty' and student_id:
        allowed = g.db.execute('SELECT 1 FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.student_id=? AND c.faculty_id=? LIMIT 1', (student_id, g.api_user['linked_id'])).fetchone()
        if not allowed:
            return jsonify(error='forbidden'), 403
    sql = ('SELECT a.student_id,a.course_id,c.name course,a.class_date,a.status '
           'FROM attendance a JOIN courses c ON c.id=a.course_id')
    params = ()
    conditions = []
    if student_id:
        conditions.append('a.student_id=?'); params += (student_id,)
    if g.api_user['role'] == 'faculty':
        conditions.append('c.faculty_id=?'); params += (g.api_user['linked_id'],)
    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    sql += ' ORDER BY a.class_date DESC LIMIT 500'
    return jsonify(data=_rows(g.db.execute(sql, params).fetchall()))


@api.get('/marks')
@api_auth()
def marks():
    student_id = request.args.get('student_id') or (g.api_user['linked_id'] if g.api_user['role'] == 'student' else None)
    if g.api_user['role'] == 'student' and student_id != g.api_user['linked_id']:
        return jsonify(error='forbidden'), 403
    sql = ('SELECT m.student_id,m.course_id,c.name course,m.assessment,m.internal,m.external,'
           '(m.internal+m.external) total FROM marks m JOIN courses c ON c.id=m.course_id')
    params = ()
    conditions = []
    if student_id:
        conditions.append('m.student_id=?'); params += (student_id,)
    if g.api_user['role'] == 'faculty':
        conditions.append('c.faculty_id=?'); params += (g.api_user['linked_id'],)
    if conditions:
        sql += ' WHERE ' + ' AND '.join(conditions)
    sql += ' ORDER BY c.name,m.assessment LIMIT 500'
    return jsonify(data=_rows(g.db.execute(sql, params).fetchall()))


@api.get('/dashboard')
@api_auth()
def dashboard():
    role = g.api_user['role']
    if role == 'admin':
        data = {
            'students': g.db.execute('SELECT COUNT(*) n FROM students').fetchone()['n'],
            'faculty': g.db.execute('SELECT COUNT(*) n FROM faculty').fetchone()['n'],
            'courses': g.db.execute('SELECT COUNT(*) n FROM courses').fetchone()['n'],
            'pending_fees': g.db.execute("SELECT COUNT(*) n FROM fees WHERE status!='Paid'").fetchone()['n'],
        }
    elif role == 'faculty':
        data = {
            'courses': g.db.execute('SELECT COUNT(*) n FROM courses WHERE faculty_id=?', (g.api_user['linked_id'],)).fetchone()['n'],
            'students': g.db.execute('SELECT COUNT(DISTINCT student_id) n FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE c.faculty_id=?', (g.api_user['linked_id'],)).fetchone()['n'],
        }
    else:
        data = {
            'courses': g.db.execute('SELECT COUNT(*) n FROM enrollments WHERE student_id=?', (g.api_user['linked_id'],)).fetchone()['n'],
            'attendance_entries': g.db.execute('SELECT COUNT(*) n FROM attendance WHERE student_id=?', (g.api_user['linked_id'],)).fetchone()['n'],
            'results': g.db.execute('SELECT COUNT(*) n FROM marks WHERE student_id=?', (g.api_user['linked_id'],)).fetchone()['n'],
        }
    return jsonify(data=data)


@api.post('/attendance')
@api_auth('admin', 'faculty')
def record_attendance():
    payload = request.get_json(silent=True) or {}
    course_id = str(payload.get('course_id', '')).strip().upper()
    class_date = str(payload.get('class_date', '')).strip()
    entries = payload.get('entries')
    if not course_id or not class_date or not isinstance(entries, list):
        return jsonify(error='course_id, class_date and entries are required'), 400
    if g.api_user['role'] == 'faculty':
        course = g.db.execute('SELECT id FROM courses WHERE id=? AND faculty_id=?', (course_id, g.api_user['linked_id'])).fetchone()
    else:
        course = g.db.execute('SELECT id FROM courses WHERE id=?', (course_id,)).fetchone()
    if not course:
        return jsonify(error='course_not_accessible'), 403
    valid = {'Present', 'Absent'}
    try:
        from datetime import date
        date.fromisoformat(class_date)
    except ValueError:
        return jsonify(error='invalid_class_date'), 400
    values = []
    for item in entries:
        if not isinstance(item, dict) or item.get('status') not in valid:
            return jsonify(error='each entry requires student_id and Present/Absent status'), 400
        student_id = str(item.get('student_id', '')).strip().upper()
        enrolled = g.db.execute('SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?', (student_id, course_id)).fetchone()
        if not enrolled:
            return jsonify(error=f'{student_id} is not enrolled in {course_id}'), 400
        values.append((student_id, course_id, class_date, item['status']))
    with g.db:
        g.db.executemany(
            'INSERT INTO attendance(student_id,course_id,class_date,status) VALUES(?,?,?,?) '
            'ON CONFLICT(student_id,course_id,class_date) DO UPDATE SET status=excluded.status', values
        )
        g.db.execute('INSERT INTO audit_log(actor_id,action,object_type,object_id) VALUES(?,?,?,?)', (g.api_user['id'], 'record', 'attendance', course_id + ':' + class_date))
    return jsonify(message='attendance_saved', count=len(values)), 200


@api.post('/marks')
@api_auth('admin', 'faculty')
def record_marks():
    payload = request.get_json(silent=True) or {}
    course_id = str(payload.get('course_id', '')).strip().upper()
    entries = payload.get('entries')
    if not course_id or not isinstance(entries, list):
        return jsonify(error='course_id and entries are required'), 400
    if g.api_user['role'] == 'faculty':
        course = g.db.execute('SELECT id FROM courses WHERE id=? AND faculty_id=?', (course_id, g.api_user['linked_id'])).fetchone()
    else:
        course = g.db.execute('SELECT id FROM courses WHERE id=?', (course_id,)).fetchone()
    if not course:
        return jsonify(error='course_not_accessible'), 403
    values = []
    for item in entries:
        try:
            student_id = str(item['student_id']).strip().upper()
            internal = int(item['internal'])
            external = int(item['external'])
        except (KeyError, TypeError, ValueError):
            return jsonify(error='each entry requires student_id, internal and external'), 400
        if not 0 <= internal <= 40 or not 0 <= external <= 60:
            return jsonify(error='marks must be internal 0-40 and external 0-60'), 400
        enrolled = g.db.execute('SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?', (student_id, course_id)).fetchone()
        if not enrolled:
            return jsonify(error=f'{student_id} is not enrolled in {course_id}'), 400
        values.append((student_id, course_id, 'End Semester', internal, external))
    with g.db:
        g.db.executemany(
            'INSERT INTO marks(student_id,course_id,assessment,internal,external) VALUES(?,?,?,?,?) '
            'ON CONFLICT(student_id,course_id,assessment) DO UPDATE SET internal=excluded.internal,external=excluded.external', values
        )
        g.db.execute('INSERT INTO audit_log(actor_id,action,object_type,object_id) VALUES(?,?,?,?)', (g.api_user['id'], 'record', 'marks', course_id + ':End Semester'))
    return jsonify(message='marks_saved', count=len(values)), 200
