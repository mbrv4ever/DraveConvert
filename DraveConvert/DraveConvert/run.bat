@echo off
setlocal
cd /d "%~dp0"
set "PYEXE="
set "PYW="
for %%V in (3.13 3.12 3.11 3.10) do (
  if not defined PYEXE (
    py -%%V -c "import sys" >nul 2>&1 && ( set "PYEXE=py -%%V" & set "PYW=pyw -%%V" )
  )
)
if not defined PYEXE (
  python -c "import sys" >nul 2>&1 && ( set "PYEXE=python" & set "PYW=pythonw" )
)
if not defined PYEXE (
  echo Python 3.10 t/m 3.13 niet gevonden. Installeer Python van https://www.python.org/downloads/
  pause
  exit /b 1
)
%PYEXE% -c "import PyQt6, PIL" >nul 2>&1
if errorlevel 1 (
  echo Benodigdheden installeren, een moment...
  %PYEXE% -m pip install --upgrade pip
  %PYEXE% -m pip install --only-binary=:all: -r requirements.txt
)
%PYW% app.py
endlocal
