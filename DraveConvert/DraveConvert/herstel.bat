@echo off
setlocal
cd /d "%~dp0"
echo DraveConvert herstellen...
set "PYEXE="
for %%V in (3.13 3.12 3.11 3.10) do (
  if not defined PYEXE (
    py -%%V -c "import sys" >nul 2>&1 && set "PYEXE=py -%%V"
  )
)
if not defined PYEXE (
  python -c "import sys" >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
  echo Python niet gevonden.
  pause
  exit /b 1
)
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "DraveConvert-data\app-fout.txt" del /q "DraveConvert-data\app-fout.txt"
echo Benodigdheden opnieuw installeren...
%PYEXE% -m pip install --upgrade pip
%PYEXE% -m pip install --only-binary=:all: --force-reinstall -r requirements.txt
echo Klaar. Je kunt run.bat weer gebruiken.
pause
endlocal
