from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 🎯 POOLER CONNECTION (6543 Portu - IPv4 Uyumlu)
# Not: Kullanıcı adındaki noktaya ve portun 6543 olduğuna dikkat reis!
SQLALCHEMY_DATABASE_URL = "postgresql://postgres.qqkyjsafhevywgdaywvk:Eomer3255..@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres?pgbouncer=true"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
