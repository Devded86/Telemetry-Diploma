@echo off
chcp 65001 > nul
echo 🚀 Запуск дипломного комплексу (FastAPI, TimescaleDB, Grafana, Simulator)...

docker compose up -d

start "" "http://localhost:8000/"
start "" "http://localhost:3000/"