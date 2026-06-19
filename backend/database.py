# backend/database.py
# This file creates the connection between FastAPI and PostgreSQL.
# Think of it as the "phone line" between your Python code and your database.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load the .env file so we can read DATABASE_URL
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# create_engine = opens a connection pool to PostgreSQL
# (like opening multiple phone lines so many requests can be handled at once)
engine = create_engine(DATABASE_URL)

# SessionLocal = a factory that creates new DB sessions on demand
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = the parent class all your ORM models will inherit from
Base = declarative_base()

# get_db = a FastAPI "dependency" — routes call this to get a DB session
# The try/finally ensures the session is always closed after the request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()