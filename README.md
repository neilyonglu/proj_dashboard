# 專案管理與工時追蹤系統 (Project Dashboard)

> **版本：v1.3.0**

一個基於 Python Flask 開發的輕量級企業內部專案與人員工時管理系統。提供直覺的介面來管理專案進度、人員工作紀錄、並具備甘特圖式的時間軸檢視以及完整的資料庫匯入/匯出功能。

## 🌟 主要功能 (Features)

*   **📊 總覽儀表板 (Dashboard)**：快速檢視目前進行中的專案數量、參與人員總數與當月總工作天數。未登入管理者時，資料庫管理入口以鎖頭圖示顯示並導向登入。
*   **📅 專案時間軸 (Project Timeline)**：以甘特圖 (Gantt Chart) 形式視覺化呈現所有專案的起始與結束時間，並精準標示各人員在專案中的工作區段。
    *   清楚的今天線、月份交替底色與週末背景區隔。
    *   明顯的水平卷軸，滑鼠移到人員工作區段時顯示完整資訊（日期、天數、時數、內容）的浮動提示。
    *   月份區間篩選（修正了選取月份時溢出到下個月的問題）。
*   **📝 工作紀錄追蹤 (Task Tracking)**：記錄個別人員在不同專案中投入的工作天數與內容，並可額外填寫**日班 / 加班 / 夜班時數**（選填，與工作天數並存）。
*   **👥 人員進度管理 (Employee Dashboard)**：專屬的人員檢視頁面，支援自訂大頭貼與顯示名稱，快速查詢特定員工參與的所有專案與總時數。
    *   工作紀錄支援**依月／週／日分組收納**，大量筆數一目了然，可逐組展開／收合。
    *   **刪除紀錄限管理者**：一般使用者僅能查看與編輯，刪除需登入管理者帳號後才顯示。
*   **⏱️ 加班統計 (Overtime Stats)**：依日／月／年／自訂區間統計各人員與各專案的日班、加班、夜班時數，由高到低排序。
*   **🗄️ 資料庫管理 (Database Management)**：受密碼保護的後台管理介面。
    *   支援全資料表（專案、工作紀錄、人員、業務代表、專案種類）的**搜尋與管理**。
    *   **新增、編輯與刪除**專案種類與業務代表（改名時會自動同步更新關聯專案）；修改人員系統代號時會同步更新所有相關工作紀錄。
    *   **CSV 匯出/匯入**：支援一鍵備份資料為 CSV，並支援上傳 CSV 進行批量新增或覆蓋更新（自動處理 Excel 產生的 BIG5 編碼與 UTF-8-BOM 問題）。
    *   **資料庫備份/還原**：每天自動備份資料庫一次（啟動時檢查＋伺服器持續運作時每小時檢查一次，保留最近 10 份），並可在後台一鍵「立即備份」、「下載備份」與「還原備份」（還原前會自動先備份目前資料）。
*   **📋 操作日誌 (Activity Log)**：所有寫入操作（新增／編輯／刪除／匯入／備份、登入成功與失敗）皆自動記錄至 `instance/logs/` 目錄，格式為 `[時間] IP | 操作 | 細節`，每個月份自動分檔（每檔上限 2000 筆）。

## 🛠️ 技術棧 (Tech Stack)

*   **後端**: Python 3, Flask, Flask-SQLAlchemy
*   **資料庫**: SQLite (`app.db`)
*   **前端**: HTML5, Tailwind CSS (透過 CDN), Material Symbols (Icons)
*   **伺服器**: Waitress (WSGI Production Server)

## 📁 專案結構 (Project Structure)

```text
proj_dashboard/
├── app.py                 # 應用程式進入點（Flask 初始化、設定、啟動）
├── core/                  # 核心應用模組
│   ├── extensions.py      # SQLAlchemy db 實例
│   ├── models.py          # 資料庫模型（Project, Task, Personnel, ...）
│   ├── helpers.py         # 工具函式（備份＋每日排程、Migration、表單解析）
│   ├── updater.py         # 版本檢查與一鍵自我更新（下載/替換/重啟）
│   ├── activity_log.py    # 操作日誌寫入模組
│   └── routes/            # 路由模組
│       ├── main.py        # 儀表板、時間軸、員工頁、加班統計
│       ├── projects.py    # 專案 CRUD
│       ├── tasks.py       # 工時紀錄 CRUD
│       ├── admin.py       # 後台登入、備份 API、自我更新 API、CSV 匯出/匯入
│       └── manage.py      # 人員、代表、分類管理
├── build.bat              # Windows 打包執行檔腳本 (PyInstaller)，同時產生 proj_dash_update.zip
├── .env                   # 環境變數設定檔 (需手動建立, 已被 .gitignore 排除)
├── instance/              # 執行期資料 (已被 .gitignore 排除)
│   ├── app.db             # SQLite 資料庫檔案 (系統自動建立)
│   ├── backups/           # 資料庫備份檔 (系統自動建立, 保留最近 10 份)
│   └── logs/              # 操作日誌 (activity_YYYYMM_NNN.log)
├── static/
│   └── avatars/           # 人員大頭貼上傳目錄
└── templates/             # HTML 渲染模板
    ├── base.html          # 共用版型 (Navbar)
    ├── index.html         # 首頁儀表板
    ├── proj_timeline.html # 專案時間軸 (甘特圖)
    ├── employee_case.html # 人員專屬頁面
    ├── overtime_stats.html# 加班統計
    ├── manage_db*.html    # 資料庫管理相關頁面
    └── ...
```

## 🚀 安裝與執行 (Installation & Setup)

1. **安裝 Python**
   請確保您的系統已安裝 Python 3.8 或以上版本。本專案使用 conda 環境 `proj_dash`。

2. **安裝依賴套件 (Requirements)**
   請在終端機中執行以下指令安裝必要的 Python 套件：
   ```bash
   pip install flask flask-sqlalchemy waitress werkzeug
   ```

3. **設定環境變數 (.env)**
   在專案根目錄下建立一個 `.env` 檔案（此檔案已被 `.gitignore` 排除，不會進版控），可設定以下變數（若未設定系統將使用預設值）：
   ```env
   SECRET_KEY=your_super_secret_key
   DB_ADMIN_PASSWORD=admin123
   ```
   *(註：`DB_ADMIN_PASSWORD` 是進入資料庫管理頁面的密碼，未設定時預設為 `admin123`)*

4. **啟動伺服器**
   在終端機中執行以下指令（建議使用 conda 環境）：
   ```bash
   conda run -n proj_dash python app.py
   # 或
   conda activate proj_dash
   python app.py
   ```
   伺服器啟動後，請打開瀏覽器並前往：[http://localhost:5001](http://localhost:5001)

## 📦 打包執行檔 (Packaging)

若要將系統打包為單一的可執行檔 (`.exe`)，以便在未安裝 Python 的電腦上或方便佈署執行：

1. **安裝 PyInstaller**：
   ```bash
   pip install pyinstaller
   ```
2. **執行打包腳本**（僅支援 Windows）：
   ```powershell
   cmd.exe /c build.bat
   ```
3. **完成打包**：
   打包完成後，會在專案根目錄產生 `proj_dash.exe`，以及 `proj_dash_update.zip`（`proj_dash.exe` + `templates/` + `static/` 打包在一起，供下方「發布新版本」上傳使用）。
   *(註：打包出的 exe 檔案會自動讀取同層目錄下的 `templates` 與 `static` 資料夾，因此在部屬 exe 給其他人使用時，請將 `proj_dash.exe` 與這兩個資料夾放在同一個目錄下。)*

## 🚀 發布新版本（供一鍵更新使用）

程式內建的「檢查更新／一鍵更新」會讀取本專案 GitHub Release 的 `proj_dash_update.zip` 附件。發布新版時：

1. 更新 `app.py` 裡的 `APP_VERSION`（例如 `1.3.1`），並在 README 補上 changelog。
2. 執行 `build.bat` 產生 `proj_dash.exe`、`proj_dash_update.zip`，以及獨立手動安裝程式 `proj_dash_installer.exe`。
3. 到 GitHub 建立新的 tag/release（例如 `v1.3.1`），把 `proj_dash_update.zip`（一鍵更新用）與 `proj_dash_installer.exe`（手動安裝用，雙擊即可）都當作附件上傳。
4. 已在跑舊版 exe 的電腦，下次點擊「檢查更新」就會看到新版本，管理者登入後即可「立即更新」；或直接下載 `proj_dash_installer.exe` 雙擊手動安裝。兩種方式都只覆寫真的有變動的檔案，且不會動到 `instance/app.db` 與 `instance/backups`。

*(若某次發布沒有上傳 `proj_dash_update.zip`，舊版程式只會顯示「已是最新版本」，不會出錯，但也不會提示這個新 release。)*

## 💡 使用說明

1. **首次啟動**：系統會自動建立 `instance/app.db` 資料庫，並預先寫入一些預設的業務代表、專案種類與人員名單。若資料庫為舊版，啟動時會自動補上新欄位（時數欄）。
2. **新增專案**：點擊導覽列的「新增專案」，填寫基本資訊。如果輸入了系統中不存在的業務代表或種類，系統會自動將其加入選項中。
3. **資料庫管理**：點擊首頁「資料庫管理」（需先登入，未登入時顯示鎖頭），輸入 `.env` 中設定的密碼（未設定時預設為 `admin123`）。您可以在此處：
   *   下載 CSV 備份或匯入修改後的 CSV 進行資料還原或批量更新。
   *   使用「立即備份 / 下載備份 / 還原備份」管理整個資料庫檔案（`.db`）。
4. **資料庫備份與還原**：
   *   每天自動在 `instance/backups/` 建立一次備份（啟動時檢查一次，之後即使伺服器不重啟也會每小時再檢查一次），最多保留最近 10 份。
   *   要還原時，點「還原備份」並上傳先前下載的 `.db` 檔；系統會在覆蓋前自動先備份目前資料（`pre_restore`），確保可回復。
5. **操作日誌**：所有操作記錄在 `instance/logs/activity_YYYYMM_NNN.log`，可用文字編輯器直接開啟查閱。

## 📋 版本紀錄 (Changelog)

### v1.3.2
- **工作紀錄匯入可選擇先清空**：匯入 CSV 前可勾選「匯入前清空所有工作紀錄」，會先自動備份再清空，避免舊資料與新資料混雜；匯入視窗提示文字也修正為實際的去重規則
- **員工表不顯示離職員工**：`/employee-case` 的員工下拉選單只列出在職人員（透過連結直接開啟離職員工的紀錄仍可正常顯示）
- **專案狀態改為可複選**：新增/編輯專案時可同時勾選多個狀態（例如「進行中」+「等待中」），專案列表與時間軸的狀態篩選也改為可複選

### v1.3.1
- **全庫匯出 (Excel)**：資料庫管理頁新增「全部匯出 (Excel)」，一次匯出整個資料庫成單一 .xlsx 檔，每個資料表各一個分頁
- **手動安裝更新程式**：新增獨立的 `proj_dash_installer.exe`，雙擊即可連線 GitHub 抓取最新版本並安裝，不需要透過網頁介面，`instance/app.db` 與 `instance/backups` 不會被更動
- **自動更新改為只覆寫有變動的檔案**：套用更新前逐檔比對雜湊值，未變動的檔案不再重新寫入，降低重啟風險

### v1.3.0
- **資料庫每日備份修正**：改為啟動時＋背景每小時檢查一次，伺服器長時間不重啟也能確保每天備份一次（原本只在啟動當下判斷，長期不重啟就不會再備份）
- **一鍵自動更新**：首頁與資料庫管理後台可偵測 GitHub 上的新版本，管理者登入後可一鍵下載、自動關閉並重啟為新版（詳見下方「發布新版本」說明）

### v1.2.1
- **員工表專案圓餅圖**：員工資訊卡右側新增「專案分佈」甜甜圈圖，顯示各專案工時佔比；點擊下方分組標頭（年／月／週／日）可即時切換該期間的圓餅圖，tooltip 改為 HTML 浮層不受 canvas 邊界遮擋

### v1.2.0
- **專案詳情頁面**：點擊專案名稱進入專案詳情，含工期/人員/紀錄統計卡、人員工時圓餅圖（可點進員工表）、日/加/夜時數橫條圖
- **員工表「年」分組**：新增「年」分組選項，可依年度收納大量紀錄
- **專案表人員可點**：專案表格與時間軸的人員名稱改為連結，點擊直接跳到該員工工時頁

### v1.1.1
- 修正加班統計頁標題「加班統計」文字改為可點連結，點擊回首頁

### v1.1.0
- 員工表工作紀錄支援依**月／週／日分組**，可折疊展開，大量筆數易於瀏覽
- 刪除工作紀錄／專案限**管理者登入**才可操作（後端同步防護）
- 首頁**資料庫管理**入口未登入時顯示鎖頭，登入後才顯示完整入口
- 新增**操作日誌**系統，自動記錄所有寫入操作、登入事件至 `instance/logs/`
- 加班統計頁新增「首頁」文字超連結

### v1.0.1
- 加班統計（日/月/年/自訂區間，日加夜三欄）
- 員工辭職標記
- 狀態過濾
- 工時模糊下拉

## 📄 授權 (License)

This project is intended for internal company use.
