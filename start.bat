@echo off

call .\Scripts\Activate.bat

start "" waitress-serve --listen=127.0.0.1:5002 app:app

timeout /t 1 /nobreak >nul

start http://127.0.0.1:5002/

pause
