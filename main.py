import requests
from fastapi import FastAPI, File, UploadFile, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal, get_db

# --- 1. Veritabanı Modeli ---
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 🎯 iNaturalist Gizli Kapısı ---
# Senin keşfettiğin o nokta atışı URL
INAT_URL = "https://api.inaturalist.org/v1/computervision/score_image"

@app.get("/")
async def root():
    return {"mesaj": "iNaturalist Frankfurt Hattı Zırhlı Modda Aktif! 🌿"}

@app.post("/predict")
async def predict(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Fotoğrafı oku
        contents = await file.read()
        files = {'image': (file.filename, contents, 'image/jpeg')}
        
        # iNaturalist bazen lokasyon parametresi de isteyebilir, boş gönderiyoruz
        data = {'latitude': '0', 'longitude': '0'}
        headers = {'User-Agent': 'GreenLensPro/1.0 (Mozilla/5.0)'}

        # 🚀 iNaturalist'e saldırıyoruz
        response = requests.post(INAT_URL, files=files, data=data, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"iNaturalist Hatası: {response.status_code} - {response.text}")
            return {"scientific_name": f"Hata: {response.status_code}", "score": 0.0, "status": "Error"}

        result_data = response.json()
        results = result_data.get("results") or result_data.get("predictions")

        if results and len(results) > 0:
            best = results[0]
            
            # ✅ REİSİN DOKUNUŞU: Taxon kontrolü (Kodun patlamasını engeller)
            if not best.get("taxon"):
                return {"scientific_name": "Takson bulunamadı", "score": 0.0, "status": "Fail"}
            
            taxon = best["taxon"]
            
            # İsim Ayıklama: Varsa Türkçe/Yaygın isim, yoksa Bilimsel isim
            plant_name = taxon.get("preferred_common_name") or taxon.get("name") or "Bilinmeyen Tür"
            
            # Skor Ayıklama ve Normalize Etme (0.0 - 1.0 aralığına)
            raw_score = best.get("vision_score") or best.get("combined_score") or best.get("score") or 0.0
            score = float(raw_score) / 100 if raw_score > 1 else float(raw_score)
            
            # 🗄️ Frankfurt Veritabanına Kayıt
            try:
                yeni_kayit = TaramaGecmisi(bitki_adi=plant_name, guven_orani=score)
                db.add(yeni_kayit)
                db.commit()
            except:
                db.rollback()
            
            return {
                "scientific_name": plant_name, 
                "score": score, 
                "status": "Success"
            }
        
        return {"scientific_name": "Tanınamadı", "score": 0.0, "status": "Fail"}

    except Exception as e:
        print(f"Kritik Hata: {str(e)}")
        return {"scientific_name": "Sunucu Hatası", "score": 0.0, "status": "Error"}

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    return db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
