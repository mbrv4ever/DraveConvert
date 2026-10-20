@echo off
setlocal
cd /d "%~dp0"
echo DraveConvert.exe bouwen met PyInstaller...
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
%PYEXE% -m pip install --only-binary=:all: -r requirements.txt
%PYEXE% -m pip install pyinstaller
%PYEXE% -m PyInstaller --noconfirm app.spec
echo.
echo Klaar. De exe staat in de map dist\DraveConvert\
pause
endlocal
