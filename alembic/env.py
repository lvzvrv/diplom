import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Импортируем Base из нашего приложения
from app.models.base import Base

# Этот блок нужен для Alembic
config = context.config

# Настраиваем логгирование
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Добавляем модели для автогенерации
target_metadata = Base.metadata

# Получаем URL из переменных окружения
def get_url():
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME')

    if not all([user, password, dbname]):
        raise ValueError(
            "Не хватает переменных окружения для подключения к БД. "
            "Проверьте DB_USER, DB_PASSWORD и DB_NAME в файле .env"
        )

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()