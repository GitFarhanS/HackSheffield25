"""
Database connection and session management for PostgreSQL.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/styleswipe"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """
    Dependency function to get database session.
    Use this in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Call this on application startup.
    """
    # Import models to register them with Base
    try:
        from backend.models import (
            User, UserImage, Preference, Product, Swipe, LikedProduct, ProductClick
        )
    except ImportError:
        from models import (
            User, UserImage, Preference, Product, Swipe, LikedProduct, ProductClick
        )
    Base.metadata.create_all(bind=engine)

