@echo off
title GMN Muhasebe - Otomatik Baslatici
echo ===================================================
echo   GMN MUHASEBE - ONBELLEK TEMIZLIYOR VE BASLIYOR...
echo ===================================================
echo.

for /d /r %%i in (__pycache__) do (
    if exist "%%i" (
        echo [TEMIZLENIYOR] %%i
        rmdir /s /q "%%i"
    )
)

echo.
echo ===================================================
echo   ONBELLEK TEMIZLENDI! UYGULAMA BASLATILIYOR...
echo ===================================================
echo.

start "" pythonw -B app.py
exit