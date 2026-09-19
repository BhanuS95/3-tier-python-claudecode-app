"""
Local development entrypoint.

DO NOT use this in production -- the Flask dev server is single
threaded, unsafe, and not designed to handle production traffic.
Production uses Gunicorn (see docs/DEVOPS_HANDOVER.md and the
Dockerfile CMD).

Usage:
    python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.config["APP_PORT"], debug=app.config["DEBUG"])
