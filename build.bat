@echo off
echo Starting build process...

REM Run PyInstaller from the project root so the core/ package is included
pyinstaller --onefile --name "proj_dash" app.py

REM Move the built exe to the project root
if exist dist\proj_dash.exe (
    move /Y dist\proj_dash.exe proj_dash.exe
    echo Build completed! The executable is proj_dash.exe
) else (
    echo Build failed.
)

REM Clean up PyInstaller artifacts
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build

pause
