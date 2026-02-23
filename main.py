from fastapi import FastAPI, File, UploadFile
import requests
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# 1. Veritabanı Tablo Yapısını Oluştur (Hafıza)
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    bakim_notu = Column(String)
    tarih = Column(DateTime, default=datetime.utcnow)

# Frankfurt'taki veritabanında tabloyu oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI()

API_KEY = "2b10mlep2lyP5fp2wfjE3LUxe"

# Bitki Bilgi Bankası
PLANT_INFO = {
    "Papatya": {"bakim": "Haftada 2 kez sula.", "gunes": "Doğrudan güneş sever.", "uyari": "Toprağı kurudukça su ver."},
    "Orkide": {"bakim": "10 günde bir daldırma sulama yap.", "gunes": "Yarı gölge sever.", "uyari": "Yapraklarına su değdirme."},
    "Default": {"bakim": "Düzenli kontrol et.", "gunes": "Aydınlık ortam.", "uyari": "Fazla sudan kaçın."}
}

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Bulut Backend Aktif! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        # 1. Resmi PlantNet'e gönder
        image_data = await file.read()
        url = f"https://my-api.plantnet.org/v2/identify/all?api-key={API_KEY}"
        files = {'images': (file.filename, image_data)}
        
        response = requests.post(url, files=files)
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            best = data["results"][0]
            sci_name = best["species"]["scientificNameWithoutAuthor"]
            name = best["species"]["commonNames"][0] if best["species"]["commonNames"] else sci_name
            
            info = PLANT_INFO.get(name, PLANT_INFO["Default"])
            
            # 2. BULUTA KAYDET: Frankfurt'taki veritabanına yazıyoruz
            yeni_kayit = TaramaGecmisi(
                bitki_adi=name,
                guven_orani=float(best["score"]),
                bakim_notu=info["bakim"]
            )
            db.add(yeni_kayit)
            db.commit()
            
            return {
                "name": name,
                "score": best["score"],
                "care": info["bakim"],
                "sun": info["gunes"],
                "warning": info["uyari"]
            }
        
        return {"name": "Bilinmeyen Bitki", "score": 0, "care": "-", "sun": "-", "warning": "-"}

    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
        
@app.get("/history")
async def get_history():
    db = SessionLocal()
    try:
        # Son 20 taramayı tarihe göre tersten getiriyoruz
        history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
        return history
    finally:
        db.close()       