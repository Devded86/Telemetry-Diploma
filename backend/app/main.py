from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import time

from . import models, database

app = FastAPI(title="Telemetry Monitoring System")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(BASE_DIR, "..", "templates")
if not os.path.exists(templates_path):
    templates_path = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=templates_path)

# Глобальні змінні конфігурації Edge-контролера
CURRENT_THRESHOLD = 80
CURRENT_TEMP_THRESHOLD = 32  # Дефолтний ліміт температури

@app.on_event("startup")
def startup_db():
    print("⏳ Перевірка зв'язку з TimescaleDB...")
    retries = 10
    while retries > 0:
        try:
            models.Base.metadata.create_all(bind=database.engine)
            print("✅ База даних успішно підключена, структури створено!")
            break
        except Exception as e:
            retries -= 1
            print(f"⚠️ База ще не готова. Спроб залишилось: {retries}. Чекаємо 3 секунди...")
            time.sleep(3)

@app.get("/", response_class=HTMLResponse)
def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "current_threshold": CURRENT_THRESHOLD,
        "current_temp_threshold": CURRENT_TEMP_THRESHOLD
    })

@app.post("/update_threshold")
def update_threshold(threshold: int = Form(...), temp_threshold: int = Form(...)):
    global CURRENT_THRESHOLD, CURRENT_TEMP_THRESHOLD
    CURRENT_THRESHOLD = threshold
    CURRENT_TEMP_THRESHOLD = temp_threshold
    return RedirectResponse(url="/", status_code=303)

@app.get("/api/config")
def get_config():
    return {
        "threshold": CURRENT_THRESHOLD,
        "temp_threshold": CURRENT_TEMP_THRESHOLD
    }

@app.post("/ingest")
def ingest_telemetry(data: dict, db: Session = Depends(database.get_db)):
    global CURRENT_THRESHOLD, CURRENT_TEMP_THRESHOLD
    
    weight = data.get("product_weight_g", 500.0)
    metal = data.get("metal_signal", 20)
    temp = data.get("temperature", 22.0)
    
    is_rejected = False
    status = "normal"
    
    # 1. Перевірка на сторонній метал (Критичний брак продукту)
    if metal > CURRENT_THRESHOLD:
        is_rejected = True
        status = "anomaly_metal"
        alert = models.SystemAlert(
            alert_type="METAL_DETECTED",
            message="Знайдено сторонній метал у пакеті!",
            value=float(metal)
        )
        db.add(alert)
        
    # 2. Динамічна перевірка перегріву за порогом оператора (Брак заліза)
    elif temp > CURRENT_TEMP_THRESHOLD:
        status = "overheating"
        alert = models.SystemAlert(
            alert_type="OVERHEATING",
            message=f"Критичний перегрів редуктора конвеєра (> {CURRENT_TEMP_THRESHOLD}°C)!",
            value=float(temp)
        )
        db.add(alert)

    telemetry_entry = models.Telemetry(
        product_weight_g=weight,
        metal_signal=metal,
        threshold=CURRENT_THRESHOLD,
        temperature=temp,
        is_rejected=is_rejected,
        status=status
    )
    db.add(telemetry_entry)
    db.commit()
    
    return {"status": "success", "is_rejected": is_rejected}

@app.get("/api/live_data")
def get_live_data(db: Session = Depends(database.get_db)):
    telemetry = db.query(models.Telemetry).order_by(models.Telemetry.timestamp.desc()).limit(10).all()
    alerts = db.query(models.SystemAlert).order_by(models.SystemAlert.timestamp.desc()).limit(5).all()
    
    total_count = db.query(models.Telemetry).count()
    # Тепер у брак рахуємо і метал, і перегрів приводу
    rejected_count = db.query(models.Telemetry).filter(
        (models.Telemetry.is_rejected == True) | (models.Telemetry.status == "overheating")
    ).count()
    normal_count = total_count - rejected_count
    
    return {
        "telemetry": telemetry, 
        "alerts": alerts,
        "stats": {
            "total": total_count,
            "normal": normal_count,
            "rejected": rejected_count
        }
    }