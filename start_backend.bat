Set-Content -Path .\start_backend.bat -Value @'
@echo off
cd /d D:\BANTY\student-performance-prediction-system
call venv\Scripts\activate.bat
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
pause
'@