"""DB configuration"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator
from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve the environment variables
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")


# Create the engine using environment variables
engine = create_engine(
    f"mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{"192.168.0.12"}:{DB_PORT}/{DB_NAME}",
    echo=True,  # Set to True to see SQL statements being executed, False to disable
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_db_tables():
    """create all tables"""
    SQLModel.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
