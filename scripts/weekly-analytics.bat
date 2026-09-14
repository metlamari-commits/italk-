@echo off
REM Weekly analytics runner — invoked by Windows Task Scheduler.
REM Runs the script (which writes MD + HTML) and opens the HTML report in the browser.
cd /d "%~dp0.."
node scripts\weekly-analytics.mjs --open > "%USERPROFILE%\Documents\italk-analytics\_last-run.log" 2>&1
