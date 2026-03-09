import os
import requests
from fastapi import FastAPI, File, UploadFile
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# 1. Veritabanı Modeli (Frankfurt PostgreSQL)
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

# Tabloları Otomatik Oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 Pl@ntNet API Ayarları (Sadece Bilimsel İsim)
PLANET_API_KEY = "2b10IuE06X6U6T6E6f6P6o6R6n" 
PLANET_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANET_API_KEY}"

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Frankfurt Bulut Hattı Aktif! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        # Fotoğrafı Oku
        contents = await file.read()
        files = [('images', (file.filename, contents))]
        data = {'organs': ['leaf']} 

        # API Soteleme
        response = requests.post(PLANET_URL, files=files, data=data)
        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            # Sadece Bilimsel İsim Alıyoruz (En Sağlamı)
            scientific_name = best["species"]["scientificNameWithoutAuthor"]
            score = float(best["score"])
            
            # 🗄️ Veritabanına Kaydet
            yeni_kayit = TaramaGecmisi(
                bitki_adi=scientific_name, 
                guven_orani=score
            )
            db.add(yeni_kayit)
            db.commit()
            
            # Flutter'ın beklediği "scientific_name" anahtarıyla gönderiyoruz
            return {
                "scientific_name": scientific_name,
                "score": score,
                "status": "Success"
            }
        
        return {"scientific_name": "Bilinmeyen Tür", "score": 0.0, "status": "Fail"}

    except Exception as e:
        print(f"Hata: {str(e)}")
        return {"scientific_name": "Bağlantı Hatası", "score": 0.0, "status": "Error"}
    finally:
        db.close()

@app.get("/history")
async def get_history():
    db = SessionLocal()
    try:
        # Geçmişteki son 20 taramayı getir
        history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
        return history
    finally:
        db.close()

# 🚀 Render Deployment Ayarı
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
