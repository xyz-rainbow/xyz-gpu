@echo off
cls
setlocal enabledelayedexpansion

:: Forzar soporte de secuencias de escape ANSI en la consola de Windows
reg add "HKCU\Console" /v VirtualTerminalLevel /t REG_DWORD /d 1 /f >nul 2>&1

title XYZ-GPU CLUSTER MANAGER
cd /d "%~dp0"

:: Verificar si python está en el PATH
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERR] Python no está instalado o no se encuentra en el PATH.
    echo Por favor, instala Python e inténtalo de nuevo.
    pause
    exit /b 1
)

:: Ejecutar script de orquestacion interactiva
python install_gpu.py
if %errorlevel% neq 0 (
    echo.
    echo [ERR] Hubo un problema al ejecutar el script de control.
    pause
)
