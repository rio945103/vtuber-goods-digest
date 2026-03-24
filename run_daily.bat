@echo off
cd /d C:\work\vtuber_goods_digest
if not exist logs mkdir logs
.venv\Scripts\python.exe .\src\main.py >> .\logs\scheduled.log 2>&1
