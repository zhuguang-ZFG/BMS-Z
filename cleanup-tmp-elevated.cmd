@echo off
setlocal DisableDelayedExpansion
rem Run as administrator. Removes temp/test residue under D:\Users\BMS-Z.
cd /d "D:\Users\BMS-Z" || exit /b 1

rem Keep paths out of CALL arguments to prevent a second expansion.
for /d %%d in (.tmp-*) do if /i not "%%d"==".tmp-serve" (
  set "purgeTarget=%%d"
  call :purge
)
for /d %%d in (bms-book\.tmp-pytest-* code\protocol\.tmp-pytest code\soc\.tmp-pytest) do (
  set "purgeTarget=%%d"
  call :purge
)
set "purgeTarget=bms-book\.local\tmp\pytest-of-zhugu"
call :purge
for /d %%d in (.local\book-depth-* .local\book-tests-* .local\book-v042-*tests .local\book-visual-* .local\project-tests-* .local\pytest-book-link-fix-*) do (
  set "purgeTarget=%%d"
  call :purge
)

echo Done. Remaining .tmp-*:
dir /b /ad .tmp-* 2>nul
pause
endlocal
exit /b

:purge
echo Purging "%purgeTarget%"
takeown /f "%purgeTarget%" /r /d y >nul 2>&1
icacls "%purgeTarget%" /reset /t /c /q >nul 2>&1
rd /s /q "%purgeTarget%" 2>nul
exit /b
