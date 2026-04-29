<<<<<<< HEAD
# 專案管理與工時追蹤系統 (Project Dashboard)

一個基於 Python Flask 開發的輕量級企業內部專案與人員工時管理系統。提供直覺的介面來管理專案進度、人員工作紀錄、並具備甘特圖式的時間軸檢視以及完整的資料庫匯入/匯出功能。

## 🌟 主要功能 (Features)

*   **📊 總覽儀表板 (Dashboard)**：快速檢視目前進行中的專案數量、參與人員總數與當月總工作天數。
*   **📅 專案時間軸 (Project Timeline)**：以甘特圖 (Gantt Chart) 形式視覺化呈現所有專案的起始與結束時間，並精準標示各人員在專案中的工作區段。
*   **📝 工作紀錄追蹤 (Task Tracking)**：記錄個別人員在不同專案中投入的工作天數與內容。
*   **👥 人員進度管理 (Employee Dashboard)**：專屬的人員檢視頁面，支援自訂大頭貼與顯示名稱，快速查詢特定員工參與的所有專案與總時數。
*   **🗄️ 資料庫管理 (Database Management)**：
    *   受密碼保護的後台管理介面。
    *   支援全資料表（專案、工作紀錄、人員、業務代表、專案種類）的**搜尋與管理**。
    *   **CSV 匯出/匯入**：支援一鍵備份資料為 CSV，並支援上傳 CSV 進行批量新增或覆蓋更新（自動處理 Excel 產生的 BIG5 編碼與 UTF-8-BOM 問題）。

## 🛠️ 技術棧 (Tech Stack)

*   **後端**: Python 3, Flask, Flask-SQLAlchemy
*   **資料庫**: SQLite (`app.db`)
*   **前端**: HTML5, Tailwind CSS (透過 CDN), Material Symbols (Icons)
*   **伺服器**: Waitress (WSGI Production Server)

## 📁 專案結構 (Project Structure)

```text
proj_dashboard/
├── app.py                 # 應用程式主程式與所有路由邏輯
├── .env                   # 環境變數設定檔 (需手動建立)
├── instance/
│   └── app.db             # SQLite 資料庫檔案 (系統自動建立)
├── static/
│   └── avatars/           # 人員大頭貼上傳目錄
└── templates/             # HTML 渲染模板
    ├── base.html          # 共用版型 (Navbar)
    ├── index.html         # 首頁儀表板
    ├── proj_timeline.html # 專案時間軸 (甘特圖)
    ├── employee_case.html # 人員專屬頁面
    ├── manage_db*.html    # 資料庫管理相關頁面
    └── ...
```

## 🚀 安裝與執行 (Installation & Setup)

1. **安裝 Python**
   請確保您的系統已安裝 Python 3.8 或以上版本。

2. **安裝依賴套件 (Requirements)**
   請在終端機中執行以下指令安裝必要的 Python 套件：
   ```bash
   pip install flask flask-sqlalchemy waitress werkzeug
   ```

3. **設定環境變數 (.env)**
   在專案根目錄下建立一個 `.env` 檔案，可設定以下變數（若未設定系統將使用預設值）：
   ```env
   SECRET_KEY=your_super_secret_key
   DB_ADMIN_PASSWORD=admin123
   ```
   *(註：`DB_ADMIN_PASSWORD` 是進入資料庫管理頁面的預設密碼)*

4. **啟動伺服器**
   在終端機中執行以下指令：
   ```bash
   python app.py
   ```
   伺服器啟動後，請打開瀏覽器並前往：[http://localhost:5001](http://localhost:5001)

## 💡 使用說明

1. **首次啟動**：系統會自動建立 `instance/app.db` 資料庫，並預先寫入一些預設的業務代表、專案種類與人員名單。
2. **新增專案**：點擊導覽列的「新增專案」，填寫基本資訊。如果輸入了系統中不存在的業務代表或種類，系統會自動將其加入選項中。
3. **資料庫管理**：點擊「資料庫」圖示，預設密碼為 `admin123`（或您在 `.env` 中設定的密碼）。您可以在此處下載 CSV 備份或匯入修改後的 CSV 進行資料還原或批量更新。

## 📄 授權 (License)

This project is intended for internal company use.
=======
# proj_dashboard
>>>>>>> ee2a7b3d78e3cabf97afe51cbe1307f868cc9b15
