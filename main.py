import os
from fastapi import FastAPI, File, UploadFile
import requests
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# 1. Veritabanı Tablo Yapısı (Aynı kalıyor, Frankfurt hattı aktif)
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    bakim_notu = Column(String)
    tarih = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 SINIRSIZ API AYARLARI (Pl@ntNet)
# Not: Kendi API key'ini buraya yapıştır reis
PLANET_API_KEY = "2b10IuE06X6U6T6E6f6P6o6R6n" 
PLANET_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANET_API_KEY}"

# Gelişmiş Bilgi Bankası
PLANT_INFO = {
    "Punica granatum": {"tr": "Nar", "bakim": "Güneşli yerleri sever, toprağı kurudukça sula."},
    "Schefflera": {"tr": "Beşparmak Otu", "bakim": "Aydınlık ama direkt güneş almayan yer sever."},
    "Default": {"tr": "Bilinmeyen Tür", "bakim": "Düzenli kontrol et, fazla sudan kaçın."}
}

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Pl@ntNet Sınırsız Motor Aktif! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        contents = await file.read()
        files = [('images', (file.filename, contents))]
        data = {'organs': ['leaf']} 

        # Pl@ntNet API Çağrısı
        response = requests.post(PLANET_URL, files=files, data=data)
        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            scientific_name = best["species"]["scientificNameWithoutAuthor"]
            common_names = best["species"].get("commonNames", [])
            
            # 🇹🇷 Türkçe isim varsa al, yoksa bilimsel ismi kullan
            tr_name = common_names[0] if common_names else scientific_name
            score = float(best["score"])
            
            # Veritabanına kaydet
            yeni_kayit = TaramaGecmisi(bitki_adi=scientific_name, guven_orani=score)
            db.add(yeni_kayit)
            db.commit()
            
            return {
                "tr_name": tr_name,     # Flutter'daki karşılığı
                "scientific_name": scientific_name, 
                "score": score,         # Flutter'daki karşılığı
                "status": "Success"
            }
        
        return {"tr_name": "Bilinmeyen Bitki", "score": 0.0, "status": "Fail"}

    except Exception as e:
        return {"tr_name": "Hata Oluştu", "score": 0.0, "status": "Error", "detail": str(e)}
    finally:
        db.close()

@app.get("/history")
async def get_history():
    db = SessionLocal()
    try:
        history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
        return history
    finally:
        db.close()

# 🚀 Render için Port Ayarı (Full Online için şart!)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

