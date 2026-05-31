from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Якщо Docker з якоїсь причини не прокинув змінну, беремо залізобетонний дефолтний шлях
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin_password@db:5432/telemetry")

engine = create_engine(DATABASE_URL)

Base = declarative_base()          

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()