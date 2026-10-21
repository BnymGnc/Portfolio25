"""Offline operator tools. Never reads .env, prints credentials, or creates users.

Use a maintenance window with application writes stopped. Backups contain
private account hashes and project data: store them outside Git and web roots.
"""
import argparse
from contextlib import closing, contextmanager
import getpass
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
import zipfile


def existing_database(directory):
    directory = Path(directory).resolve()
    database = directory / 'accounts.sqlite3'
    if not database.is_file() or database.is_symlink():
        raise ValueError('Mevcut hesap veritabanı bulunamadı. Yeni dosya veya hesap oluşturulmadı.')
    return directory, database


@contextmanager
def connect_existing(database):
    db = sqlite3.connect(database.as_uri() + '?mode=rw', uri=True, timeout=15)
    try:
        with db:
            yield db
    finally:
        db.close()


def private_file(path):
    if os.name != 'nt':
        path.chmod(0o600)


def backup(data_dir, output):
    directory, database = existing_database(data_dir)
    output = Path(output).resolve()
    if output.is_relative_to(directory):
        raise ValueError('Yedek hedefi veri dizininin dışında olmalı.')
    output.parent.mkdir(parents=True, exist_ok=True)
    # x mode never overwrites an existing private backup.
    with output.open('xb') as destination:
        private_file(output)
        try:
            with tempfile.TemporaryDirectory() as temp:
                snapshot = Path(temp) / 'accounts.sqlite3'
                snapshot.touch(mode=0o600)
                with connect_existing(database) as source, closing(sqlite3.connect(snapshot)) as target:
                    source.backup(target)
                    if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                        raise ValueError('SQLite yedeği doğrulanamadı.')
                private_file(snapshot)
                with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                    archive.write(snapshot, 'accounts.sqlite3')
                    # Include legacy inputs, results, migrations, private projects and history.
                    # Never include .env, logs, model files or unrelated operator files.
                    for path in sorted(directory.rglob('*.json')):
                        if path == directory / 'backup-manifest.json':
                            continue
                        if path.is_symlink() or not path.resolve().is_relative_to(directory):
                            raise ValueError('Veri dizininde sembolik bağlantı bulundu; yedek durduruldu.')
                        archive.write(path, path.relative_to(directory).as_posix())
                    archive.writestr('backup-manifest.json', json.dumps({
                        'format': 'portfolio25-storage-v1',
                        'created_at': datetime.now(timezone.utc).isoformat(),
                        'consistency': 'SQLite backup API; project files require a maintenance window',
                    }))
        except Exception:
            destination.close()
            output.unlink(missing_ok=True)
            raise
    return output


def restore(archive_path, data_dir):
    directory = Path(data_dir).resolve()
    if directory.exists() and (not directory.is_dir() or any(directory.iterdir())):
        raise ValueError('Geri yükleme yalnız boş/yeni veri dizinine yapılır. Mevcut kayıtların üzerine yazılmadı.')
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory.parent, prefix='portfolio25-restore-') as temp:
        staging = Path(temp) / 'data'
        staging.mkdir(mode=0o700)
        with zipfile.ZipFile(archive_path) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or 'accounts.sqlite3' not in names or 'backup-manifest.json' not in names:
                raise ValueError('Geçersiz yedek içeriği.')
            manifest = json.loads(archive.read('backup-manifest.json'))
            if manifest.get('format') != 'portfolio25-storage-v1':
                raise ValueError('Desteklenmeyen yedek biçimi.')
            for name in names:
                part = PurePosixPath(name)
                if part.is_absolute() or '..' in part.parts or '\\' in name or ':' in name or name.endswith('/'):
                    raise ValueError('Güvenli olmayan yedek yolu.')
                if name == 'backup-manifest.json':
                    continue
                if name != 'accounts.sqlite3' and not name.endswith('.json'):
                    raise ValueError('Desteklenmeyen yedek dosyası.')
                target = staging.joinpath(*part.parts)
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with target.open('xb') as stream:
                    private_file(target)
                    with archive.open(name) as source:
                        shutil.copyfileobj(source, stream)
        with connect_existing(staging / 'accounts.sqlite3') as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('SQLite bütünlük doğrulaması başarısız.')
            # A backup must not reactivate previously revoked sessions.
            db.execute('DELETE FROM sessions')
            db.execute('DELETE FROM attempts')
            db.commit()
            db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        # No overwrite, including if another process populated it during validation.
        if directory.exists():
            directory.rmdir()  # raises if it is no longer empty
        staging.rename(directory)


def reset_password(data_dir, email, password):
    _, database = existing_database(data_dir)
    if not 12 <= len(password) <= 128:
        raise ValueError('Yeni parola 12–128 karakter olmalı.')
    from auth import Credentials, hasher
    credentials = Credentials(email=email, password=password)
    with connect_existing(database) as db:
        row = db.execute('SELECT id FROM users WHERE email=?', (credentials.email,)).fetchone()
        if not row:
            raise ValueError('Bu veritabanında hesap bulunamadı. Parola sıfırlanmadı; yeni hesap oluşturulmadı.')
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (hasher.hash(password), row[0]))
        db.execute('DELETE FROM sessions WHERE user_id=?', (row[0],))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('backup')
    p.add_argument('--data-dir', required=True)
    p.add_argument('--output', required=True)
    p = commands.add_parser('restore')
    p.add_argument('--archive', required=True)
    p.add_argument('--data-dir', required=True)
    p = commands.add_parser('reset-password')
    p.add_argument('--data-dir', required=True)
    p.add_argument('--email', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'backup':
            backup(args.data_dir, args.output)
            print('Özel yedek oluşturuldu. Git’e veya herkese açık dizine koymayın.')
        elif args.command == 'restore':
            restore(args.archive, args.data_dir)
            print('Kayıtlar geri yüklendi. Önceki oturumlar iptal edildi; kullanıcılar yeniden giriş yapmalı.')
        else:
            password = getpass.getpass('Yeni parola (gizli): ')
            if password != getpass.getpass('Yeni parola tekrar (gizli): '):
                raise ValueError('Parolalar eşleşmiyor; hiçbir kayıt değiştirilmedi.')
            reset_password(args.data_dir, args.email, password)
            print('Mevcut hesabın parolası yenilendi; hesabın eski oturumları iptal edildi. Projeler korunur.')
    except (ValueError, OSError, sqlite3.Error, zipfile.BadZipFile):
        # Do not leak DB paths, contents, credentials or internal SQL through tracebacks.
        parser.exit(1, 'İşlem tamamlanamadı: mevcut veritabanını, boş hedefi, dosya izinlerini ve yedek biçimini kontrol edin. Hesap bulunamıyorsa yedek gerekir.\n')


if __name__ == '__main__':
    main()
