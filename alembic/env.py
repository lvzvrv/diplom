from logging.config import fileConfig
from sqlalchemy import create_engine
from alembic import context
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Импортируем Base из вашего приложения
from app.database import Base
from app.models.user import User  # Импортируем все модели
# from app.models.album import Album  # Раскомментируйте для других моделей

config = context.config
fileConfig(config.config_file_name)
print("Таблицы в Base.metadata:", list(Base.metadata.tables.keys()))
target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()