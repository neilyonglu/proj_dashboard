import hashlib
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


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _changed_files(src_dir, dst_dir):
    """Relative paths (os.sep-joined) under src_dir whose content differs from
    the corresponding file under dst_dir, or that don't exist there yet."""
    changed = []
    for root, _dirs, files in os.walk(src_dir):
        for name in files:
            src_path = os.path.join(root, name)
            rel = os.path.relpath(src_path, src_dir)
            dst_path = os.path.join(dst_dir, rel)
            if not os.path.exists(dst_path) or _sha256(src_path) != _sha256(dst_path):
                changed.append(rel)
    return changed


def _bat_copy_lines(changed, src_dir, dst_dir):
    lines = []
    for rel in changed:
        src = os.path.join(src_dir, rel)
        dst = os.path.join(dst_dir, rel)
        dst_folder = os.path.dirname(dst)
        lines.append(f'if not exist "{dst_folder}" mkdir "{dst_folder}" >nul 2>&1')
        lines.append(f'copy /Y "{src}" "{dst}" >nul')
    return '\n'.join(lines)


def perform_self_update(download_url, application_path):
    """Download the release zip (exe + templates/ + static/), hash-compare each
    file against what's installed, then spawn a detached relauncher .bat that
    waits for this process to exit and only overwrites the files that actually
    changed (never touches instance/app.db or instance/backups — the zip never
    contains them). Only valid inside a PyInstaller build."""
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
    tpl_dst = os.path.join(application_path, 'templates')
    static_dst = os.path.join(application_path, 'static')

    exe_changed = not os.path.exists(current_exe) or _sha256(new_exe) != _sha256(current_exe)
    changed_templates = _changed_files(tpl_src, tpl_dst) if os.path.exists(tpl_src) else []
    changed_static = _changed_files(static_src, static_dst) if os.path.exists(static_src) else []
    copy_block = '\n'.join(filter(None, [
        _bat_copy_lines(changed_templates, tpl_src, tpl_dst),
        _bat_copy_lines(changed_static, static_src, static_dst),
    ]))

    exe_swap_block = ''
    if exe_changed:
        exe_swap_block = '''
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
goto after_exe
:giveup
goto after_exe
:after_exe
'''
    else:
        exe_swap_block = 'timeout /t 1 /nobreak >nul\n'

    bat_path = os.path.join(stage_dir, 'apply_update.bat')
    with open(bat_path, 'w') as f:
        f.write(f'''@echo off
setlocal
set "EXE={current_exe}"
set "NEWEXE={new_exe}"
set "STAGE={stage_dir}"
{exe_swap_block}
{copy_block}
start "" "%EXE%"

rmdir /S /Q "%STAGE%" >nul 2>&1
(goto) 2>nul & del "%~f0"
''')

    subprocess.Popen(
        ['cmd.exe', '/c', bat_path],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
    )
