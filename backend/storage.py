"""Explicit PostgreSQL production storage; never silently fall back to local files."""
from pathlib import Path
from postgres_store import DatabaseUnavailable, get_store


def storage_status(data_file: Path) -> dict:
    try:
        store = get_store()
        if store is not None:
            store.health()
            return {'status':'postgresql','required':True,'message':'PostgreSQL bağlantısı ve şema sürümü doğrulandı. Eski hesabın varlığı bu kontrolle doğrulanmaz.'}
        return {'status':'local','required':False,'message':'Yerel SQLite/JSON geliştirme deposu; bulut kalıcılığı iddiası yok.'}
    except DatabaseUnavailable:
        return {'status':'unavailable','required':True,'message':'PostgreSQL erişimi veya şeması hazır değil. Yerel dosyalara geri dönülmedi.'}


def check_storage(data_file: Path) -> None:
    # Validate the choice/configuration; actual operations check pooled connections.
    get_store()
