@echo off
rem 右键 → 以管理员身份运行。清理 D:\Users\BMS-Z 下 .tmp-* 残留。
cd /d D:\Users\BMS-Z
for /d %%d in (.tmp-*) do (
  if /i not "%%d"==".tmp-serve" (
    echo 处理 %%d
    takeown /f "%%d" /r /d y >nul 2>&1
    icacls "%%d" /reset /t /c /q >nul 2>&1
    rd /s /q "%%d" 2>nul
  )
)
echo 完成。残留：
dir /b /ad .tmp-* 2>nul
pause
