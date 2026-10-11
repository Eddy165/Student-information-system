import tempfile
import unittest
import os
from pathlib import Path

from app import create_app


class SISIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING': True, 'DATABASE': str(Path(self.temp.name) / 'sis.sqlite3')})
        self.client = self.app.test_client()
        self.client.get('/login')

    def tearDown(self):
        self.temp.cleanup()

    def csrf(self):
        with self.client.session_transaction() as current:
            value = current.get('csrf')
        if not value:
            self.client.get('/login')
            with self.client.session_transaction() as current:
                value = current['csrf']
        return value

    def login(self, username, password):
        return self.client.post('/login', data={'csrf': self.csrf(), 'username': username, 'password': password})

    def logout(self):
        return self.client.post('/logout', data={'csrf': self.csrf()})


    def api_token(self, username='faculty'):
        import hashlib
        import secrets
        raw = secrets.token_urlsafe(24)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self.app.app_context():
            import sqlite3
            con = sqlite3.connect(self.app.config['DATABASE'])
            user_id = con.execute('SELECT id FROM users WHERE username=?', (username,)).fetchone()[0]
            con.execute('INSERT INTO api_tokens(token_hash,name,user_id) VALUES(?,?,?)', (digest, 'test-token', user_id))
            con.commit(); con.close()
        return raw

    def test_api_auth_and_scoped_data(self):
        token = self.api_token('faculty')
        response = self.client.get('/api/v1/me', headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data']['role'], 'faculty')
        courses = self.client.get('/api/v1/courses', headers={'Authorization': 'Bearer ' + token})
        self.assertEqual(courses.status_code, 200)
        self.assertTrue(all(row['faculty_id'] == 'FAC101' for row in courses.json['data']))
        self.assertEqual(self.client.get('/api/v1/students').status_code, 401)

    def test_api_can_write_attendance_without_browser_csrf(self):
        token = self.api_token('faculty')
        response = self.client.post('/api/v1/attendance', headers={
            'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'
        }, json={
            'course_id': 'IT24501', 'class_date': '2026-10-01',
            'entries': [{'student_id': 'IT24018', 'status': 'Present'}]
        })
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            import sqlite3
            con=sqlite3.connect(self.app.config['DATABASE'])
            self.assertEqual(con.execute('SELECT status FROM attendance WHERE student_id=? AND class_date=?',('IT24018','2026-10-01')).fetchone()[0], 'Present')
            con.close()

    def test_credentials_roles_and_csrf(self):
        self.assertEqual(self.login('admin', 'wrong').status_code, 200)
        self.assertEqual(self.login('admin', 'admin123').status_code, 302)
        self.assertEqual(self.client.post('/students/new', data={'id': 'IT99999'}).status_code, 400)
        self.logout()
        self.login('student', 'student123')
        self.assertEqual(self.client.get('/reports').status_code, 403)
        self.assertEqual(self.client.get('/students/new').status_code, 403)
        self.assertEqual(self.client.post('/marks', data={'csrf': self.csrf()}).status_code, 403)

    def test_attendance_marks_and_student_readback(self):
        self.login('faculty', 'faculty123')
        self.assertEqual(self.client.get('/attendance?course_id=IT24502').status_code, 403)
        entries={'csrf': self.csrf(), 'course_id': 'IT24501', 'class_date': '2026-09-25',
                 'status_IT24018': 'Present', 'status_IT24027': 'Absent', 'status_IT24044': 'Present'}
        self.assertEqual(self.client.post('/attendance', data=entries).status_code, 302)
        self.assertEqual(self.client.post('/attendance', data=entries).status_code, 302)
        marks={'csrf': self.csrf(), 'course_id': 'IT24501', 'internal_IT24018': 36, 'external_IT24018': 54,
               'internal_IT24027': 31, 'external_IT24027': 48, 'internal_IT24044': 34, 'external_IT24044': 52}
        self.assertEqual(self.client.post('/marks', data=marks).status_code, 302)
        self.logout()
        self.login('student', 'student123')
        self.assertIn(b'100%', self.client.get('/attendance').data)
        self.assertIn(b'86', self.client.get('/marks').data)
        with self.app.app_context():
            import sqlite3
            con=sqlite3.connect(self.app.config['DATABASE'])
            self.assertEqual(con.execute('SELECT COUNT(*) FROM attendance WHERE class_date=?',('2026-09-25',)).fetchone()[0],3)
            con.close()

    def test_admin_creates_user_and_exports_report(self):
        self.login('admin', 'admin123')
        self.assertEqual(self.client.post('/students/new', data={
            'csrf': self.csrf(), 'id': 'IT24099', 'name': 'Test Learner',
            'department': 'Information Technology', 'semester': 4,
            'email': 'learner@licet.ac.in', 'phone': '', 'initial_password': 'newpassword123'
        }).status_code, 302)
        report=self.client.get('/reports?type=students&export=csv')
        self.assertEqual(report.status_code,200)
        self.assertIn(b'IT24099',report.data)
        self.logout()
        self.assertEqual(self.login('it24099','newpassword123').status_code,302)
        self.assertIn(b'Test Learner',self.client.get('/profile').data)

    def test_security_headers_policy_pages_and_login_limit(self):
        response=self.client.get('/privacy')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'Draft policy',response.data)
        self.assertIn(b'favicon.svg',self.client.get('/login').data)
        self.assertIn('frame-ancestors',response.headers['Content-Security-Policy'])
        for _ in range(5):
            self.assertEqual(self.login('wrong-user','wrong').status_code,200)
        self.assertEqual(self.login('wrong-user','wrong').status_code,429)

    def test_password_change_revokes_current_session(self):
        self.login('student','student123')
        response=self.client.post('/account/password',data={
            'csrf':self.csrf(),'current_password':'student123','new_password':'longer-unique-password-123'
        })
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/profile').status_code,302)
        self.assertEqual(self.login('student','longer-unique-password-123').status_code,302)

    def test_portal_and_session_csrf_api(self):
        self.login('student', 'student123')
        portal = self.client.get('/portal')
        self.assertEqual(portal.status_code, 200)
        self.assertIn(b'CampusOS', portal.data)
        csrf_response = self.client.get('/api/v1/auth/csrf')
        self.assertEqual(csrf_response.status_code, 200)
        token = csrf_response.json['csrf']
        rejected = self.client.post('/api/v1/auth/logout')
        self.assertEqual(rejected.status_code, 400)
        accepted = self.client.post('/api/v1/auth/logout', headers={'X-CSRF-Token': token})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(self.client.get('/api/v1/me').status_code, 401)

    def test_role_scoped_fees_and_timetable(self):
        self.login('student', 'student123')
        fees = self.client.get('/api/v1/fees')
        self.assertEqual(fees.status_code, 200)
        self.assertTrue(all(row['student_id'] == 'IT24044' for row in fees.json['data']))
        timetable = self.client.get('/api/v1/timetable')
        self.assertEqual(timetable.status_code, 200)
        self.assertTrue(all(row['course_id'] in {'IT24501', 'IT24502', 'IT24503'} for row in timetable.json['data']))

    def test_production_configuration_fails_closed(self):
        original=os.environ.get('SIS_ENV')
        os.environ['SIS_ENV']='production'
        try:
            with self.assertRaisesRegex(RuntimeError,'Production configuration is incomplete'):
                create_app({'TESTING':True,'DATABASE':str(Path(self.temp.name)/'other.sqlite3')})
        finally:
            if original is None:os.environ.pop('SIS_ENV',None)
            else:os.environ['SIS_ENV']=original


if __name__ == '__main__':
    unittest.main()
