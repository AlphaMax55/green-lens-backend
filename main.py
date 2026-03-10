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

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 iNaturalist Görüntü Tanıma Adresi
INAT_URL = "https://api.inaturalist.org/v1/identifications"

@app.get("/")
async def root():
    return {"mesaj": "iNaturalist Frankfurt Hattı Güven Skoruyla Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        
        # 🧪 iNaturalist'in istediği tam paket
        files = {'image': (file.filename, contents, 'image/jpeg')}
        
        # 🛡️ Boş parametreleri eklemezsek bazen 422 veya 400 hatası verebilir
        data = {
            'observation_id': '',
            'geomodel': 'true'
        }

        # 🚀 Headers ekleyerek gerçek bir tarayıcı gibi davranıyoruz
        headers = {
            'User-Agent': 'GreenLensPro/1.0 (Kastamonu University Student Project)'
        }

        response = requests.post(INAT_URL, files=files, data=data, headers=headers, timeout=25)

        # 🔍 Hatayı Loglarda Kabak Gibi Görelim
        if response.status_code != 200:
            print(f"--- iNaturalist KRITIK HATA ---")
            print(f"Kod: {response.status_code}")
            print(f"Mesaj: {response.text}")
            return {"scientific_name": f"Hata: {response.status_code}", "score": 0.0, "status": "Error"}

        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            taxon = best.get("taxon", {})
            
            # En iyi ismi yakala
            plant_name = taxon.get("preferred_common_name") or taxon.get("name") or "Bilinmeyen Tür"
            raw_score = best.get("vision_score") or best.get("combined_score") or 0.0
            score = float(raw_score) / 100 if raw_score > 1 else float(raw_score)
            
            # 🗄️ Veritabanı Kaydı
            try:
                yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
                db.add(yeni_kayit)
                db.commit()
            except:
                db.rollback()

            return {"scientific_name": plant_name, "score": score, "status": "Success"}
        
        return {"scientific_name": "Bitki Tanınamadı", "score": 0.0, "status": "Fail"}

    except Exception as e:
        print(f"Sistem Hatası: {str(e)}")
        return {"scientific_name": "Sunucu Meşgul", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()



