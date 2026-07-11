# ARCHITECTURE — proj_dashboard (reference)

Extracted from the old CLAUDE.md on 2026-07-06. This is a convenience map — the code
is the source of truth. If this file disagrees with the code, fix this file
(see global `40-maintenance.md`).

## Directory layout

```
app.py              entry point (Flask init, config, startup; ~80 lines)
core/
  extensions.py       db = SQLAlchemy()  (avoids circular imports)
  models.py           DB models
  helpers.py          utilities (backup + daily scheduler, migration, form parsing,
                      compute_back_url)
  updater.py          GitHub-release version check + self-update (download/relaunch)
  routes/
    __init__.py       register_routes(app) — mounts all route modules
    main.py           dashboard, timeline, employee page, overtime stats
    projects.py       project CRUD
    tasks.py          task (work-hours) CRUD
    admin.py          admin login, backup API, self-update API, CSV export/import
    manage.py         personnel / representative / category management
templates/          Jinja2 templates (base.html = shared navbar layout)
static/
  css/style.css, js/main.js, js/tailwind-config.js, avatars/
instance/app.db     SQLite DB (not in VCS); backups in instance/backups/
.env                SECRET_KEY, DB_ADMIN_PASSWORD
build.bat           PyInstaller packaging (Windows)
```

## Models (core/models.py)

| Model | Purpose |
|---|---|
| `Representative` | sales representative |
| `Personnel` | employee (avatar path, display name) |
| `Category` | project category |
| `Project` | project (dates, status, equipment, description) |
| `Task` | work-hours record, FK to Project; person, work days, day/overtime/night hours |

- Deleting a `Project` cascades to its `Task`s.
- `Task.day_hours` / `overtime_hours` / `night_hours` are optional and coexist with
  `work_days`. Old DBs get missing columns via `ensure_task_columns()` (ALTER TABLE
  at startup, defined in `core/helpers.py`).
- First startup seeds 3 representatives, 5 categories, 6 personnel (end of `app.py`).

## Routes

Public (`core/routes/main.py`, `projects.py`, `tasks.py`):

| Route | Purpose |
|---|---|
| `GET /` | dashboard |
| `GET/POST /add-project`, `/edit-project/<id>`; `POST /delete-project/<id>` | project CRUD |
| `GET/POST /add-task`, `/edit-task/<id>`; `POST /delete-task/<id>` | task CRUD |
| `GET /timeline` | Gantt chart (month/quarter/year zoom) |
| `GET /project/<id>` | project detail page |
| `GET /employee-case` | per-employee dashboard |
| `GET /overtime-stats` | overtime statistics |

Admin, session-gated (`admin.py`, `manage.py`):

| Route | Purpose |
|---|---|
| `GET/POST /manage-db-login`; `GET /manage-db` | admin login / home |
| `GET/POST /manage-personnel`, `/manage-reps`, `/manage-categories` | entity management |
| `/api/export-db`, `/api/import-db` | projects CSV |
| `/api/export-tasks`, `/api/import-tasks` | tasks CSV |
| `/api/export-reps`, `/api/import-reps` | representatives CSV |
| `/api/export-personnel`, `/api/import-personnel` | personnel CSV |
| `/api/export-categories`, `/api/import-categories` | categories CSV |
| `GET /api/export-all` | whole DB as one .xlsx, one sheet per table (admin-auth gated) |
| `GET /api/backup-download`; `POST /api/backup-now`, `/api/backup-restore` | DB backup |
| `GET /api/check-update`; `POST /api/update-now` | self-update (latter admin-auth gated) |

## Design decisions that are NOT obvious from a quick read

- Route modules expose `def register(app):` and are mounted by `register_routes(app)`
  — deliberately NOT Blueprints, to keep `url_for` names stable. Do not convert.
- Renaming a Personnel code updates all `Task.personnel`; renaming a Category or
  Representative updates matching `Project` fields (`core/routes/manage.py`).
  Preserve this propagation when touching those routes.
- Manage pages' "back" buttons use server-side `back_url` from `compute_back_url()`
  (`core/helpers.py`) — `history.back()` was removed because bfcache served stale
  pages. Do not reintroduce it.
- Frontend dates are parsed with `parseLocalDate()` — defined inline in
  `templates/proj_timeline.html` (~line 402), NOT in `static/js/main.js` (that file
  is combobox code). `new Date('YYYY-MM-DD')` is treated as UTC and shifts months
  (April bled into May).
- CSV import auto-detects UTF-8 / UTF-8-BOM / BIG5 (Excel compatibility); import
  modes are `skip` (skip duplicates) or `overwrite`.
- Avatar upload: PNG/JPG/GIF/WebP only, max 5 MB.
- Admin auth: `session['db_admin_auth']`; password from `.env` `DB_ADMIN_PASSWORD`
  (fallback `admin123`).
- DB backup: once per day, checked at startup AND hourly via a background thread
  (`start_daily_backup_scheduler`, `core/helpers.py`) so a server left running for
  days without restart still gets a daily backup — startup-only used to mean no
  backup ever happened again until the next restart. Backs up to
  `instance/backups/`, keep `BACKUP_KEEP=10`. Paths come from
  `current_app.config['DB_FILE_PATH']` / `['DB_INSTANCE_DIR']`.
- Self-update (`core/updater.py`, routes in `core/routes/admin.py`): compares
  `APP_VERSION` against the latest GitHub release tag (public repo, no auth
  needed) via `GET /api/check-update`. `POST /api/update-now` (admin-auth
  gated) downloads that release's `proj_dash_update.zip` asset (built by
  `build.bat`: exe + `templates/` + `static/`, since PyInstaller does NOT embed
  those folders — most past releases changed templates, not just Python code),
  hash-compares (`_sha256`/`_changed_files`) each extracted file against what's
  installed and only writes the ones that actually differ, writes a detached
  relauncher `.bat` that waits for the running exe to unlock, swaps only the
  changed exe/templates/static files (keeping one `.bak` of the old exe if the
  exe changed), and restarts it, then the Flask process exits itself. Only
  works inside a frozen PyInstaller build (`sys.frozen`); no-ops with a clear
  error in dev. Requires Neil to manually attach `proj_dash_update.zip` to
  each GitHub Release — see README "發布新版本".
- Manual update installer (`tools/installer.py`, built by `build.bat` into a
  separate `proj_dash_installer.exe`): pure-stdlib standalone script — reuses
  `core.updater`'s `_sha256`/`_changed_files`/`API_LATEST_RELEASE`/`ASSET_NAME`
  but does NOT import Flask/db, so it can be PyInstalled independently of the
  main app. Meant to be downloaded and double-clicked directly from a GitHub
  Release, without going through the running app's admin UI (e.g. if the exe
  won't start). Stops `proj_dash.exe` via `taskkill` if running, applies the
  same changed-files-only swap, never touches `instance/app.db` or
  `instance/backups` (the release zip never contains them), then relaunches
  the app if it was running.
