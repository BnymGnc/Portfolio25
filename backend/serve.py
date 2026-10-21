"""Container entrypoint: platform port, all interfaces, a single persistent writer."""
import os
import uvicorn


def platform_port():
    value = os.environ.get('PORT', '10000')
    try:
        port = int(value)
    except ValueError:
        raise ValueError('PORT must be an integer between 1 and 65535.') from None
    if not 1 <= port <= 65535:
        raise ValueError('PORT must be an integer between 1 and 65535.')
    return port


def serve():
    # Idempotent schema migration; a transient outage must never select SQLite.
    from postgres_store import get_store, DatabaseUnavailable
    try:
        store = get_store()
        if store is not None:
            store.migrate()
    except DatabaseUnavailable:
        print('PostgreSQL hazır değil; sağlık ve hesap istekleri bağlantı düzelene kadar 503 dönecek.', flush=True)
    uvicorn.run('main:app', host='0.0.0.0', port=platform_port(), workers=1)


if __name__ == '__main__':
    serve()
