import requests
from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, get_db

# --- 1. Veritabanı Tablosunu Tanımlıyoruz ---
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

# Tabloları Frankfurt'taki PostgreSQL'de oluşturuyoruz
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 PlantNet Test Hattı (Key istemez, her zaman açık)
PLANTNET_URL = "https://my-api.plantnet.org/v2/identify/all?api-key=2b10t9agHw2S9R0v0G2EcIOGNe"

@app.get("/")
async def root():
    return {"mesaj": "Frankfurt Hattı PlantNet Üzerinden Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        # PlantNet'in beklediği formatta hazırlıyoruz
        files = [('images', (file.filename, contents, 'image/jpeg'))]
        data = {'organs': ['leaf']} 

        # 🚀 İstek Atılıyor
        response = requests.post(PLANTNET_URL, files=files, data=data, timeout=30)
        
        if response.status_code != 200:
             return {"scientific_name": "Servis Meşgul", "score": 0.0, "status": "Error"}

        result_data = response.json()
        
        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            species = best.get("species", {})
            plant_name = species.get("scientificNameWithoutAuthor") or "Bilinmiyor"
            score = float(best.get("score", 0.0))
            
            # 🗄️ Veritabanına Kayıt Atıyoruz (Hocaya gösterirsin)
            try:
                yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
                db.add(yeni_kayit)
                db.commit()
            except Exception as db_err:
                print(f"DB Kayıt Hatası: {db_err}")
                db.rollback()
            
            return {"scientific_name": plant_name, "score": score, "status": "Success"}
            
        return {"scientific_name": "Tanınamadı", "score": 0.0, "status": "Fail"}
        
    except Exception as e:
        print(f"Genel Hata: {str(e)}")
        return {"scientific_name": "Bağlantı Yok", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
