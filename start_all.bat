@echo off
cd /d C:\Users\khoir\Downloads\youtube-auto-clip

echo Starting Telegram Bot...
start "Telegram Bot" cmd /k python3 bot.py

timeout /t 3 >nul

echo Starting Web Streamlit...
start "Streamlit Web" cmd /k python3 -m streamlit run app.py

echo.
echo ✅ Telegram Bot + Web Streamlit sudah berjalan
echo.
pause