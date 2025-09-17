from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Configuration pour Neon PostgreSQL avec pool de connexions optimisé
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,  # Désactive le pool pour éviter les connexions fermées
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    pool_recycle=300,    # Recycle les connexions après 5 minutes
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
