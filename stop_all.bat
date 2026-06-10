@echo off
cd /d C:\Users\khoir\Downloads\youtube-auto-clip

echo Menghentikan Telegram Bot dan Web Streamlit...

taskkill /FI "WindowTitle eq Telegram Bot*" /F >nul 2>&1
taskkill /FI "WindowTitle eq Streamlit Web*" /F >nul 2>&1

echo.
echo ✅ Semua proses sudah dimatikan.
echo.
pause