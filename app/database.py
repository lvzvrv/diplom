from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Подключение к PostgreSQL
DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True, index=True)
    album_title = Column(String(255), nullable=False)
    artist_name = Column(String(255), nullable=False)
    release_date = Column(Date)
    cover_url = Column(String(512))
    genre = Column(String(100))
    created_at = Column(Date, server_default='now()')

# Создание таблицы (выполнить один раз)
def create_tables():
    Base.metadata.create_all(bind=engine)