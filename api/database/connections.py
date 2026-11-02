"""Database connection and session management."""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from ..config.settings import settings

logger = logging.getLogger(__name__)

# PostgreSQL Configuration
postgresql_engine = None
postgresql_session_factory = None
PostgresBase = declarative_base()

def create_postgresql_engine():
    """Create PostgreSQL engine with proper configuration."""
    global postgresql_engine, postgresql_session_factory
    
    try:
        postgresql_engine = create_engine(
            settings.POSTGRESQL_URL,
            poolclass=StaticPool,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG,
            echo_pool=settings.DEBUG,
            pool_size=10,
            max_overflow=20
        )
        
        postgresql_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=postgresql_engine
        )
        
        logger.info("PostgreSQL engine created successfully")
        return postgresql_engine
        
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL engine: {e}")
        raise


def get_postgresql_session() -> Generator[Session, None, None]:
    """Get PostgreSQL database session."""
    global postgresql_session_factory
    
    if postgresql_session_factory is None:
        create_postgresql_engine()
    
    session = postgresql_session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_postgresql():
    """Initialize PostgreSQL database tables."""
    try:
        if postgresql_engine is None:
            create_postgresql_engine()
        
        # Import all models to ensure they are registered
        from ..models.database import ValidationLogDB, APIKeyDB, ThreatIntelDB, CachedResultDB
        
        # Create all tables
        PostgresBase.metadata.create_all(bind=postgresql_engine)
        logger.info("PostgreSQL tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL: {e}")
        raise


def close_postgresql():
    """Close PostgreSQL database connections."""
    global postgresql_engine
    if postgresql_engine:
        postgresql_engine.dispose()
        logger.info("PostgreSQL connections closed")


# MongoDB Configuration
mongodb_client = None
mongodb_db = None

def create_mongodb_connection():
    """Create MongoDB connection."""
    global mongodb_client, mongodb_db
    
    try:
        from pymongo import MongoClient
        
        mongodb_client = MongoClient(settings.MONGODB_URL)
        mongodb_db = mongodb_client[settings.MONGODB_DATABASE]
        
        # Test connection
        mongodb_client.admin.command('ping')
        
        logger.info("MongoDB connection established successfully")
        return mongodb_client
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


def get_mongodb_database():
    """Get MongoDB database instance."""
    global mongodb_db
    
    if mongodb_db is None:
        create_mongodb_connection()
    
    return mongodb_db


def get_mongodb_collection(collection_name: str):
    """Get MongoDB collection."""
    db = get_mongodb_database()
    return db[collection_name]


def init_mongodb():
    """Initialize MongoDB collections and indexes."""
    try:
        if mongodb_client is None:
            create_mongodb_connection()
        
        # Create indexes for common collections
        threat_intel_collection = get_mongodb_collection("threat_intelligence")
        threat_intel_collection.create_index([("indicator", 1)], unique=True)
        threat_intel_collection.create_index([("indicator_type", 1)])
        threat_intel_collection.create_index([("last_seen", -1)])
        
        validation_logs_collection = get_mongodb_collection("validation_logs")
        validation_logs_collection.create_index([("timestamp", -1)])
        validation_logs_collection.create_index([("api_key", 1)])
        validation_logs_collection.create_index([("endpoint", 1)])
        
        cache_collection = get_mongodb_collection("cache")
        cache_collection.create_index([("expires_at", 1)], expireAfterSeconds=0)
        cache_collection.create_index([("cache_key", 1)], unique=True)
        
        logger.info("MongoDB collections and indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise


def close_mongodb():
    """Close MongoDB connection."""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")


# Database initialization
def init_databases():
    """Initialize all database connections."""
    try:
        init_postgresql()
        init_mongodb()
        logger.info("All databases initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize databases: {e}")
        raise


def close_databases():
    """Close all database connections."""
    try:
        close_postgresql()
        close_mongodb()
        logger.info("All database connections closed")
    except Exception as e:
        logger.error(f"Failed to close database connections: {e}")
        raise


# Health check functions
def check_postgresql_health() -> dict:
    """Check PostgreSQL database health."""
    try:
        with get_postgresql_session() as session:
            session.execute("SELECT 1")
            return {
                "status": "healthy",
                "message": "PostgreSQL is responding"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"PostgreSQL error: {str(e)}"
        }


def check_mongodb_health() -> dict:
    """Check MongoDB database health."""
    try:
        if mongodb_client is None:
            create_mongodb_connection()
        
        mongodb_client.admin.command('ping')
        return {
            "status": "healthy",
            "message": "MongoDB is responding"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"MongoDB error: {str(e)}"
        }