@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >NUL 2>NUL
if %errorlevel%==0 (
    py buscar_clientes.py %*
) else (
    python buscar_clientes.py %*
)
echo.
pause
