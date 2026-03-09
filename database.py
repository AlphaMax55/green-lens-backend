import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🎯 Koyeb'deki o DATABASE_URL değişkenini okur
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# ⚠️ ÇOK ÖNEMLİ: Koyeb 'postgres://' verir ama SQLAlchemy 'postgresql://' ister.
# Eğer bu düzeltmeyi yapmazsak sistem asla bağlanmaz.
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Eğer localde çalıştırırsan diye bir güvenlik önlemi (opsiyonel)
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
