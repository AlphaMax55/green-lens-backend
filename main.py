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
        # 1. Resmi Pl@ntNet'e gönderilecek formata hazırla
        # Kindwise gibi Base64 istemez, direkt dosya (binary) göndeririz.
        contents = await file.read()
        files = [('images', (file.filename, contents))]
        
        # 🎯 KRİTİK AYAR: Organ belirtmezsek Pl@ntNet "0" döner!
        data = {'organs': ['leaf']} 

        # 2. Pl@ntNet API'ye Soteleme
        response = requests.post(PLANET_URL, files=files, data=data)
        result_data = response.json()

        # 3. Sonuçları İşle
        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            scientific_name = best["species"]["scientificNameWithoutAuthor"]
            score = float(best["score"])
            
            # Türkçe isim ve bakım notu eşleştirme
            # (Haftaya bunu tamamen otomatik veritabanından çekeceğiz)
            info = PLANT_INFO.get(scientific_name, PLANT_INFO["Default"])
            tr_name = info["tr"]
            
            # 4. BULUTA KAYDET (Frankfurt PostgreSQL)
            yeni_kayit = TaramaGecmisi(
                bitki_adi=scientific_name,
                guven_orani=score,
                bakim_notu=info["bakim"]
            )
            db.add(yeni_kayit)
            db.commit()
            
            return {
                "name": scientific_name,
                "tr_name": tr_name,
                "score": score,
                "care": info["bakim"],
                "status": "Success"
            }
        
        return {"error": "Bitki tanımlanamadı (0 sonuç)", "status": "Fail"}

    except Exception as e:
        print(f"🔥 Hata Detayı: {str(e)}")
        return {"error": str(e), "status": "Error"}
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
