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
        contents = await file.read()
        files = {'image': (file.filename, contents, 'image/jpeg')}
        
        # 🚀 iNaturalist'e soruyoruz
        response = requests.post(INAT_URL, files=files)
        result_data = response.json()

        # Loglarda detayları görelim
        print(f"iNaturalist Ham Yanit: {result_data}")

        if "results" in result_data and len(result_data["results"]) > 0:
            # En iyi sonucu alıyoruz
            best = result_data["results"][0]
            taxon = best.get("taxon", {})
            
            # 🏷️ İsim Ayıklama
            # Önce varsa Türkçe/Yaygın ismini, yoksa bilimsel ismini alıyoruz
            plant_name = taxon.get("preferred_common_name") or taxon.get("name") or "Bilinmeyen Tür"
            
            # 📈 Güven Skoru (0 ile 1 arası bir değer döner, örn: 0.94)
            # iNaturalist'te bu bazen 'vision_score' bazen 'combined_score' olarak gelir
            raw_score = best.get("vision_score") or best.get("combined_score") or 0.0
            
            # Skoru 0-1 aralığına normalize edelim (Bazen 100 üzerinden gelebilir)
            score = float(raw_score) / 100 if raw_score > 1 else float(raw_score)
            
            # 🗄️ Frankfurt Veritabanına Kaydet
            yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
            db.add(yeni_kayit)
            db.commit()
            
            # Flutter tarafındaki 'scientific_name' ve 'score' ile tam uyumlu
            return {
                "scientific_name": plant_name, 
                "score": score, 
                "status": "Success"
            }
        
        return {"scientific_name": "Tanınamadı", "score": 0.0, "status": "Fail"}

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {"scientific_name": "Bağlantı Hatası", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
