from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🎯 SUPABASE FINAL CONNECTION (Sydney Line)
# Şifren olan 'Eomer3255..' başarıyla yerleştirildi.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Eomer3255..@db.qqkyjsafhevywgdaywvk.supabase.co:5432/postgres"

# Not: Şifredeki noktalar (.) sorun çıkarırsa SQLAlchemy otomatik halleder, 
# ancak bağlantı hatası alırsan burayı 'Eomer3255%2E%2E' olarak güncelleriz.
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
