# RUNBOOK — proj_dashboard

Canonical, previously-working commands. **Copy verbatim; do not improvise variants.**
If an operation you need is missing and took you >1 attempt to get right, append the
working command here in the same session (see global rule 3).

All PowerShell below is Windows PowerShell 5.1: no `&&`, no `?:`; chain with `;`.
Paths verified to exist on 2026-07-06:
`C:\Users\Neil\miniconda3\Scripts\conda.exe` and
`C:\Users\Neil\miniconda3\envs\proj_dash\python.exe`.

## Start the app

Foreground (blocks — use the run-in-background option of the shell tool):

```powershell
conda run -n proj_dash python app.py
```

Detached (survives the tool call; use when you need the server up for smoke tests):

```powershell
$conda = "C:\Users\Neil\miniconda3\Scripts\conda.exe"; Start-Process -FilePath $conda -ArgumentList "run -n proj_dash python app.py" -WorkingDirectory "C:\Users\Neil\project\dad_projects\proj_dashboard" -WindowStyle Hidden; Start-Sleep -Seconds 5
```

If `conda` is not on PATH, always use the full exe path as above.
App URL: http://localhost:5001

## Port 5001 — check and free (DO THIS FIRST when startup "silently fails")

The app exits silently if port 5001 is already bound. Check who holds it:

```powershell
Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; Write-Output ("PID {0} : {1}" -f $_.OwningProcess, $p.ProcessName) }
```

Kill the stale holder (only if it is a python/proj_dash process):

```powershell
Get-NetTCPConnection -LocalPort 5001 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

## Smoke test (run after ANY route or template change)

One command, all key pages. Extend the list when you add pages; keep it ONE command.

```powershell
$pages = @("/", "/timeline", "/employee-case", "/overtime-stats", "/add-project", "/add-task", "/api/check-update"); foreach ($p in $pages) { try { $r = Invoke-WebRequest -Uri "http://localhost:5001$p" -UseBasicParsing -TimeoutSec 5; Write-Output "$p -> $($r.StatusCode)" } catch { Write-Output "$p -> FAIL $($_.Exception.Message)" } }
```

To verify a specific template change actually rendered, grep the page for a marker
you added, e.g.:

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:5001/employee-case" -UseBasicParsing; if ($r.Content -match "YOUR_MARKER") { "marker OK" } else { "MISSING" }
```

A template edit is NOT verified until a real GET shows the marker.

## Syntax check without starting the app

`conda run` intermittently fails with "conda not recognized" in this shell — use
the env's python directly (verified working 2026-07-07):

```powershell
& "C:\Users\Neil\miniconda3\envs\proj_dash\python.exe" -c "import ast; ast.parse(open('app.py',encoding='utf-8').read()); print('app.py syntax OK')"
```

## Run a one-off script against the project / DB

Use the env's python directly (avoids conda PATH issues entirely):

```powershell
& "C:\Users\Neil\miniconda3\envs\proj_dash\python.exe" path\to\script.py
```

DB lives at `instance\app.db`; automatic backups in `instance\backups\` (keep 10).
Before any schema experiment, copy `instance\app.db` aside first.

**Trap (cost real data, 2026-07-11):** to test a DB-destructive route (e.g. a
"wipe before import" feature) in isolation, do NOT `from app import app` and then
override `app.config['SQLALCHEMY_DATABASE_URI']` afterward, expecting queries to
use the new path. This project's Flask-SQLAlchemy binds the engine at
`db.init_app(app)` time (inside `app.py`, at import time) — config changes made
after that are silently ignored by `Model.query`, so ORM reads/writes still hit
the REAL `instance/app.db` even though plain-file-path helpers (like
`backup_database()`, which re-reads `current_app.config['DB_INSTANCE_DIR']` live)
correctly honor the override. This split made a test look isolated while it
actually deleted 171 real rows from the live task table.
Safe alternative: copy `instance\app.db` aside FIRST (always, no exceptions,
even for "isolated" tests), then either (a) test pure Python helper functions
directly against a copy via raw `sqlite3`/a fresh throwaway `Flask`+`SQLAlchemy()`
app object that's never touched the real one, or (b) accept that testing through
the real `app` object means you're on the real DB and restore from the pre-test
copy afterward regardless of whether the test "looked" isolated.

## Build the exe

```powershell
cmd.exe /c build.bat
```

If invoked as `cmd.exe /c "cd /d <path> && build.bat"` from the PowerShell tool,
it can fail with `'build.bat' is not recognized` even though the file exists and
`cd /d <path> && dir build.bat` succeeds (verified 2026-07-11). Use the absolute
path instead, after `Set-Location` to the project root:

```powershell
& cmd.exe /c "C:\Users\Neil\project\dad_projects\proj_dashboard\build.bat"
```

`build.bat` calls `python.exe -m PyInstaller` directly (not `conda run`, which was
observed to silently drop the rest of the script after a long build) but manually
prepends the env's `Library\bin` etc. to PATH first — without that, PyInstaller
can't find `libffi` and the built exe crashes instantly with `ImportError: DLL
load failed while importing _ctypes` (no window, no console output unless you
redirect stdout yourself; verified 2026-07-11). After any change to `build.bat`'s
PyInstaller invocation, verify the exe isn't just "file exists" but actually
boots — run it and hit a real page, since a broken build silently produces a
same-shaped exe that just crashes on start:

```powershell
cmd.exe /c "cd /d C:\Users\Neil\project\dad_projects\proj_dashboard && start /B proj_dash.exe > exe_test.log 2>&1"
Start-Sleep -Seconds 6
Get-Content "C:\Users\Neil\project\dad_projects\proj_dashboard\exe_test.log"
Invoke-WebRequest -Uri "http://localhost:5001/" -UseBasicParsing
```

`build.bat` already calls conda internally (commit a16a578) and deletes the .spec.
Output `proj_dash.exe` must sit next to `templates\` and `static\` to run.
It also produces `proj_dash_update.zip` (exe + templates + static) — upload this
as the GitHub Release asset so the in-app "一鍵更新" can find it (README "發布新版本").

## Known traps (Windows / this project)

- PowerShell 5.1: no `&&` — use `;` or `if ($?) { ... }`.
- `Out-File`/`Set-Content` default to UTF-16 — always pass `-Encoding utf8` for
  files other tools will read.
- The Bash tool is Git Bash (POSIX). Never put PowerShell cmdlets in it.
- Port 5001 taken → app exits with NO error message. Check the port first.
- No global node/npm; all Python tooling lives inside the `proj_dash` conda env.
