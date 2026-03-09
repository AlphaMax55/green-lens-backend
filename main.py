import os
import requests
from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal, get_db

# 1. Veritabanı Modeli
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

# 🚀 Frankfurt Hattında Tabloları Otomatik Oluşturur
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 API Anahtarını Koyeb'den güvenli çeker
PLANET_API_KEY = os.getenv("PLANTNET_API_KEY", "2b10mlep2lyP5fp2wfjE3LUxe") 
PLANET_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANET_API_KEY}"

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Frankfurt Hattı Aktif! 🚀 PC'yi Kapatabilirsin Reis."}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        files = [('images', (file.filename, contents))]
        data = {'organs': ['leaf']} 

        response = requests.post(PLANET_URL, files=files, data=data)
        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            scientific_name = best["species"]["scientificNameWithoutAuthor"]
            score = float(best["score"])
            
            # 🗄️ Yeni Frankfurt Veritabanına Kaydet
            yeni_kayit = TaramaGecmisi(bitki_adi=scientific_name, guven_orani=score)
            db.add(yeni_kayit)
            db.commit()
            
            return {"scientific_name": scientific_name, "score": score, "status": "Success"}
        
        return {"scientific_name": "Bilinmeyen Tür", "score": 0.0, "status": "Fail"}

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {"scientific_name": "Bağlantı Hatası", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    # Geçmişteki son 20 taramayı Frankfurt'tan çeker
    history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
    return history
