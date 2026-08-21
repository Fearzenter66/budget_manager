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