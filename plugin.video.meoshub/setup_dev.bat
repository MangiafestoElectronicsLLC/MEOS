@echo off
REM ============================================================================
REM  MEOS Hub - developer automation script (setup / validate / dev-launch)
REM  Usage:
REM      setup_dev.bat            -> run validation + smoke tests only
REM      setup_dev.bat launch     -> also copy the add-on into your Kodi
REM                                  addons folder and start Kodi with logging
REM      setup_dev.bat logs       -> just tail/open the current kodi.log
REM ============================================================================
setlocal enabledelayedexpansion

set "ADDON_DIR=%~dp0"
set "ADDON_ID=plugin.video.meoshub"
set "MODE=%~1"

echo.
echo === MEOS Hub dev automation ===
echo Add-on folder: %ADDON_DIR%
echo.

REM --- 1. Locate Python -------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3 and re-run this script.
    goto :end
)

REM --- 2. Validate the add-on (XML, py_compile, router smoke test) -----------
echo [1/3] Running validation / test harness...
python "%ADDON_DIR%tools\test_harness.py"
if errorlevel 1 (
    echo [ERROR] Validation failed. Fix the reported issues before launching Kodi.
    goto :end
)
echo Validation passed.
echo.

if /I "%MODE%"=="logs" goto :openlogs
if /I NOT "%MODE%"=="launch" goto :end

REM --- 3. Copy into the local Kodi add-ons folder (dev-mode install) ----------
echo [2/3] Installing into local Kodi add-ons folder...
if "%KODI_HOME%"=="" set "KODI_HOME=%APPDATA%\Kodi"
set "TARGET_DIR=%KODI_HOME%\addons\%ADDON_ID%"

if not exist "%KODI_HOME%" (
    echo [WARN] Could not find a Kodi profile at %KODI_HOME%.
    echo        Set the KODI_HOME environment variable to your Kodi userdata folder and re-run.
    goto :end
)

if exist "%TARGET_DIR%" (
    echo Removing previous dev copy...
    rmdir /s /q "%TARGET_DIR%"
)
robocopy "%ADDON_DIR%." "%TARGET_DIR%" /E /XD __pycache__ .git /XF *.pyc >nul

echo Installed to %TARGET_DIR%
echo.

REM --- 4. Launch Kodi in debug mode -------------------------------------------
echo [3/3] Launching Kodi (debug logging enabled)...
set "KODI_EXE=%ProgramFiles(x86)%\Kodi\kodi.exe"
if not exist "%KODI_EXE%" set "KODI_EXE=%ProgramFiles%\Kodi\kodi.exe"

if not exist "%KODI_EXE%" (
    echo [WARN] Could not find kodi.exe automatically. Start Kodi manually.
) else (
    start "" "%KODI_EXE%" --debug
)

:openlogs
echo Opening the Kodi log for live viewing...
set "LOG_FILE=%KODI_HOME%\temp\kodi.log"
if not exist "%LOG_FILE%" set "LOG_FILE=%APPDATA%\Kodi\temp\kodi.log"
if exist "%LOG_FILE%" (
    start "" notepad "%LOG_FILE%"
) else (
    echo [WARN] kodi.log not found yet at %LOG_FILE% - start Kodi first.
)

:end
echo.
echo Done.
endlocal
