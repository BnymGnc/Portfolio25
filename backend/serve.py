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
    uvicorn.run('main:app', host='0.0.0.0', port=platform_port(), workers=1)


if __name__ == '__main__':
    serve()
