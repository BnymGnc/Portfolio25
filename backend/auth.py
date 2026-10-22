"""Persistent opaque cookie sessions. Secrets never enter API responses or logs."""
import hashlib
import secrets
import sqlite3
import time
from contextvars import ContextVar
from contextlib import contextmanager
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator

user_context = ContextVar('authenticated_user', default=None)
COOKIE = 'portfolio25_session'
TTL = 7 * 86400
ONBOARDING_VERSION = 1
hasher = PasswordHasher()
dummy_hash = hasher.hash(secrets.token_urlsafe(24))


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=12, max_length=128)

    @field_validator('email')
    @classmethod
    def email_format(cls, value):
        import re
        value = value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Geçerli e-posta adresi girin.')
        return value


class Accounts:
    def __init__(self, path_provider, secure=False, storage_guard=None, db_provider=None):
        self.path_provider = path_provider
        self.secure = secure
        self.storage_guard = storage_guard
        self.db_provider = db_provider

    @contextmanager
    def db(self):
        if self.storage_guard:
            self.storage_guard()
        provider = self.db_provider() if self.db_provider else None
        if provider is not None:
            with provider() as db:
                yield db
            return
        path = self.path_provider()
        path.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL, onboarding_version INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id),
                    csrf TEXT NOT NULL, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS attempts(bucket TEXT NOT NULL, moment REAL NOT NULL);
            ''')
            yield db
            db.commit()
        finally:
            db.close()

    def session(self, request):
        token = request.cookies.get(COOKIE, '')
        if not token or len(token) > 128:
            return None
        digest = hashlib.sha256(token.encode()).hexdigest()
        with self.db() as db:
            row = db.execute('SELECT * FROM sessions WHERE digest=? AND expires>?', (digest, time.time())).fetchone()
            return dict(row) if row else None

    def public_user(self, uid):
        if not uid:
            return None
        with self.db() as db:
            row = db.execute('SELECT id,email,onboarding_version FROM users WHERE id=?', (uid,)).fetchone()
            return dict(row) if row else None

    def issue(self, response, uid=None, previous=None):
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
            if previous:
                db.execute('DELETE FROM sessions WHERE digest=?', (previous['digest'],))
            db.execute('INSERT INTO sessions VALUES(?,?,?,?)',
                (hashlib.sha256(token.encode()).hexdigest(), uid, csrf, time.time() + (TTL if uid else 3600)))
        response.set_cookie(COOKIE, token, httponly=True, secure=self.secure, samesite='lax',
                            max_age=TTL if uid else 3600, path='/')
        return {'user': self.public_user(uid), 'csrf': csrf, 'onboarding_version': ONBOARDING_VERSION}

    def check_csrf(self, request, session, origins):
        if request.headers.get('origin') not in origins:
            raise HTTPException(403, 'İstek kaynağı izinli değil. Giriş ve kayıt için https://buildingportfolio25.vercel.app adresini açın; eski dağıtım bağlantısını kullanmayın.')
        if not session or not secrets.compare_digest(session['csrf'], request.headers.get('x-csrf-token', '')):
            raise HTTPException(403, 'Oturum doğrulaması yenilenmeli; sayfayı yeniden açın.')

    def limit(self, request, email):
        # Untrusted forwarded headers cannot bypass rate limits.
        ip = request.client.host if request.client else 'unknown'
        buckets = ['ip:' + ip, 'email:' + hashlib.sha256(email.encode()).hexdigest()]
        now = time.time()
        with self.db() as db:
            if hasattr(db, 'lock_auth'):
                db.lock_auth(buckets)
            db.execute('DELETE FROM attempts WHERE moment<?', (now - 900,))
            for bucket in buckets:
                if db.execute('SELECT count(*) FROM attempts WHERE bucket=?', (bucket,)).fetchone()[0] >= 12:
                    raise HTTPException(429, 'Çok sayıda giriş denemesi. On beş dakika sonra tekrar deneyin.')
            db.executemany('INSERT INTO attempts VALUES(?,?)', [(b, now) for b in buckets])

    def register(self, credentials):
        uid = secrets.token_hex(16)
        password_hash = hasher.hash(credentials.password)
        try:
            with self.db() as db:
                db.execute('INSERT INTO users(id,email,password_hash) VALUES(?,?,?)', (uid, credentials.email, password_hash))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'Bu adres için kayıt oluşturulamadı; giriş yapmayı deneyin.') from None
        return uid

    def login(self, credentials):
        with self.db() as db:
            row = db.execute('SELECT id,password_hash FROM users WHERE email=?', (credentials.email,)).fetchone()
        try:
            hasher.verify(row['password_hash'] if row else dummy_hash, credentials.password)
        except (VerificationError, InvalidHashError):
            raise HTTPException(401, 'E-posta veya parola geçersiz.') from None
        if not row:
            raise HTTPException(401, 'E-posta veya parola geçersiz.')
        return row['id']
