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
INAT_URL = "https://api.inaturalist.org/v1/computervision/score"

@app.get("/")
async def root():
    return {"mesaj": "iNaturalist Frankfurt Hattı Güven Skoruyla Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Fotoğrafı oku
        contents = await file.read()
        
        # iNaturalist'in en sevdiği format: multipart/form-data
        files = {'image': (file.filename, contents, 'image/jpeg')}
        
        # 🚀 İstek atarken timeout (zaman aşımı) ekliyoruz ki sistem asılı kalmasın
        response = requests.post(INAT_URL, files=files, timeout=20)
        
        # Eğer cevap 200 değilse (hata varsa) direkt burada yakalayalım
        if response.status_code != 200:
            print(f"iNaturalist Hatası: {response.status_code} - {response.text}")
            return {"scientific_name": "API Hatası", "score": 0.0, "status": "Error"}

        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            taxon = best.get("taxon", {})
            
            # İsim ve Skor ayıklama
            plant_name = taxon.get("preferred_common_name") or taxon.get("name") or "Bilinmeyen Tür"
            raw_score = best.get("vision_score") or best.get("combined_score") or 0.0
            score = float(raw_score) / 100 if raw_score > 1 else float(raw_score)
            
            # Frankfurt Veritabanına Kayıt
            try:
                yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
                db.add(yeni_kayit)
                db.commit()
            except:
                db.rollback() # Veritabanı hatası olsa bile sonucu döndür

            return {"scientific_name": plant_name, "score": score, "status": "Success"}
        
        return {"scientific_name": "Bitki Tanınamadı", "score": 0.0, "status": "Fail"}

    except requests.exceptions.RequestException as e:
        print(f"Bağlantı Hatası: {str(e)}")
        return {"scientific_name": "Hatta Sorun Var", "score": 0.0, "status": "Error"}
    except Exception as e:
        print(f"Genel Hata: {str(e)}")
        return {"scientific_name": "Sunucu Hatası", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()

