@echo off
REM Starts Brainy's local API server. No browser interface is served.
setlocal

set "ROOT=%~dp0"

start "Brainy API" /D "%ROOT%" cmd /k "venv\Scripts\python -m uvicorn brainy.interfaces.api:app --host 127.0.0.1 --port 8000"

endlocal
