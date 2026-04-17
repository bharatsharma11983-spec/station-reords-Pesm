@echo off
echo ========================================
echo PESMOS Station GUI - FINAL VERSION
echo ========================================
echo.
echo [1] Station Data GUI
echo [2] Station Map GUI
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    python station_data_gui.py
    goto end
)
if "%choice%"=="2" (
    python station_map_gui.py
    goto end
)
echo Invalid choice
pause
exit /b 1

:end
echo.
echo Done!
pause