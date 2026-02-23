from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Senin Render External URL'in
SQLALCHEMY_DATABASE_URL = "postgresql://omer:aUicMYRCDfvEaj31J1uFfemBUfC3pcWb@dpg-d6ecsd08tnhs73emu65g-a.frankfurt-postgres.render.com/green_lens"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()