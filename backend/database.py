from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database configuration - Using local SQLite database
DATABASE_URL = "sqlite:///./bitcoin_generator.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

class BitcoinAddress(Base):
    """Model for storing generated Bitcoin addresses"""
    __tablename__ = "bitcoin_addresses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    address = Column(String(100), nullable=False, index=True)
    private_key = Column(Text, nullable=False)  # WIF format
    address_type = Column(String(20), nullable=False, index=True)  # p2pkh, p2sh-p2wpkh, p2wpkh, p2tr
    pattern = Column(String(50), nullable=True, index=True)  # Search pattern if any
    position = Column(String(10), nullable=True)  # start, middle, end
    attempts = Column(Integer, nullable=True)  # Number of attempts to find pattern
    generation_source = Column(String(20), nullable=False, default='backend')  # backend or frontend
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BitcoinAddress(id={self.id}, address='{self.address[:10]}...', type='{self.address_type}')>"

def get_db():
    """Dependency to get database session"""
    try:
        db = SessionLocal()
        yield db
    except Exception as e:
        print(f"Database session error: {e}")
        # Return a mock session that does nothing if database is unavailable
        yield None
    finally:
        try:
            if 'db' in locals():
                db.close()
        except:
            pass

def create_tables():
    """Create all tables in the database"""
    try:
        # SQLite will automatically create the database file if it doesn't exist
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
        
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            # Simple test query for SQLite
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            print("Database connection successful")
            return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection and create tables
    if test_connection():
        create_tables()
    else:
        print("Failed to connect to database")