@echo off
echo Starting build process...

REM 1. Create a temporary folder named proj_dash
if not exist proj_dash mkdir proj_dash

REM 2. Copy app.py to the folder
copy /Y app.py proj_dash\

REM Enter the folder
cd proj_dash

REM 3. Package app.py using pyinstaller (without html/static)
pyinstaller --onefile --name "proj_dash" app.py

REM Move the packaged exe out to the parent directory
move /Y dist\proj_dash.exe ..\proj_dash.exe

REM Go back to the parent directory
cd ..

REM 4. Delete the temporary folder
rmdir /S /Q proj_dash

echo Build completed! The executable is proj_dash.exe
pause
