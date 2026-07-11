"""Standalone manual updater for proj_dashboard.

Double-click this (or its compiled proj_dash_installer.exe) from inside the
same folder as proj_dash.exe. It fetches the latest GitHub release, stops the
running app if needed, and overwrites only the exe/templates/static files
that actually changed. instance/app.db and instance/backups/ are never
touched — the release zip never contains them.

Run standalone; do not import Flask/db modules here so this stays a tiny,
independent PyInstaller build.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.updater import API_LATEST_RELEASE, ASSET_NAME, _changed_files, _sha256  # noqa: E402

EXE_NAME = 'proj_dash.exe'


def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _stop_running_app():
    try:
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {EXE_NAME}'],
                                capture_output=True, text=True)
        running = EXE_NAME in result.stdout
    except Exception:
        running = False
    if running:
        subprocess.run(['taskkill', '/IM', EXE_NAME, '/F'], capture_output=True)
        time.sleep(2)
    return running


def _copy_changed(changed, src_dir, dst_dir):
    for rel in changed:
        src = os.path.join(src_dir, rel)
        dst = os.path.join(dst_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def main():
    app_dir = _app_dir()
    print('proj_dashboard 手動安裝更新程式')
    print(f'應用程式資料夾：{app_dir}')
    print('正在查詢最新版本...')

    req = urllib.request.Request(
        API_LATEST_RELEASE,
        headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'proj_dash-installer'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception as e:
        print(f'查詢失敗：{e}')
        input('按 Enter 結束...')
        return

    asset = next((a for a in data.get('assets', []) if a.get('name') == ASSET_NAME), None)
    if not asset:
        print('目前的 GitHub Release 沒有附加更新包，無法安裝。')
        input('按 Enter 結束...')
        return

    latest_version = data.get('tag_name', '').lstrip('vV')
    print(f'找到版本 v{latest_version}，開始下載...')

    stage_dir = tempfile.mkdtemp(prefix='proj_dash_installer_')
    try:
        zip_path = os.path.join(stage_dir, 'update.zip')
        urllib.request.urlretrieve(asset['browser_download_url'], zip_path)

        extract_dir = os.path.join(stage_dir, 'extracted')
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        new_exe = os.path.join(extract_dir, EXE_NAME)
        if not os.path.exists(new_exe):
            print('更新包內找不到 proj_dash.exe，已取消。')
            input('按 Enter 結束...')
            return

        current_exe = os.path.join(app_dir, EXE_NAME)
        tpl_src = os.path.join(extract_dir, 'templates')
        static_src = os.path.join(extract_dir, 'static')
        tpl_dst = os.path.join(app_dir, 'templates')
        static_dst = os.path.join(app_dir, 'static')

        was_running = _stop_running_app()

        exe_changed = not os.path.exists(current_exe) or _sha256(new_exe) != _sha256(current_exe)
        changed_templates = _changed_files(tpl_src, tpl_dst) if os.path.exists(tpl_src) else []
        changed_static = _changed_files(static_src, static_dst) if os.path.exists(static_src) else []

        print(f'需要更新：exe={"是" if exe_changed else "否（已是最新）"}，'
              f'templates {len(changed_templates)} 個檔案，static {len(changed_static)} 個檔案')
        print('（instance/app.db 與 instance/backups 不會被更動）')

        if exe_changed:
            if os.path.exists(current_exe):
                bak = current_exe + '.bak'
                if os.path.exists(bak):
                    os.remove(bak)
                shutil.move(current_exe, bak)
            shutil.move(new_exe, current_exe)

        _copy_changed(changed_templates, tpl_src, tpl_dst)
        _copy_changed(changed_static, static_src, static_dst)

        print(f'已更新到 v{latest_version}！')
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)

    if was_running:
        print('正在重新啟動主程式...')
        subprocess.Popen([current_exe], cwd=app_dir)

    input('按 Enter 結束...')


if __name__ == '__main__':
    main()
