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

Output `proj_dash.exe` must sit next to `templates\` and `static\` to run. Also
produces `proj_dash_update.zip` (exe+templates+static, for in-app update) and
`proj_dash_installer.exe` (standalone manual installer) — both are release assets.

## Publish a GitHub Release (after `build.bat`)

No `gh` CLI in this environment. Use the GitHub API with the token from the
existing git credential (never echo the token itself):

```bash
TOKEN=$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill | sed -n 's/^password=//p')
```

Building the JSON body: `curl --data-urlencode` mangles Chinese text when the
value comes through PowerShell (console codepage), and Git Bash's `python3` is
a non-functional Windows Store stub (`exit 49`) — always build the JSON with the
conda env's real python, writing to a Windows-style path (`/tmp/...` resolves
to `C:\tmp\...` for a native Windows python.exe and silently fails):

```bash
export REL_BODY="release notes text, may contain 中文"
"/c/Users/Neil/miniconda3/envs/proj_dash/python.exe" -c "
import json, os
payload = {'tag_name':'vX.Y.Z','target_commitish':'main','name':'vX.Y.Z','body':os.environ['REL_BODY'],'draft':False,'prerelease':False}
with open(r'<scratchpad>\release_payload.json','w',encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False)
"
curl -s -X POST "https://api.github.com/repos/neilyonglu/proj_dashboard/releases" \
  -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  --data-binary "@<scratchpad>/release_payload.json"
```

Grab `id` from the response, then upload each asset (repeat per file):

```bash
curl -s -X POST "https://uploads.github.com/repos/neilyonglu/proj_dashboard/releases/<id>/assets?name=proj_dash_update.zip" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/zip" \
  --data-binary "@proj_dash_update.zip"
```

Verify: `curl -s https://api.github.com/repos/neilyonglu/proj_dashboard/releases/latest`
should show the new `tag_name` and both assets with `"state":"uploaded"`.

## Known traps (Windows / this project)

- PowerShell 5.1: no `&&` — use `;` or `if ($?) { ... }`.
- `Out-File`/`Set-Content` default to UTF-16 — always pass `-Encoding utf8` for
  files other tools will read.
- The Bash tool is Git Bash (POSIX). Never put PowerShell cmdlets in it.
- Port 5001 taken → app exits with NO error message. Check the port first.
- No global node/npm; all Python tooling lives inside the `proj_dash` conda env.
