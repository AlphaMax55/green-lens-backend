from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🎯 SUPABASE SESSION POOLER (Sydney Hattı)
# Şifren olan 'Eomer3255..' başarıyla mühürlendi.
# Render'ın IPv4 üzerinden ulaşabilmesi için bu adres şarttı reis.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.qqkyjsafhevywgdaywvk:Eomer3255..@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
