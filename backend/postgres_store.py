"""PostgreSQL persistence, with bounded checked connections and safe errors.

No DSN is logged, no local storage fallback, and no changes to the physics engine.
All SQL is qualified: no session state is required by Neon's transaction pooler.
"""
from contextlib import contextmanager
import hashlib
import logging
import os
from pathlib import Path
import re
import sqlite3
import threading

import psycopg
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool, PoolTimeout, PoolClosed, TooManyRequests
from fastapi import HTTPException

from models import Campus, CalculationResult
from calculation_context import stale_reason

SCHEMA_VERSION = 1
# Driver exceptions can contain server details/DSNs. Emit only our safe errors.
for _logger_name in ('psycopg', 'psycopg.pool'):
    _pool_logger = logging.getLogger(_logger_name)
    _pool_logger.handlers = [logging.NullHandler()]
    _pool_logger.propagate = False


class DatabaseUnavailable(HTTPException):
    code = 'database_unavailable'

    def __init__(self):
        super().__init__(503, 'Kalıcı veritabanına erişilemiyor. İşlem kaydedilmedi veya sonucu doğrulanamadı; bağlantı düzeldiğinde kaydı kontrol edin.')


def backend_name():
    selected = os.getenv('STORAGE_BACKEND', '').strip().lower()
    if not selected:
        selected = 'postgres' if os.getenv('DATABASE_URL') or os.getenv('RENDER') == 'true' else 'sqlite'
    if selected not in ('sqlite', 'postgres') or (os.getenv('RENDER') == 'true' and selected != 'postgres'):
        raise DatabaseUnavailable()
    return selected


class CompatRow(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class AuthCursor:
    def __init__(self, cursor): self.cursor = cursor
    def fetchone(self):
        row = self.cursor.fetchone()
        return CompatRow(row) if row is not None else None
    def fetchall(self): return [CompatRow(r) for r in self.cursor.fetchall()]


class AuthConnection:
    """Small adapter for the existing fixed auth queries, not arbitrary SQL input."""
    def __init__(self, connection): self.connection = connection
    @staticmethod
    def sql(statement):
        qualified = re.sub(r'\b(users|sessions|attempts)\b', r'portfolio25.\1', statement)
        return qualified.replace('?', '%s')
    def execute(self, statement, params=()):
        return AuthCursor(self.connection.execute(self.sql(statement), params))
    def executemany(self, statement, params):
        with self.connection.cursor() as cursor:
            cursor.executemany(self.sql(statement), params)
    def lock_auth(self, buckets):
        for bucket in sorted(buckets):
            self.connection.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s, 25))', (bucket,))


class PostgresStore:
    def __init__(self, dsn, *, max_size=3, timeout=12, connect_timeout=8):
        try:
            options = conninfo_to_dict(dsn)
            local = options.get('host') in ('localhost', '127.0.0.1', '::1')
            if not local and options.get('sslmode') not in ('require', 'verify-ca', 'verify-full'):
                raise ValueError('TLS required')
            # DSN options, including sslmode/channel_binding, remain intact.
            self.pool = ConnectionPool(dsn, min_size=0, max_size=max(1, min(int(max_size), 4)),
                timeout=timeout, max_waiting=16, max_idle=60, max_lifetime=300,
                reconnect_timeout=10, num_workers=1, open=False,
                kwargs={'connect_timeout': connect_timeout, 'prepare_threshold': None, 'row_factory': dict_row},
                check=ConnectionPool.check_connection, name='portfolio25')
            self.pool.open()
        except (ValueError, psycopg.Error):
            raise DatabaseUnavailable() from None
        self._migrated = False
        self._migration_lock = threading.Lock()

    def close(self): self.pool.close()

    @contextmanager
    def connection(self, *, migrate=True):
        if migrate and not self._migrated:
            self.migrate()
        try:
            with self.pool.connection() as connection:
                # Transaction-local settings work with Neon PgBouncer.
                connection.execute("SET LOCAL statement_timeout = '15000'")
                connection.execute("SET LOCAL lock_timeout = '5000'")
                yield connection
        except psycopg.errors.UniqueViolation:
            raise
        except (psycopg.Error, PoolTimeout, PoolClosed, TooManyRequests) as error:
            # Category only: exception text can contain host names or credentials.
            logging.getLogger('portfolio25.storage').warning('PostgreSQL request unavailable (%s)', type(error).__name__)
            raise DatabaseUnavailable() from None

    def migrate(self):
        with self._migration_lock:
            with self.connection(migrate=False) as connection:
                connection.execute('SELECT pg_advisory_xact_lock(25002501)')
                connection.execute('CREATE SCHEMA IF NOT EXISTS portfolio25')
                connection.execute('''CREATE TABLE IF NOT EXISTS portfolio25.schema_migrations(
                    version INTEGER PRIMARY KEY, checksum TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
                for path in sorted((Path(__file__).parent / 'db_migrations').glob('*.sql')):
                    version = int(path.name.split('_', 1)[0])
                    script = path.read_text(encoding='utf-8')
                    digest = hashlib.sha256(script.encode()).hexdigest()
                    previous = connection.execute('SELECT checksum FROM portfolio25.schema_migrations WHERE version=%s', (version,)).fetchone()
                    if previous:
                        if previous['checksum'] != digest:
                            raise DatabaseUnavailable()
                        continue
                    connection.execute(script, prepare=False)
                    connection.execute('INSERT INTO portfolio25.schema_migrations(version,checksum) VALUES(%s,%s)', (version, digest))
            self._migrated = True

    @contextmanager
    def auth_connection(self):
        try:
            with self.connection() as connection:
                yield AuthConnection(connection)
        except psycopg.errors.UniqueViolation:
            # Preserve the existing generic duplicate-registration response.
            raise sqlite3.IntegrityError('duplicate account') from None

    def health(self):
        with self.connection() as connection:
            row = connection.execute('SELECT max(version) AS version FROM portfolio25.schema_migrations').fetchone()
            if row['version'] != SCHEMA_VERSION:
                raise DatabaseUnavailable()

    def project(self, uid, project_id):
        with self.connection() as connection:
            row = connection.execute('SELECT document FROM portfolio25.projects WHERE owner_id=%s AND project_id=%s', (uid, project_id)).fetchone()
            return row['document'] if row else None

    def projects(self, uid):
        with self.connection() as connection:
            return [r['document'] for r in connection.execute('SELECT document FROM portfolio25.projects WHERE owner_id=%s ORDER BY project_id', (uid,)).fetchall()]

    def seed_pilot(self, uid, samples, dataset):
        created, preserved = [], []
        with self.connection() as connection:
            connection.execute('SELECT id FROM portfolio25.users WHERE id=%s FOR UPDATE', (uid,))
            for sample in samples:
                row = connection.execute('SELECT document FROM portfolio25.projects WHERE owner_id=%s AND project_id=%s', (uid, sample.id)).fetchone()
                if row:
                    current = Campus.model_validate(row['document'])
                    if not current.pilot or current.pilot.get('dataset') != dataset:
                        raise HTTPException(409, 'Pilot kimliği mevcut başka bir kayda ait; hiçbir kayıt değiştirilmedi.')
                    preserved.append(sample.id)
                else:
                    connection.execute('INSERT INTO portfolio25.projects(owner_id,project_id,revision,document) VALUES(%s,%s,%s,%s)',
                        (uid, sample.id, sample.revision, Jsonb(sample.model_dump(mode='json'))))
                    created.append(sample.id)
        return created, preserved

    def save_project(self, uid, campus, expected_revision=None):
        if expected_revision is not None and campus.revision != expected_revision + 1:
            raise HTTPException(409, 'Yeni girdi revizyonu beklenen sırada değil.')
        with self.connection() as connection:
            if expected_revision is None:
                row = connection.execute('''INSERT INTO portfolio25.projects(owner_id,project_id,revision,document)
                    VALUES(%s,%s,%s,%s) ON CONFLICT(owner_id,project_id) DO NOTHING RETURNING project_id''',
                    (uid, campus.id, campus.revision, Jsonb(campus.model_dump(mode='json')))).fetchone()
                return bool(row)
            row = connection.execute('''UPDATE portfolio25.projects SET revision=%s,document=%s
                WHERE owner_id=%s AND project_id=%s AND revision=%s RETURNING project_id''',
                (campus.revision, Jsonb(campus.model_dump(mode='json')), uid, campus.id, expected_revision)).fetchone()
            if not row:
                raise HTTPException(409, 'Veri başka bir oturumda değişti. Sayfayı yenileyip tekrar deneyin.')
            return True

    def last_result(self, uid, project_id):
        with self.connection() as connection:
            row = connection.execute('''SELECT c.document FROM portfolio25.projects p
                JOIN portfolio25.calculations c ON c.owner_id=p.owner_id AND c.project_id=p.project_id
                    AND c.calculation_id=p.latest_calculation_id
                WHERE p.owner_id=%s AND p.project_id=%s''', (uid, project_id)).fetchone()
            return CalculationResult.model_validate(row['document']) if row else None

    def save_result(self, uid, campus, result):
        with self.connection() as connection:
            row = connection.execute('SELECT document FROM portfolio25.projects WHERE owner_id=%s AND project_id=%s FOR UPDATE', (uid, campus.id)).fetchone()
            if not row or stale_reason(Campus.model_validate(row['document']), result):
                raise HTTPException(409, 'Hesaplama sırasında girdiler değişti; sonucu yeniden hesaplayın.')
            document = result.model_dump(mode='json')
            existing = connection.execute('SELECT document FROM portfolio25.calculations WHERE owner_id=%s AND project_id=%s AND calculation_id=%s',
                (uid, campus.id, result.calculation_id)).fetchone()
            if existing and existing['document'] != document:
                raise HTTPException(409, 'Hesap kimliği başka bir sonuçla eşleşiyor; sonuç kaydedilmedi.')
            connection.execute('''INSERT INTO portfolio25.calculations(owner_id,project_id,calculation_id,document)
                VALUES(%s,%s,%s,%s) ON CONFLICT(owner_id,project_id,calculation_id) DO NOTHING''',
                (uid, campus.id, result.calculation_id, Jsonb(document)))
            connection.execute('UPDATE portfolio25.projects SET latest_calculation_id=%s WHERE owner_id=%s AND project_id=%s', (result.calculation_id, uid, campus.id))


_store = None
_store_key = None
_store_lock = threading.Lock()


def get_store():
    global _store, _store_key
    if backend_name() == 'sqlite':
        return None
    dsn = os.getenv('DATABASE_URL', '').strip()
    if not dsn:
        raise DatabaseUnavailable()
    # Key only used in memory. Never print it or the pool representation.
    with _store_lock:
        if _store is None or _store_key != dsn:
            if _store is not None: _store.close()
            _store = PostgresStore(dsn)
            _store_key = dsn
        return _store


if __name__ == '__main__':
    # Intentionally do not read .env; load DATABASE_URL privately into the process.
    try:
        store = get_store()
        if store is None: raise DatabaseUnavailable()
        store.migrate()
        print('PostgreSQL migration tamamlandı; mevcut kayıtlar korunur.')
        store.close()
    except DatabaseUnavailable:
        raise SystemExit('PostgreSQL migration yapılamadı. Bağlantı, TLS ve yetkileri kontrol edin; gizli bağlantıyı çıktı olarak paylaşmayın.') from None
