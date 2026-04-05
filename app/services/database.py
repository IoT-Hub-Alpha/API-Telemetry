import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()
DB_NAME = os.getenv("TELEMETRY_DB_NAME")
DB_USER = os.getenv("TELEMETRY_DB_USER", "postgres")
DB_PASSWORD = os.getenv("TELEMETRY_DB_PASSWORD", "postgres")
DB_HOST = os.getenv("TELEMETRY_DB_HOST")
DB_PORT = int(os.getenv("TELEMETRY_DB_PORT", 5432))
DB_CONNECT_TIMEOUT = int(os.getenv("TELEMETRY_DB_CONNECT_TIMEOUT", 10))

DATABASE_URL = (
    f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
