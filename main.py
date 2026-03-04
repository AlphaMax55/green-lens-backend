from fastapi import FastAPI, File, UploadFile
import requests
import base64
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# 1. Veritabanı Tablo Yapısı
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    bakim_notu = Column(String)
    tarih = Column(DateTime, default=datetime.utcnow)

# Tabloyu oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI()

# 🎯 YENİ API AYARLARI (KINDWISE)
KINDWISE_KEY = "kcI3xPhsvU0tCvFrvwN27TLB7IHf9tj5RcXeUIZnKb8xCYZRRz"
KINDWISE_URL = "https://plant.id/api/v3/identification"

# Bitki Bilgi Bankası (Şimdilik manuel, haftaya otomatikleşecek)
PLANT_INFO = {
    "Daisy": {"bakim": "Haftada 2 kez sula.", "gunes": "Doğrudan güneş sever.", "uyari": "Toprağı kurudukça su ver."},
    "Orchid": {"bakim": "10 günde bir daldırma sulama yap.", "gunes": "Yarı gölge sever.", "uyari": "Yapraklarına su değdirme."},
    "Default": {"bakim": "Düzenli kontrol et.", "gunes": "Aydınlık ortam.", "uyari": "Fazla sudan kaçın."}
}

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Kindwise Gözü Aktif! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        # 1. Resmi oku ve Base64 formatına çevir (Kindwise bunu ister)
        image_data = await file.read()
        base64_image = base64.b64encode(image_data).decode("ascii")
        
        # 2. Kindwise API'ye Gönder
        headers = {"Api-Key": KINDWISE_KEY, "Content-Type": "application/json"}
        payload = {
            "images": [base64_image],
            "latitude": 41.38, # Kastamonu koordinatları (isabeti artırır)
            "longitude": 33.77,
            "similar_images": True
        }
        
        response = requests.post(KINDWISE_URL, json=payload, headers=headers)
        data = response.json()

        # 3. Sonuçları İşle
        if "result" in data and data["result"]["classification"]["suggestions"]:
            best = data["result"]["classification"]["suggestions"][0]
            name = best["name"] # Kindwise İngilizce isim döner
            score = float(best["probability"])
            
            # Veritabanı için bilgi eşleştirme
            info = PLANT_INFO.get(name, PLANT_INFO["Default"])
            
            # 4. BULUTA KAYDET (Frankfurt)
            yeni_kayit = TaramaGecmisi(
                bitki_adi=name,
                guven_orani=score,
                bakim_notu=info["bakim"]
            )
            db.add(yeni_kayit)
            db.commit()
            
            return {
                "name": name,
                "score": score,
                "care": info["bakim"],
                "sun": info["gunes"],
                "warning": info["uyari"]
            }
        
        return {"name": "Bilinmeyen Bitki", "score": 0, "care": "-", "sun": "-", "warning": "-"}

    except Exception as e:
        print(f"Hata Detayı: {str(e)}")
        return {"error": str(e)}
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
