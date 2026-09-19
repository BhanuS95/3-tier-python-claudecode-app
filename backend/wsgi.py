"""
Production WSGI entrypoint.

Gunicorn is started against this module:

    gunicorn --bind 0.0.0.0:${APP_PORT} --workers 4 \
        --graceful-timeout 30 --timeout 60 wsgi:app

Gunicorn itself translates SIGTERM (sent by Docker/Kubernetes on
container stop / pod termination) into a graceful worker shutdown:
in-flight requests are allowed to finish (up to --graceful-timeout
seconds) before workers exit. No custom signal handling is required
in application code for the standard shutdown path.
"""

from app import create_app

app = create_app()
