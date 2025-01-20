@echo off

call .\Scripts\Activate.bat

waitress-serve --listen=127.0.0.1:5002 app:app

start http://127.0.0.1:5002/

pause
