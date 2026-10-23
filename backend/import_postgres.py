"""Explicit, transactional import from an operator-created private backup.

No .env reads, no implicit owner assignment and no password rehash. Use
storage_admin.py backup first. Reusing the same archive never duplicates data.
"""
import argparse
import getpass
import os
import warnings
from contextlib import closing
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sqlite3
import tempfile
import zipfile
import psycopg

from argon2 import extract_parameters
from psycopg.types.json import Jsonb
from models import Campus, CalculationResult
from migrations import migrate_v1, migrate_v2
from engine import prepare
from postgres_store import get_store, DatabaseUnavailable


def project_document(raw):
    if raw.get('schema_version', '1.0') == '1.0':
        campus = migrate_v1(raw)
    elif raw.get('schema_version') == '2.0':
        campus = migrate_v2(raw)
    else:
        campus = Campus.model_validate(raw)
    prepare(campus)  # Same physical validity rule as saves, before any target write.
    return campus


def read_archive(path):
    path = Path(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive, tempfile.TemporaryDirectory() as temp:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive paths')
        for name in names:
            part = PurePosixPath(name)
            if part.is_absolute() or '..' in part.parts or '\\' in name or ':' in name:
                raise ValueError('Unsafe archive path')
        if json.loads(archive.read('backup-manifest.json')).get('format') != 'portfolio25-storage-v1':
            raise ValueError('Unsupported backup')
        database = Path(temp) / 'accounts.sqlite3'
        with database.open('xb') as target:
            database.chmod(0o600)
            target.write(archive.read('accounts.sqlite3'))
        with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source:
            source.row_factory = sqlite3.Row
            if source.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('Invalid SQLite')
            users = [dict(r) for r in source.execute('SELECT id,email,password_hash,onboarding_version FROM users')]
            sessions = [dict(r) for r in source.execute('SELECT digest,user_id,csrf,expires FROM sessions')]
            attempts = [dict(r) for r in source.execute('SELECT bucket,moment FROM attempts')]
        ids = {u['id'] for u in users}
        for user in users:
            if not re.fullmatch(r'[a-f0-9]{32}', user['id']): raise ValueError('Invalid owner')
            extract_parameters(user['password_hash'])  # Validate format; never rehash.
        if any(s['user_id'] is not None and s['user_id'] not in ids for s in sessions):
            raise ValueError('Orphan session')
        projects, results = [], []
        for uid in ids:
            prefix = f'users/{uid}/'
            input_names = [n for n in names if n == prefix + 'campus.json' or
                           re.fullmatch(re.escape(prefix) + r'projects/project-[a-f0-9]{12}\.json', n)]
            for name in input_names:
                campus = project_document(json.loads(archive.read(name)))
                expected_id = 'campus-demo-25' if name == prefix + 'campus.json' else PurePosixPath(name).stem
                if campus.id != expected_id: raise ValueError('Project identity mismatch')
                projects.append((uid, campus))
                latest = name[:-5] + '.result.json'
                result_names = [n for n in names if n.startswith(prefix + f'history/{campus.id}/') and n.endswith('.json')]
                if latest in names: result_names.append(latest)
                for result_name in result_names:
                    raw = json.loads(archive.read(result_name))
                    result = CalculationResult.model_validate(raw)
                    if result.project_id != campus.id: raise ValueError('Result identity mismatch')
                    rid = result.calculation_id or 'legacy-' + hashlib.sha256(archive.read(result_name)).hexdigest()
                    results.append((uid, campus.id, rid, raw, result_name == latest))
        # Legacy global campus/projects stay in the backup. Never assign to the first user.
        return dict(digest=digest, users=users, sessions=sessions, attempts=attempts, projects=projects, results=results)


def import_archive(store, path, *, apply=False):
    data = read_archive(path)
    counts = {k: len(data[k]) for k in ('users', 'sessions', 'projects', 'results')}
    if not apply:
        return {'status':'validated_only', **counts}
    with store.connection() as db:
        db.execute('SELECT pg_advisory_xact_lock(25002502)')
        if db.execute('SELECT 1 FROM portfolio25.legacy_imports WHERE source_digest=%s', (data['digest'],)).fetchone():
            return {'status':'already_imported', **counts}
        for user in data['users']:
            existing = db.execute('SELECT * FROM portfolio25.users WHERE id=%s OR email=%s', (user['id'], user['email'])).fetchall()
            if existing:
                if len(existing) != 1 or any(existing[0][k] != user[k] for k in ('id', 'email', 'password_hash', 'onboarding_version')):
                    raise ValueError('Account conflict; no overwrite')
            else:
                db.execute('INSERT INTO portfolio25.users(id,email,password_hash,onboarding_version) VALUES(%s,%s,%s,%s)',
                    tuple(user[k] for k in ('id', 'email', 'password_hash', 'onboarding_version')))
        for session in data['sessions']:
            existing = db.execute('SELECT * FROM portfolio25.sessions WHERE digest=%s', (session['digest'],)).fetchone()
            if existing and any(existing[k] != session[k] for k in session):
                raise ValueError('Session conflict')
            if not existing:
                db.execute('INSERT INTO portfolio25.sessions(digest,user_id,csrf,expires) VALUES(%s,%s,%s,%s)',
                    tuple(session[k] for k in ('digest', 'user_id', 'csrf', 'expires')))
        for uid, campus in data['projects']:
            document = campus.model_dump(mode='json')
            existing = db.execute('SELECT document FROM portfolio25.projects WHERE owner_id=%s AND project_id=%s', (uid, campus.id)).fetchone()
            if existing and existing['document'] != document:
                raise ValueError('Project conflict; newer target data must not be overwritten')
            if not existing:
                db.execute('INSERT INTO portfolio25.projects(owner_id,project_id,revision,document) VALUES(%s,%s,%s,%s)',
                    (uid, campus.id, campus.revision, Jsonb(document)))
        for uid, pid, rid, raw, latest in data['results']:
            existing = db.execute('SELECT document FROM portfolio25.calculations WHERE owner_id=%s AND project_id=%s AND calculation_id=%s', (uid, pid, rid)).fetchone()
            if existing and existing['document'] != raw: raise ValueError('Calculation conflict')
            if not existing:
                db.execute('INSERT INTO portfolio25.calculations(owner_id,project_id,calculation_id,document) VALUES(%s,%s,%s,%s)', (uid, pid, rid, Jsonb(raw)))
            if latest:
                db.execute('UPDATE portfolio25.projects SET latest_calculation_id=%s WHERE owner_id=%s AND project_id=%s AND latest_calculation_id IS NULL', (rid, uid, pid))
        for attempt in data['attempts']:
            db.execute('''INSERT INTO portfolio25.attempts(bucket,moment) SELECT %s,%s
                WHERE NOT EXISTS(SELECT 1 FROM portfolio25.attempts WHERE bucket=%s AND moment=%s)''',
                (attempt['bucket'], attempt['moment'], attempt['bucket'], attempt['moment']))
        db.execute('INSERT INTO portfolio25.legacy_imports(source_digest) VALUES(%s)', (data['digest'],))
    return {'status':'imported', **counts}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--prompt-database-url', action='store_true', help='Read PostgreSQL connection privately; never reads .env or echoes the URL.')
    args = parser.parse_args()
    try:
        if args.prompt_database_url:
            os.environ['DATABASE_URL'] = getpass.getpass('Neon pooled bağlantısı (gizli; kaydedilmez): ').strip()
            os.environ['STORAGE_BACKEND'] = 'postgres'
        store = get_store()
        if store is None: raise DatabaseUnavailable()
        print(json.dumps(import_archive(store, args.archive, apply=args.apply)))
        store.close()
    except (DatabaseUnavailable, ValueError, OSError, sqlite3.Error, psycopg.Error, zipfile.BadZipFile, KeyError, getpass.GetPassWarning):
        raise SystemExit('Aktarım tamamlanmadı. Kaynak yedeği, sahiplik ve hedef çakışmalarını kontrol edin. Var olan kayıtlar ezilmedi; bağlantı veya parola ayrıntılarını paylaşmayın.') from None
