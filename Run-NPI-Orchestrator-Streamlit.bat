@echo off
title NPI Orchestrator - Streamlit
cd /d "%~dp0"
echo Starting NPI Orchestrator in your browser...
echo Close this window to stop the server (or press Ctrl+C in the server log).
python -m streamlit run streamlit_npi.py
if errorlevel 1 pause
exit /b %ERRORLEVEL%
