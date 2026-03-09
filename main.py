import os
import requests
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base, engine, SessionLocal

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Veritabanı Modeli
class TaramaGecmisi(Base):
    __tablename__ = "taramalar"
    id = Column(Integer, primary_key=True, index=True)
    bitki_adi = Column(String)
    guven_orani = Column(Float)
    tarih = DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS ayarı (Flutter'dan erişim için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎯 DÜZELTİLMİŞ Pl@ntNet API Ayarları
PLANET_API_KEY = os.environ.get("PLANTNET_API_KEY", "2b10mlep2lyP5fp2wfjE3LUxe")
# ❌ BOŞLUK YOK! 
PLANET_URL = "https://my-api.plantnet.org/v2/identify/all"

@app.get("/")
async def root():
    return {"mesaj": "Green Lens Pro: Frankfurt Bulut Hattı Aktif! 🚀"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        # Dosya kontrolü
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "Sadece resim dosyası yükleyin!")
        
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(400, "Dosya çok büyük! Max 10MB")

        # 🎯 DÜZELTİLMİŞ API İsteği
        files = [('images', (file.filename, contents, file.content_type))]
        data = {'organs': ['auto']}  # 'auto' daha iyi sonuç verir
        
        params = {
            'api-key': PLANET_API_KEY,  # Query parametre olarak gönder
            'include-related-images': 'false',
            'no-reject': 'false',
            'lang': 'tr',
            'page': '1'
        }

        logger.info(f"API isteği gönderiliyor: {PLANET_URL}")
        
        response = requests.post(
            PLANET_URL,
            files=files,
            data=data,
            params=params,  # API key burada!
            timeout=30
        )
        
        logger.info(f"API Yanıt Kodu: {response.status_code}")
        
        # Hata kontrolü
        if response.status_code != 200:
            error_detail = response.text
            logger.error(f"API Hatası: {response.status_code} - {error_detail}")
            raise HTTPException(500, f"PlantNet API Hatası: {error_detail}")

        result_data = response.json()
        logger.info(f"API Yanıtı: {result_data}")

        if "results" in result_data and len(result_data["results"]) > 0:
            best = result_data["results"][0]
            
            # Güvenli veri erişimi
            species = best.get("species", {})
            scientific_name = species.get("scientificNameWithoutAuthor") or species.get("scientificName", "Bilinmeyen")
            common_names = species.get("commonNames", [])
            score = float(best.get("score", 0))
            
            # Veritabanına kaydet
            yeni_kayit = TaramaGecmisi(
                bitki_adi=scientific_name,
                guven_orani=score
            )
            db.add(yeni_kayit)
            db.commit()
            
            return {
                "scientific_name": scientific_name,
                "common_names": common_names,
                "score": round(score, 4),
                "status": "Success",
                "family": species.get("family", {}).get("scientificName", "Bilinmiyor")
            }
        
        return {
            "scientific_name": "Tanımlanamadı",
            "score": 0.0,
            "status": "NoResults",
            "message": "Bitki bulunamadı, daha net fotoğraf çekin"
        }

    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Bağlantı Hatası: {str(e)}")
        raise HTTPException(503, f"PlantNet API'ye bağlanılamadı: {str(e)}")
    except Exception as e:
        logger.error(f"Beklenmeyen Hata: {str(e)}")
        db.rollback()
        raise HTTPException(500, f"Sunucu Hatası: {str(e)}")
    finally:
        db.close()

@app.get("/history")
async def get_history():
    db = SessionLocal()
    try:
        history = db.query(TaramaGecmisi).order_by(TaramaGecmisi.tarih.desc()).limit(20).all()
        return [
            {
                "id": h.id,
                "bitki_adi": h.bitki_adi,
                "guven_orani": h.guven_orani,
                "tarih": h.tarih.isoformat() if h.tarih else None
            }
            for h in history
        ]
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
