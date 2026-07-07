import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile

GITHUB_REPO = 'neilyonglu/proj_dashboard'
ASSET_NAME = 'proj_dash_update.zip'
API_LATEST_RELEASE = f'https://api.github.com/repos/{GITHUB_REPO}/releases/latest'
REQUEST_TIMEOUT = 6
CACHE_SECONDS = 6 * 3600

_cache = {'checked_at': None, 'result': None}


def _version_tuple(v):
    v = (v or '').strip().lstrip('vV')
    parts = []
    for p in v.split('.'):
        digits = ''.join(ch for ch in p if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_update(current_version, force=False):
    """Return dict describing the latest GitHub release vs current_version.
    Cached for CACHE_SECONDS to avoid hammering the GitHub API. Never raises —
    network/API failures come back as {'available': False, 'error': ...}."""
    now = time.time()
    if not force and _cache['result'] is not None and \
            now - _cache['checked_at'] < CACHE_SECONDS:
        return _cache['result']

    try:
        req = urllib.request.Request(
            API_LATEST_RELEASE,
            headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'proj_dash-updater'}
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.load(resp)
        latest_version = data.get('tag_name', '').lstrip('vV')
        asset = next((a for a in data.get('assets', []) if a.get('name') == ASSET_NAME), None)
        if asset and _version_tuple(latest_version) > _version_tuple(current_version):
            result = {
                'available': True,
                'latest_version': latest_version,
                'download_url': asset['browser_download_url'],
                'html_url': data.get('html_url'),
                'notes': data.get('body', ''),
            }
        else:
            result = {'available': False, 'latest_version': latest_version}
    except Exception as e:
        result = {'available': False, 'error': str(e)}

    _cache['checked_at'] = now
    _cache['result'] = result
    return result


def perform_self_update(download_url, application_path):
    """Download the release zip (exe + templates/ + static/), then spawn a
    detached relauncher .bat that waits for this process to exit, swaps the
    files, and restarts the exe. Only valid inside a PyInstaller build."""
    if not getattr(sys, 'frozen', False):
        raise RuntimeError('自我更新僅支援封裝後的 exe，開發模式請直接 git pull。')

    stage_dir = tempfile.mkdtemp(prefix='proj_dash_update_')
    zip_path = os.path.join(stage_dir, 'update.zip')
    urllib.request.urlretrieve(download_url, zip_path)

    extract_dir = os.path.join(stage_dir, 'extracted')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)

    new_exe = os.path.join(extract_dir, 'proj_dash.exe')
    if not os.path.exists(new_exe):
        raise RuntimeError('更新檔內找不到 proj_dash.exe，已取消更新。')

    current_exe = sys.executable
    tpl_src = os.path.join(extract_dir, 'templates')
    static_src = os.path.join(extract_dir, 'static')

    bat_path = os.path.join(stage_dir, 'apply_update.bat')
    with open(bat_path, 'w') as f:
        f.write(f'''@echo off
setlocal
set "EXE={current_exe}"
set "NEWEXE={new_exe}"
set "TPL_SRC={tpl_src}"
set "STATIC_SRC={static_src}"
set "APP_DIR={application_path}"
set "STAGE={stage_dir}"
set "TRIES=0"

:retry
set /a TRIES+=1
if exist "%EXE%.bak" del /Q "%EXE%.bak" >nul 2>&1
move /Y "%EXE%" "%EXE%.bak" >nul 2>&1
if errorlevel 1 (
    if %TRIES% GEQ 30 goto giveup
    timeout /t 1 /nobreak >nul
    goto retry
)

move /Y "%NEWEXE%" "%EXE%" >nul
if exist "%TPL_SRC%" xcopy /Y /E /I /Q "%TPL_SRC%" "%APP_DIR%\\templates\\" >nul
if exist "%STATIC_SRC%" xcopy /Y /E /I /Q "%STATIC_SRC%" "%APP_DIR%\\static\\" >nul
start "" "%EXE%"
goto cleanup

:giveup
start "" "%EXE%"

:cleanup
rmdir /S /Q "%STAGE%" >nul 2>&1
(goto) 2>nul & del "%~f0"
''')

    subprocess.Popen(
        ['cmd.exe', '/c', bat_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
