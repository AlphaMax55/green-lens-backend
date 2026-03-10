import os
import requests
from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal, get_db

class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# ✅ Düzeltilmiş URL
INAT_URL = "https://api.inaturalist.org/v1/computervision/score_image"

@app.get("/")
async def root():
    return {"mesaj": "iNaturalist Frankfurt Hattı Güven Skoruyla Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        
        # ✅ Güvenli content-type
        content_type = file.content_type or 'image/jpeg'
        files = {'image': (file.filename, contents, content_type)}
        
        data = {'observation_id': '', 'geomodel': 'true'}
        headers = {'User-Agent': 'GreenLensPro/1.0 (Kastamonu University Student Project)'}

        response = requests.post(
            INAT_URL, 
            files=files, 
            data=data, 
            headers=headers, 
            timeout=30  # ✅ Artırıldı
        )

        if response.status_code != 200:
            print(f"--- iNaturalist HATA ---")
            print(f"Kod: {response.status_code}")
            print(f"Mesaj: {response.text[:500]}")
            return {
                "scientific_name": f"Hata: {response.status_code}", 
                "score": 0.0, 
                "status": "Error"
            }

        result_data = response.json()

        if "results" not in result_data or len(result_data["results"]) == 0:
            return {
                "scientific_name": "Bitki Tanınamadı", 
                "score": 0.0, 
                "status": "Fail"
            }

        best = result_data["results"][0]
        
        # ✅ Takson kontrolü
        if not best.get("taxon"):
            return {
                "scientific_name": "Takson bilgisi yok", 
                "score": 0.0, 
                "status": "Fail"
            }
        
        taxon = best["taxon"]
        plant_name = taxon.get("preferred_common_name") or taxon.get("name") or "Bilinmeyen Tür"
        
        # ✅ Skor düzeltildi (bölme yok!)
        raw_score = best.get("vision_score") or best.get("combined_score") or 0.0
        score = float(raw_score)

        # ✅ Güvenli DB işlemi
        try:
            yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
            db.add(yeni_kayit)
            db.commit()
        except Exception as db_error:
            print(f"DB Hatası: {db_error}")
            db.rollback()
        finally:
            db.close()  # ✅ Kapatma eklendi

        return {
            "scientific_name": plant_name, 
            "score": score, 
            "status": "Success"
        }

    except Exception as e:
        print(f"Sistem Hatası: {str(e)}")
        return {
            "scientific_name": "Sunucu Meşgul", 
            "score": 0.0, 
            "status": "Error"
        }

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    try:
        results = db.query(TaramaGecmisi).order_by(
            TaramaGecmisi.tarih.desc()
        ).limit(20).all()
        return results
    finally:
        db.close()  # ✅ Burada da kapama
