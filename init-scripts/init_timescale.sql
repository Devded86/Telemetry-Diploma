-- Активація розширення часових рядів всередині PostgreSQL
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Створення структури таблиці з коректними типами даних
CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    device_id VARCHAR(50),
    product_weight_g FLOAT, -- Виправлено на FLOAT
    metal_signal INT,
    threshold INT,
    temperature FLOAT,      -- Виправлено на FLOAT
    is_rejected BOOLEAN,
    status VARCHAR(20),
    PRIMARY KEY (id, timestamp) -- Для TimescaleDB ключ має включати timestamp
);

-- Перетворюємо таблицю на високонавантажену Hypertable за полем timestamp
SELECT create_hypertable('telemetry', 'timestamp', if_not_exists => TRUE, chunk_time_interval => INTERVAL '7 days');