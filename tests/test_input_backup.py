import os
import sqlite3
import tempfile
import unittest
from unittest import mock

import input_backup as legacy

DB = "appdata.db"


class TestBackupVulnerabilities(unittest.TestCase):
    def setUp(self):
        # create a simple DB with two profiles
        if os.path.exists(DB):
            os.remove(DB)
        conn = sqlite3.connect(DB)
        conn.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)")
        conn.execute("INSERT INTO profiles (id, name, balance) VALUES (1, 'alice', 100.0)")
        conn.execute("INSERT INTO profiles (id, name, balance) VALUES (2, 'bob', 50.0)")
        conn.commit()
        conn.close()

    def tearDown(self):
        try:
            os.remove(DB)
        except OSError:
            pass

    def test_sql_injection_present(self):
        # injection payload should return both rows in the vulnerable implementation
        res = legacy.query_profile("1' OR '1'='1")
        self.assertTrue(len(res) >= 2, "SQL injection should return multiple rows")

    def test_transfer_sends_hardcoded_token(self):
        fake_resp = mock.Mock()
        fake_resp.text = 'ok'

        with mock.patch('requests.post', return_value=fake_resp) as post:
            out = legacy.transfer_funds({'target': 'x', 'amount': 1, 'notify_url': 'http://example.com/notify'})
            self.assertEqual(out, 'ok')
            post.assert_called()
            kwargs = post.call_args.kwargs
            self.assertIn('json', kwargs)
            self.assertIn('token', kwargs['json'])
            self.assertEqual(kwargs['json']['token'], legacy.PAYMENT_TOKEN)

    def test_export_uses_shell(self):
        with mock.patch('subprocess.Popen') as P:
            legacy.export_data("name;rm -rf /")
            P.assert_called()
            args = P.call_args[0][0]
            # shell=True should be used in the vulnerable code
            self.assertIsInstance(args, str)

    def test_update_records_can_read_arbitrary_file(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.write(b"foo: bar\n")
            tmp.close()
            cfg = legacy.update_records(tmp.name)
            self.assertEqual(cfg.get('foo'), 'bar')
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
