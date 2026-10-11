"""Administrator analytics and audit views."""
from functools import wraps
from flask import Blueprint, abort, g, render_template, redirect, url_for

admin = Blueprint('admin_tools', __name__, url_prefix='/admin')


def admin_only(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not g.get('user'):
            return redirect(url_for('login'))
        if g.user['role'] != 'admin':
            abort(403)
        return fn(*args, **kwargs)
    return wrapped


@admin.get('/analytics')
@admin_only
def analytics():
    metrics = {
        'students': g.db.execute('SELECT COUNT(*) n FROM students').fetchone()['n'],
        'faculty': g.db.execute('SELECT COUNT(*) n FROM faculty').fetchone()['n'],
        'courses': g.db.execute('SELECT COUNT(*) n FROM courses').fetchone()['n'],
        'enrollments': g.db.execute('SELECT COUNT(*) n FROM enrollments').fetchone()['n'],
        'attendance': g.db.execute('SELECT COUNT(*) n FROM attendance').fetchone()['n'],
        'marks': g.db.execute('SELECT COUNT(*) n FROM marks').fetchone()['n'],
        'pending_fees': g.db.execute("SELECT COUNT(*) n FROM fees WHERE status!='Paid'").fetchone()['n'],
    }
    attendance = g.db.execute("SELECT status, COUNT(*) n FROM attendance GROUP BY status ORDER BY status").fetchall()
    fees = g.db.execute("SELECT status, COUNT(*) n FROM fees GROUP BY status ORDER BY status").fetchall()
    return render_template('analytics.html', metrics=metrics, attendance=attendance, fees=fees)


@admin.get('/audit')
@admin_only
def audit_log():
    records = g.db.execute(
        'SELECT a.id,a.action,a.object_type,a.object_id,a.created_at,u.username actor '
        'FROM audit_log a LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.created_at DESC,a.id DESC LIMIT 200'
    ).fetchall()
    return render_template('audit.html', records=records)
