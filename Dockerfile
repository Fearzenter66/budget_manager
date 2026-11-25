FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY contur/ .
COPY docker/entrypoint.py /entrypoint.py

RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/staticfiles \
    && chown -R appuser:appuser /app /entrypoint.py

USER appuser

EXPOSE 8000

ENTRYPOINT ["python", "/entrypoint.py"]
