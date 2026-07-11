@echo off
setlocal

set "CONDA_ENV=C:\Users\Neil\miniconda3\envs\proj_dash"
set "PY=%CONDA_ENV%\python.exe"

REM "conda run -n proj_dash pyinstaller ..." was tried before (commit a16a578)
REM but was observed (2026-07-11) to silently terminate the rest of this batch
REM script after a long-running build, so later steps (zip, cleanup, installer
REM build) never ran. Calling python.exe directly avoids that, but PyInstaller
REM then can't find conda's DLLs (e.g. libffi for _ctypes) unless the env's
REM Library\bin is also on PATH the way "conda activate" would set it up --
REM without this the built exe crashes on startup with "DLL load failed while
REM importing _ctypes" (verified 2026-07-11).
set "PATH=%CONDA_ENV%;%CONDA_ENV%\Library\mingw-w64\bin;%CONDA_ENV%\Library\usr\bin;%CONDA_ENV%\Library\bin;%CONDA_ENV%\Scripts;%CONDA_ENV%\bin;%PATH%"

echo Starting build process...
"%PY%" -m PyInstaller --onefile --name "proj_dash" app.py

if not exist dist\proj_dash.exe goto build_failed
move /Y dist\proj_dash.exe proj_dash.exe
echo Build completed! The executable is proj_dash.exe

REM Package exe + templates + static for GitHub Release (used by in-app auto-update)
if exist proj_dash_update.zip del /Q proj_dash_update.zip
powershell -NoProfile -Command "Compress-Archive -Path 'proj_dash.exe','templates','static' -DestinationPath 'proj_dash_update.zip' -Force"
echo Release asset ready: proj_dash_update.zip (upload this to the GitHub Release)
goto build_done

:build_failed
echo Build failed.

:build_done
REM Clean up PyInstaller artifacts
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist proj_dash.spec del /Q proj_dash.spec

REM Build the standalone manual-update installer (pure stdlib, no Flask deps)
echo Building manual update installer...
"%PY%" -m PyInstaller --onefile --name "proj_dash_installer" tools\installer.py

if not exist dist\proj_dash_installer.exe goto installer_failed
move /Y dist\proj_dash_installer.exe proj_dash_installer.exe
echo Installer ready: proj_dash_installer.exe (upload this to the GitHub Release too)
goto installer_done

:installer_failed
echo Installer build failed.

:installer_done
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist proj_dash_installer.spec del /Q proj_dash_installer.spec
