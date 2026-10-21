# This module defines the database configuration and connection management for the payment API service.
# It sets up SQLAlchemy engine, session management, and provides database connection utilities.

from sqlalchemy import create_engine  # SQLAlchemy engine for database connections
from sqlalchemy.ext.declarative import declarative_base  # Base class for ORM models
from sqlalchemy.orm import sessionmaker, scoped_session  # Session management for database operations
from decouple import config  # Environment variable management
import os  # Operating system interface for environment variables

# Construct database URL from environment variables
# Supports multiple database engines (MySQL, PostgreSQL, SQLite, etc.)
SQLALCHEMY_DATABASE_URL = "{}://{}:{}@{}:{}/{}".format(
    config("DB_ENGINE", default="sqlite"),  # Database engine (mysql, postgresql, sqlite)
    config("MYSQL_USER", default=str(os.getenv("MYSQL_USER"))),  # Database username
    config("MYSQL_PASSWORD", default=str(os.getenv("MYSQL_PASSWORD"))),  # Database password
    config("MYSQL_URL", default=str(os.getenv("MYSQL_URL"))),  # Database host URL
    config("MYSQL_PORT", default=str(os.getenv("MYSQL_PORT"))),  # Database port
    config("MYSQL_DB", default=str(os.getenv("MYSQL_DB"))),  # Database name
)

# Create SQLAlchemy engine with connection pooling and health checks
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=5,  # Number of connections to maintain in the pool
    pool_pre_ping=True,  # Verify connections before use
    isolation_level="READ COMMITTED",  # Transaction isolation level
)

# Create session factory and scoped session for thread-safe database operations
SessionLocal = sessionmaker(bind=engine)
SessionLocal = scoped_session(SessionLocal)  # Thread-local session management
Base = declarative_base()  # Base class for all ORM models


def get_db():
    """
    Dependency function for FastAPI to provide database sessions.
    
    Creates a new database session for each request and ensures proper cleanup.
    This function is used as a dependency in FastAPI route handlers.
    
    Yields:
        Session: SQLAlchemy database session
        
    Note:
        The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()  # Ensure session is closed
        engine.dispose()  # Clean up engine resources
