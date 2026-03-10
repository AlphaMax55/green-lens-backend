import requests
from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal, get_db

# --- 1. Veritabanı Modeli ---
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 🎯 iNaturalist Gizli Kapısı ---
# Senin keşfettiğin o nokta atışı URL
INAT_URL = "https://api.inaturalist.org/v1/computervision/score_image"

@app.get("/")
async def root():
    return {"mesaj": "iNaturalist Frankfurt Hattı Zırhlı Modda Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()

        files = {
            'image': (file.filename, contents, file.content_type)
        }

        data = {
            "iconic_taxa": "Plantae"
        }

        headers = {
            'User-Agent': 'GreenLensPro/1.0'
        }

        response = requests.post(
            INAT_URL,
            files=files,
            data=data,
            headers=headers,
            timeout=30
        )

        result_data = response.json()
        results = result_data.get("results", [])

        if results:
            best = results[0]
            taxon = best.get("taxon", {})

            plant_name = (
                taxon.get("preferred_common_name")
                or taxon.get("name")
                or "Bilinmeyen Tür"
            )

            score = float(best.get("score", 0))

            yeni_kayit = TaramaGecmisi(
                bitki_adi=plant_name,
                guven_orani=score
            )

            db.add(yeni_kayit)
            db.commit()

            return {
                "scientific_name": plant_name,
                "score": score,
                "status": "Success"
            }

        return {"scientific_name": "Tanınamadı", "score": 0.0, "status": "Fail"}

    except Exception as e:
        return {"scientific_name": "Sunucu Hatası", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()

