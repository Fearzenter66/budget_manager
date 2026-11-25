# budget_manager
Програмный комплекс для ведения бюджета

.env
DB_HOST=db_host (localhost)
DB_PORT=db_port 
DB_NAME=db_name
DB_USER=db_user (postgres)
DB_PASSWORD=db_password
DB_ENGINE='django.db.backends.postgresql'
DATABASE_URL=postgresql+asyncpg://db_user:db_password@db_host:db_port/db_password
ALGORITHM=HS256
DATA_KEY=
SECRET_KEY=

setup
python -m venv venv
source ./venv/Scripts.activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Docker (сервер)
1. Установи Docker и Docker Compose.
2. Скопируй проект на сервер вместе с `.env`.
3. В `.env` оставь тот же `DATA_KEY` и `SECRET_KEY`, иначе зашифрованные данные не откроются.
4. Добавь в `.env` IP или домен сервера:

```
ALLOWED_HOSTS=твой.ip.или.домен
CSRF_TRUSTED_ORIGINS=http://твой.ip.или.домен:8000
APP_PORT=8000
```

5. Запуск:

```
docker compose up -d --build
```

Сайт: http://IP_СЕРВЕРА:8000

Создать администратора:

```
docker compose exec web python manage.py createsuperuser
```

Логи: `docker compose logs -f web`
Остановка: `docker compose down`
