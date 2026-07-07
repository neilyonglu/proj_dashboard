@echo off
echo Starting build process...

REM Run PyInstaller via conda proj_dash env
conda run -n proj_dash pyinstaller --onefile --name "proj_dash" app.py

REM Move the built exe to the project root
if exist dist\proj_dash.exe (
    move /Y dist\proj_dash.exe proj_dash.exe
    echo Build completed! The executable is proj_dash.exe

    REM Package exe + templates + static for GitHub Release (used by in-app auto-update)
    if exist proj_dash_update.zip del /Q proj_dash_update.zip
    powershell -NoProfile -Command "Compress-Archive -Path 'proj_dash.exe','templates','static' -DestinationPath 'proj_dash_update.zip' -Force"
    echo Release asset ready: proj_dash_update.zip (upload this to the GitHub Release)
) else (
    echo Build failed.
)

REM Clean up PyInstaller artifacts
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist proj_dash.spec del /Q proj_dash.spec

