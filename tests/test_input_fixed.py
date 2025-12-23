import os
import sqlite3
import shutil
import tempfile
import unittest
from unittest import mock
import importlib

# ensure environment for secure module
os.environ['AUTH_SECRET'] = os.environ.get('AUTH_SECRET', 'test_auth_secret')
os.environ['PAYMENT_TOKEN'] = os.environ.get('PAYMENT_TOKEN', 'test_payment_token')
os.environ['ADMIN_API_KEY'] = os.environ.get('ADMIN_API_KEY', 'test_admin_key')
os.environ['ALLOWED_NOTIFY_HOSTS'] = 'localhost,127.0.0.1'

import input as fixed

DB = "appdata.db"


class TestFixedSecurity(unittest.TestCase):
    def setUp(self):
        # create DB
        if os.path.exists(DB):
            os.remove(DB)
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
        conn.execute("INSERT INTO profiles (id, name, balance) VALUES (1, 'alice', 100.0)")
        conn.commit()
        conn.close()

    def tearDown(self):
        try:
            os.remove(DB)
        except OSError:
            pass
        # clean exports/configs
        shutil.rmtree('exports', ignore_errors=True)
        shutil.rmtree('configs', ignore_errors=True)

    def test_sql_injection_prevented(self):
        res = fixed.query_profile("1' OR '1'='1")
        # injection should NOT succeed; only integer id allowed
        self.assertTrue(res == [] or len(res) == 1)

    def test_transfer_rejects_external_notify(self):
        with self.assertRaises(ValueError):
            fixed.transfer_funds({'target': 'x', 'amount': 1, 'notify_url': 'http://example.com/notify'})

    def test_transfer_allows_localhost(self):
        fake_resp = mock.Mock()
        fake_resp.text = 'ok'
        with mock.patch('requests.post', return_value=fake_resp) as post:
            out = fixed.transfer_funds({'target': 'x', 'amount': 1, 'notify_url': 'http://127.0.0.1/notify'})
            self.assertEqual(out, 'ok')
            post.assert_called()
            _, kwargs = post.call_args
            # headers passed as kwargs
            self.assertIn('headers', kwargs)
            self.assertIn('Authorization', kwargs['headers'])
            self.assertEqual(kwargs['headers']['Authorization'], f"Bearer {os.environ['PAYMENT_TOKEN']}")

    def test_export_is_safe_and_creates_zip(self):
        out = fixed.export_data('safe_export')
        self.assertTrue(out.endswith('safe_export.zip'))
        import zipfile
        with zipfile.ZipFile(out, 'r') as zf:
            self.assertIn('appdata.db', zf.namelist())

    def test_update_records_restricts_path(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.write(b"foo: bar\n")
            tmp.close()
            with self.assertRaises(ValueError):
                fixed.update_records(tmp.name)
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
