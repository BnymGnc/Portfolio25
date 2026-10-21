import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from fastapi import HTTPException
from fastapi.responses import Response
from fastapi.testclient import TestClient

from auth import Accounts, Credentials
import main
from storage_admin import backup, reset_password, restore
from postgres_store import PostgresStore, DatabaseUnavailable


class StorageTests(unittest.TestCase):
    def test_remote_tls_required_and_pool_is_bounded_without_connecting(self):
        from psycopg.conninfo import make_conninfo, conninfo_to_dict
        settings=dict(host='example.invalid',dbname='qa',user='qa',password='test-only')
        with self.assertRaises(DatabaseUnavailable):PostgresStore(make_conninfo(**settings,sslmode='disable'))
        store=PostgresStore(make_conninfo(**settings,sslmode='require',channel_binding='require'),max_size=100)
        try:
            options=conninfo_to_dict(store.pool.conninfo)
            self.assertEqual(options['sslmode'],'require');self.assertEqual(options['channel_binding'],'require')
            self.assertLessEqual(store.pool.max_size,4)
            self.assertEqual(store.pool.min_size,0)
        finally:store.close()

    def test_production_missing_database_rejects_without_local_writes(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(main, 'DATA_FILE', Path(temp) / 'campus.json'), \
             patch.dict(os.environ, {'RENDER': 'true', 'STORAGE_BACKEND': 'postgres', 'DATABASE_URL': ''}), TestClient(main.app) as client:
            health = client.get('/api/health')
            self.assertEqual(health.status_code, 503)
            self.assertEqual(health.json()['storage']['status'], 'unavailable')
            for method, url in [('get', '/api/auth/session'), ('post', '/api/auth/login'), ('post', '/api/auth/register')]:
                response = getattr(client, method)(url)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()['error']['code'], 'database_unavailable')
                self.assertNotIn(temp, response.text)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_same_storage_preserves_login_new_storage_reproduces_lost_account_401(self):
        credentials = Credentials(email='persist@example.test', password='temporary-password-123')
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            store = Accounts(lambda: Path(a) / 'accounts.sqlite3')
            uid = store.register(credentials)
            reopened = Accounts(lambda: Path(a) / 'accounts.sqlite3')
            self.assertEqual(reopened.login(credentials), uid)
            empty = Accounts(lambda: Path(b) / 'accounts.sqlite3')
            with self.assertRaises(HTTPException) as unknown:
                empty.login(credentials)
            with self.assertRaises(HTTPException) as wrong:
                reopened.login(Credentials(email=credentials.email, password='incorrect-password-456'))
            self.assertEqual(unknown.exception.status_code, 401)
            self.assertEqual(wrong.exception.detail, unknown.exception.detail)
            # Neither failure creates a user, changes the password or bypasses auth.
            self.assertEqual(reopened.login(credentials), uid)
            with empty.db() as db:
                self.assertEqual(db.execute('SELECT count(*) FROM users').fetchone()[0], 0)



class StorageAdminTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'data'
        self.accounts = Accounts(lambda: self.data / 'accounts.sqlite3')
        self.credentials = Credentials(email='operator-test@example.test', password='temporary-password-123')
        self.uid = self.accounts.register(self.credentials)
        self.accounts.issue(Response(), self.uid)
        self.project = self.data / 'users' / self.uid / 'projects' / 'project-0123456789ab.json'
        self.project.parent.mkdir(parents=True)
        self.project.write_text(json.dumps({'revision': 7, 'private_input': 'test-only'}), encoding='utf-8')

    def test_backup_and_restore_keep_identity_credentials_inputs_and_revoke_sessions(self):
        archive = self.root / 'snapshot.portfolio25-backup.zip'
        self.data.joinpath('.env').write_text('DO_NOT_READ=test-only', encoding='utf-8')
        before = self.project.read_bytes()
        backup(self.data, archive)
        with zipfile.ZipFile(archive) as snapshot:
            self.assertNotIn('.env', snapshot.namelist())
            self.assertIn('accounts.sqlite3', snapshot.namelist())
        target = self.root / 'restored'
        restore(archive, target)
        reopened = Accounts(lambda: target / 'accounts.sqlite3')
        self.assertEqual(reopened.login(self.credentials), self.uid)
        self.assertEqual((target / self.project.relative_to(self.data)).read_bytes(), before)
        self.assertEqual(self.project.read_bytes(), before)
        with reopened.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM sessions').fetchone()[0], 0)
        self.assertFalse((target / '.env').exists())
        with self.assertRaises(ValueError):
            restore(archive, self.data)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with self.assertRaises(FileExistsError):
            backup(self.data, archive)
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), digest)

    def test_operator_password_reset_only_changes_target_hash_and_sessions(self):
        other = self.accounts.register(Credentials(email='other@example.test', password='other-temporary-password-123'))
        self.accounts.issue(Response(), other)
        before = self.project.read_bytes()
        reset_password(self.data, self.credentials.email.upper(), 'new-temporary-password-456')
        self.assertEqual(self.accounts.login(Credentials(email=self.credentials.email, password='new-temporary-password-456')), self.uid)
        self.assertEqual(self.accounts.login(Credentials(email='other@example.test', password='other-temporary-password-123')), other)
        with self.accounts.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM sessions WHERE user_id=?', (self.uid,)).fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT count(*) FROM sessions WHERE user_id=?', (other,)).fetchone()[0], 1)
        with self.assertRaises(HTTPException):
            self.accounts.login(self.credentials)
        with self.assertRaises(ValueError):
            reset_password(self.data, 'missing@example.test', 'new-temporary-password-456')
        self.assertEqual(self.project.read_bytes(), before)
        missing = self.root / 'not-created'
        with self.assertRaises(ValueError):
            reset_password(missing, self.credentials.email, 'new-temporary-password-456')
        self.assertFalse(missing.exists())

    def test_restore_rejects_zip_traversal_before_writing_destination(self):
        archive = self.root / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as content:
            content.writestr('backup-manifest.json', json.dumps({'format': 'portfolio25-storage-v1'}))
            content.writestr('accounts.sqlite3', b'not-a-db')
            content.writestr('../outside.json', '{}')
        with self.assertRaises(ValueError):
            restore(archive, self.root / 'destination')
        self.assertFalse((self.root / 'outside.json').exists())
        self.assertFalse((self.root / 'destination').exists())


if __name__ == '__main__':
    unittest.main()
