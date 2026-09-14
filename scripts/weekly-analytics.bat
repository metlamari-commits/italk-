@echo off
REM Weekly analytics runner — invoked by Windows Task Scheduler.
cd /d "%~dp0.."
node scripts\weekly-analytics.mjs > "%USERPROFILE%\Documents\italk-analytics\_last-run.log" 2>&1
