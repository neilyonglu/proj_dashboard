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
$pages = @("/", "/timeline", "/employee-case", "/overtime-stats", "/add-project", "/add-task"); foreach ($p in $pages) { try { $r = Invoke-WebRequest -Uri "http://localhost:5001$p" -UseBasicParsing -TimeoutSec 5; Write-Output "$p -> $($r.StatusCode)" } catch { Write-Output "$p -> FAIL $($_.Exception.Message)" } }
```

To verify a specific template change actually rendered, grep the page for a marker
you added, e.g.:

```powershell
$r = Invoke-WebRequest -Uri "http://localhost:5001/employee-case" -UseBasicParsing; if ($r.Content -match "YOUR_MARKER") { "marker OK" } else { "MISSING" }
```

A template edit is NOT verified until a real GET shows the marker.

## Syntax check without starting the app

```powershell
conda run -n proj_dash python -c "import ast; ast.parse(open('app.py',encoding='utf-8').read()); print('app.py syntax OK')"
```

## Run a one-off script against the project / DB

Use the env's python directly (avoids conda PATH issues entirely):

```powershell
& "C:\Users\Neil\miniconda3\envs\proj_dash\python.exe" path\to\script.py
```

DB lives at `instance\app.db`; automatic backups in `instance\backups\` (keep 10).
Before any schema experiment, copy `instance\app.db` aside first.

## Build the exe

```powershell
cmd.exe /c build.bat
```

`build.bat` already calls conda internally (commit a16a578) and deletes the .spec.
Output `proj_dash.exe` must sit next to `templates\` and `static\` to run.

## Known traps (Windows / this project)

- PowerShell 5.1: no `&&` — use `;` or `if ($?) { ... }`.
- `Out-File`/`Set-Content` default to UTF-16 — always pass `-Encoding utf8` for
  files other tools will read.
- The Bash tool is Git Bash (POSIX). Never put PowerShell cmdlets in it.
- Port 5001 taken → app exits with NO error message. Check the port first.
- No global node/npm; all Python tooling lives inside the `proj_dash` conda env.
