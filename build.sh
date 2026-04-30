#!/bin/bash

echo "開始打包作業..."

# 1. 新增一個資料夾叫做 dash_board_v0b1
mkdir -p proj_dash

# 2. 複製 app.py 到資料夾
cp app.py proj_dash/

# 進入資料夾
cd proj_dash || exit

# 3. 打包 app.py
# 使用 pyinstaller 將 app.py 打包成單一 exe (不包含 html 與靜態檔案)
pyinstaller --onefile --name "proj_dash" app.py

# 將打包出來的 exe 移到上一層
mv dist/proj_dash.exe ../proj_dash.exe

# 回到上一層
cd ..

# 4. 結束時只留下 exe，其他包含父資料夾都刪除
rm -rf proj_dash

echo "打包完成！執行檔為 proj_dash.exe"
