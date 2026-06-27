import os
from datetime import datetime

MAX_LOG_ENTRIES = 2000  # entries per file before rotating


def _get_log_dir():
    from flask import current_app
    base = current_app.config.get('DB_INSTANCE_DIR', 'instance')
    log_dir = os.path.join(base, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _current_log_path(log_dir):
    prefix = datetime.now().strftime('%Y%m')
    try:
        files = sorted([
            f for f in os.listdir(log_dir)
            if f.startswith(f'activity_{prefix}_') and f.endswith('.log')
        ])
    except OSError:
        files = []

    if files:
        current_file = os.path.join(log_dir, files[-1])
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                count = sum(1 for line in f if line.strip())
            if count < MAX_LOG_ENTRIES:
                return current_file
        except OSError:
            pass

    n = len(files) + 1
    return os.path.join(log_dir, f'activity_{prefix}_{n:03d}.log')


def log_action(ip: str, action: str, detail: str = '') -> None:
    """Write one log entry. Never raises — logging must not break the app."""
    try:
        log_dir = _get_log_dir()
        path = _current_log_path(log_dir)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        detail_str = f' | {detail}' if detail else ''
        line = f'[{ts}] {ip} | {action}{detail_str}\n'
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line)
    except Exception:
        pass
