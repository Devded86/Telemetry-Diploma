import time
import requests
import random
import os
from datetime import datetime

API_URL = os.getenv("API_URL", "http://localhost:8000/ingest")
CONFIG_URL = os.getenv("CONFIG_URL", "http://localhost:8000/api/config")

print("⚙️ Імітатор промислової лінії конвеєра та металодетекції запущено...")

# Статична ініціалізація фізичного стану двигуна (реалістичний старт)
if not hasattr(time, 'current_engine_temp'):
    time.current_engine_temp = 27.0

while True:
    current_threshold = 80
    temp_threshold = 32
    
    # 1. Зчитуємо конфігурацію обох каналів з сервера
    try:
        config_response = requests.get(CONFIG_URL, timeout=1)
        if config_response.status_code == 200:
            config_data = config_response.json()
            current_threshold = config_data.get("threshold", 80)
            temp_threshold = config_data.get("temp_threshold", 32)
    except Exception:
        pass

    # 2. ГЕНЕРАЦІЯ ТЕЛЕМЕТРІЇ
    weight = round(random.normalvariate(500, 4), 1)
    
    # Симуляція реального теплового балансу редуктора
    # Раз на кілька хвилин конвеєр зазнає підвищеного навантаження, нагріваючись до 34°C
    is_line_heavy = (int(time.time()) % 180) > 100
    target_temp = 34.2 if is_line_heavy else 29.5
    
    # Модель теплової інерції (плавне наближення + випадкові коливання)
    time.current_engine_temp += (target_temp - time.current_engine_temp) * 0.015 + random.uniform(-0.08, 0.08)
    temperature = round(time.current_engine_temp, 1)
    
    # Генерація металевої стружки
    if random.random() < 0.03:
        metal_signal = random.randint(int(current_threshold) + 5, int(current_threshold) + 40)
    else:
        metal_signal = random.randint(15, 45)

    payload = {
        "device_id": "Cintex_Autosearch_II",
        "product_weight_g": weight,
        "metal_signal": metal_signal,
        "temperature": temperature
    }

    # 3. ВІДПРАВКА ДАНИХ
    try:
        response = requests.post(API_URL, json=payload, timeout=2)
        if response.status_code == 200:
            result = response.json()
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if result.get("is_rejected"):
                print(f"🚨 [{timestamp}] БРАК МЕТАЛУ! Сигнал: {metal_signal} (Ліміт: {current_threshold})")
            elif temperature > temp_threshold:
                print(f"⚠️ [{timestamp}] ТРИВОГА ПЕРЕГРІВУ! Т: {temperature}°C (Ліміт: {temp_threshold}°C)")
            else:
                print(f"✅ [{timestamp}] Лінія в нормі. Вага: {weight}г | Т: {temperature}°C")
        else:
            print("[❌] Помилка прийому пакета сервером")
    except Exception as e:
        print(f"[📡] Очікування зв'язку з FastAPI сервером...")

    time.sleep(2)