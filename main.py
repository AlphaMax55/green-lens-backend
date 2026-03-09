import os
from fastapi import FastAPI, File, UploadFile
import requests
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# 1. Veritabanı Tablosu (Frankfurt PostgreSQL)
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
app = FastAPI()

# 🎯 SINIRSIZ API VE TÜRKÇE DİL DESTEĞİ
PLANET_API_KEY = "2b10IuE06X6U6T6E6f6P6o6R6n" 
# URL'ye &lang=tr ekleyerek Türkçe isimleri aktif ediyoruz
PLANET_URL = f"https://my-api.plantnet.org/v2/identify/all?api-key={PLANET_API_KEY}"

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Full Online Devri Başladı! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        contents = await file.read()
        files = [('images', (file.filename, contents))]
        data = {'organs': ['leaf']} 

        # Pl@ntNet API Sotelemesi
        response = requests.post(PLANET_URL, files=files, data=data)
        result_data = response.json()

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            scientific_name = best["species"]["scientificNameWithoutAuthor"]
            
            # 🇹🇷 API'den gelen Türkçe ismi yakalıyoruz
            common_names = best["species"].get("commonNames", [])
            tr_name = common_names[0] if common_names else scientific_name
            
            score = float(best["score"])
            
            # 🗄️ BULUTA KAYDET
            yeni_kayit = TaramaGecmisi(
                bitki_adi=scientific_name,
                guven_orani=score
            )
            db.add(yeni_kayit)
            db.commit()
            
            # 🚀 FLUTTER'IN BEKLEDİĞİ DEĞİŞKENLERİ GÖNDERİYORUZ
            return {
                "tr_name": tr_name,           # Flutter bunu bekliyor
                "scientific_name": scientific_name, # Flutter bunu bekliyor
                "score": score,               # Flutter bunu bekliyor
                "status": "Success"
            }
        
        return {"tr_name": "Bitki Tanınamadı", "score": 0.0, "status": "Fail"}

    except Exception as e:
        return {"tr_name": "Bağlantı Hatası", "score": 0.0, "status": "Error", "detail": str(e)}
    finally:
        db.close()

@app.get("/history")
async def get_history():
    db = SessionLocal()
    try:
        # Geçmişi tarihe göre sıralayıp getiriyoruz
        history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
        return history
    finally:
        db.close()

# Render Port Ayarı
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


