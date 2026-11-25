import os
import subprocess
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contur.settings")


def wait_for_db(timeout=60):
    import psycopg

    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            with psycopg.connect(
                host=os.environ["DB_HOST"],
                port=os.environ.get("DB_PORT", "5432"),
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                connect_timeout=3,
            ) as conn:
                conn.execute("SELECT 1")
            return
        except Exception as exc:
            last_error = exc
            print("Waiting for database...", flush=True)
            time.sleep(2)
    raise RuntimeError(f"Database is not ready: {last_error}") from last_error


def main():
    wait_for_db()
    subprocess.check_call([sys.executable, "manage.py", "migrate", "--noinput"])
    subprocess.check_call([sys.executable, "manage.py", "collectstatic", "--noinput"])

    workers = os.environ.get("GUNICORN_WORKERS", "3")
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
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
        ],
    )


if __name__ == "__main__":
    main()
