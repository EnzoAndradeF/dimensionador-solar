import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Lê a URL do PostgreSQL das variáveis de ambiente (Docker/Production)
# Fallback local padronizado para PostgreSQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://solar_user:solar_password@localhost:5432/dimensionador_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()