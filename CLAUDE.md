# CLAUDE.md — proj_dashboard

## 專案簡介

專案管理與工時追蹤系統。用於記錄專案資訊、人員工時、Gantt 圖時程，並支援 CSV 匯入/匯出與管理後台。

- 後端：Python 3 + Flask + Flask-SQLAlchemy
- 資料庫：SQLite（`instance/app.db`，首次啟動自動建立）
- 前端：HTML + Tailwind CSS（CDN）+ Jinja2 模板
- WSGI 伺服器：Waitress（port 5001）
- 打包：PyInstaller → `proj_dash.exe`

---

## 啟動方式

本專案使用 conda 環境 `proj_dash`（依賴已安裝在其中）。

```bash
# 啟動（建議）
conda run -n proj_dash python app.py
# 或
conda activate proj_dash
python app.py
# → http://localhost:5001
```

> 注意：Node.js/npm 未在全域 PATH，Python 工具都在 `proj_dash` env 內。
> 啟動前若 5001 埠已被舊程序佔用，需先結束該程序，否則新程式無法綁定埠（會靜默退出）。

管理後台密碼透過 `.env` 的 `DB_ADMIN_PASSWORD` 設定（目前為 `5206`），未設定時預設 `admin123`。

---

## 建構執行檔

```bat
build.bat          # Windows（輸出 proj_dash.exe）
```

執行檔需與 `templates/` 和 `static/` 放在同一目錄才能正常運作。

---

## 目錄結構

```
app.py              主應用（Flask app、DB 模型、所有 routes，共 ~1150 行）
templates/          13 個 Jinja2 HTML 模板
  base.html           共用 navbar 佈局
  index.html          儀表板首頁
  proj_timeline.html  Gantt 圖
  employee_case.html  員工個人頁面
  manage_db.html      管理後台
  manage_*.html       人員/代表/分類管理頁
  add_*/edit_*.html   CRUD 表單
static/
  css/style.css       自訂樣式
  js/main.js          前端 JS
  js/tailwind-config.js  Tailwind 設定
  avatars/            人員頭像上傳目錄
instance/app.db     SQLite 資料庫（勿納入版控）
.env                環境變數（SECRET_KEY、DB_ADMIN_PASSWORD）
build.bat           Windows 打包腳本
build.sh            Unix 打包腳本
```

---

## 資料庫模型（app.py:65-112）

| 模型 | 說明 |
|---|---|
| `Representative` | 業務代表 |
| `Personnel` | 員工（含頭像路徑、顯示名稱）|
| `Category` | 專案分類 |
| `Project` | 專案（日期、狀態、設備、描述）|
| `Task` | 工時記錄（關聯 Project，含人員、工作天數、日班/加班/夜班時數）|

刪除 `Project` 會 cascade 刪除其所有 `Task`。

`Task` 的 `day_hours`/`overtime_hours`/`night_hours` 為選填時數欄位，與 `work_days` 並存。
舊資料庫由 `ensure_task_columns()`（啟動時執行）自動以 `ALTER TABLE` 補欄位。

---

## Routes 總覽（app.py）

**一般功能**
- `GET/POST /` — 儀表板
- `GET/POST /add-project` — 新增專案
- `GET/POST /edit-project/<id>` — 編輯專案
- `POST /delete-project/<id>` — 刪除專案
- `GET/POST /add-task` — 新增工時記錄
- `GET/POST /edit-task/<id>` — 編輯工時記錄
- `POST /delete-task/<id>` — 刪除工時記錄
- `GET /timeline` — Gantt 圖（月/季/年動態縮放）
- `GET /employee-case` — 員工個人儀表板

**管理後台（需驗證）**
- `GET/POST /manage-db-login` — 後台登入
- `GET /manage-db` — 管理後台主頁
- `GET/POST /manage-personnel` — 員工管理
- `GET/POST /manage-reps` — 代表管理
- `GET/POST /manage-categories` — 分類管理

**CSV API（需驗證）**
- `/api/export-db` / `/api/import-db` — 專案 CSV
- `/api/export-tasks` / `/api/import-tasks` — 工時 CSV
- `/api/export-reps` / `/api/import-reps` — 代表 CSV
- `/api/export-personnel` / `/api/import-personnel` — 員工 CSV
- `/api/export-categories` / `/api/import-categories` — 分類 CSV

---

## 資料備份（#9）

- 每次啟動自動備份 `instance/app.db` 至 `instance/backups/`（檔名 `app_startup_*.db`），只保留最近 `BACKUP_KEEP=10` 份。
- 管理後台右上「立即備份」(`POST /api/backup-now`)、「下載備份」(`GET /api/backup-download`)。
- `backup_database(reason)` 與 `ensure_task_columns()` 定義於 app.py「1b. Schema Migration & Backup Helpers」。

## 重要細節

- **自動建立種子資料**：首次啟動時建立 3 個代表、5 個分類、6 位員工（app.py 末段）
- **名稱連動**：編輯人員代號會同步更新所有 `Task.personnel`；編輯種類/代表名稱會同步更新 `Project`（`compute_back_url`/cascade 邏輯於 app.py）
- **返回鈕**：管理頁的「返回」改用伺服器端 `back_url`（依 referrer 計算），避免 `history.back()` 的 bfcache 不刷新問題
- **時間軸日期**：前端一律用 `parseLocalDate()` 解析，避免 UTC/本地時差造成月份篩選溢出（四月顯示到五月）
- **頭像上傳**：僅接受 PNG/JPG/GIF/WebP，最大 5MB
- **CSV 編碼**：自動偵測 UTF-8 / UTF-8-BOM / BIG5（相容 Excel 匯出）
- **CSV 匯入模式**：`skip`（跳過重複）或 `overwrite`（覆蓋現有）
- **管理後台驗證**：使用 Flask session（`session['admin_logged_in']`）

---

## CodeGraph 使用指引

本專案已配置 CodeGraph 語意代碼圖，AI agent 應優先透過 MCP 工具查詢符號關係，而非直接掃描檔案。

**初始化（需先安裝 Node.js >= 20）：**
```bash
npx @colbymchenry/codegraph
# 選擇 Claude Code 並依提示完成設定
```

**常用查詢：**
- 查找路由：`codegraph_search` → 搜尋 `@app.route`
- 查找模型：`codegraph_context` → 查詢 `Project` 或 `Task`
- 影響分析：`codegraph_impact` → 修改模型前先確認影響範圍
