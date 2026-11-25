import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contur.settings")


def _env(name, default=None):
    value = os.environ.get(name, default)
    if isinstance(value, str):
        return value.strip().strip("'\"")
    return value


def db_host():
    host = _env("DB_HOST", "localhost")
    if Path("/.dockerenv").exists() and host in {"localhost", "127.0.0.1"}:
        print("DB_HOST=localhost inside Docker, using host 'db'", flush=True)
        return "db"
    return host


def wait_for_db(timeout=60):
    import psycopg

    host = db_host()
    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with psycopg.connect(
                host=host,
                port=_env("DB_PORT", "5432"),
                dbname=_env("DB_NAME"),
                user=_env("DB_USER"),
                password=_env("DB_PASSWORD"),
                connect_timeout=3,
            ) as conn:
                conn.execute("SELECT 1")
            print(f"Database is ready at {host}", flush=True)
            return
        except Exception as exc:
            last_error = exc
            print(f"Waiting for database at {host}: {exc}", flush=True)
            time.sleep(2)
    raise RuntimeError(f"Database is not ready: {last_error}") from last_error


def main():
    wait_for_db()
    subprocess.check_call([sys.executable, "manage.py", "migrate", "--noinput"])
    subprocess.check_call([sys.executable, "manage.py", "collectstatic", "--noinput"])

    workers = os.environ.get("GUNICORN_WORKERS", "2")
    bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "contur.wsgi:application",
            "--bind",
            bind,
            "--workers",
            workers,
            "--timeout",
            "30",
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
        ],
    )


if __name__ == "__main__":
    main()
