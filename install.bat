@echo off
setlocal EnableDelayedExpansion
title SAP MCP Workspace Installer
color 0A

:: ============================================================
:: EDIT THIS after you create your new GitHub repo, so
:: teammates running this installer clone from the right place.
:: Leave blank to copy from the local template folder instead.
:: ============================================================
set REPO_URL=

:: Detect where this installer lives (= the template source)
set TEMPLATE_DIR=%~dp0
set TEMPLATE_DIR=%TEMPLATE_DIR:~0,-1%

echo.
echo ============================================================
echo   SAP MCP Workspace Installer
echo   Kiro + SAP ADT (spec-driven ABAP development)
echo ============================================================
echo.
echo This will set up your local development workspace by copying
echo the template structure and generating your SAP credentials.
echo.
echo Template source: %TEMPLATE_DIR%
echo.

:: ============================================================
:: 1. CHECK PREREQUISITES
:: ============================================================

echo [1/7] Checking prerequisites...

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Install Python 3.10+ from https://python.org and ensure "Add to PATH" is checked.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   Python: %PYVER%

where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo WARNING: Git is not installed. Template will be copied via xcopy.
    set GIT_AVAILABLE=0
) else (
    echo   Git: Available
    set GIT_AVAILABLE=1
)

:: Portable Node.js lives under LocalAppData (no admin / UAC required)
set NODE_HOME=%LOCALAPPDATA%\Programs\nodejs

where node >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo   Node.js: !NODEVER!
    set NODE_AVAILABLE=1
) else if exist "!NODE_HOME!\node.exe" (
    set "PATH=!NODE_HOME!;!PATH!"
    for /f "delims=" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
    echo   Node.js: !NODEVER! (portable, %LOCALAPPDATA%\Programs\nodejs)
    set NODE_AVAILABLE=1
) else (
    echo   Node.js: Not found (can be installed portably in step 6 if you enable ServiceNow)
    set NODE_AVAILABLE=0
)

:: Portable GitHub CLI lives under LocalAppData (no admin / UAC required)
set GH_HOME=%LOCALAPPDATA%\Programs\gh

where gh >nul 2>&1
if %ERRORLEVEL% equ 0 (
    for /f "delims=" %%v in ('gh --version 2^>^&1 ^| findstr /r "gh version"') do set GHVER=%%v
    echo   GitHub CLI: !GHVER!
    set GH_AVAILABLE=1
) else if exist "!GH_HOME!\bin\gh.exe" (
    set "PATH=!GH_HOME!\bin;!PATH!"
    for /f "delims=" %%v in ('gh --version 2^>^&1 ^| findstr /r "gh version"') do set GHVER=%%v
    echo   GitHub CLI: !GHVER! (portable, %LOCALAPPDATA%\Programs\gh)
    set GH_AVAILABLE=1
) else (
    echo   GitHub CLI: Not found (will be installed portably in step 7)
    set GH_AVAILABLE=0
)

echo   OK
echo.

:: ============================================================
:: 2. COLLECT WORKSPACE NAME + SAP CREDENTIALS
:: ============================================================

echo [2/7] Workspace target
echo.

set /p WORKSPACE_NAME="  Workspace folder name [sap-mcp-workspace]: "
if "!WORKSPACE_NAME!"=="" set WORKSPACE_NAME=sap-mcp-workspace
set WORKSPACE=%USERPROFILE%\!WORKSPACE_NAME!

echo.
echo   Target: !WORKSPACE!
echo.

echo [2/7] Primary SAP system
echo.

set /p SYS1_ID="  System ID (e.g. DEV, QAS): "
if "!SYS1_ID!"=="" (
    echo ERROR: System ID is required.
    pause
    exit /b 1
)
set /p SYS1_NAME="  System label (e.g. Development - Team X): "
if "!SYS1_NAME!"=="" set SYS1_NAME=!SYS1_ID!
set /p SYS1_HOST="  SAP host (e.g. myhost.company.net): "
if "!SYS1_HOST!"=="" (
    echo ERROR: SAP host is required.
    pause
    exit /b 1
)
set /p SYS1_PORT="  ADT port [8000]: "
if "!SYS1_PORT!"=="" set SYS1_PORT=8000
set /p SYS1_CLIENT="  SAP client (e.g. 100): "
if "!SYS1_CLIENT!"=="" (
    echo ERROR: SAP client is required.
    pause
    exit /b 1
)
set /p SYS1_PACKAGE="  Default Z-package [$TMP]: "
if "!SYS1_PACKAGE!"=="" set SYS1_PACKAGE=$TMP
set /p SYS1_TEAM="  Team/owner label [none]: "
set /p SYS1_CTS_PROJECT="  CTS project ID, only if this system requires one [none]: "
set /p SYS1_TRANSPORT_LAYER="  Transport layer, only if this system requires one [none]: "

set /p SAP_USER="  Your SAP username: "
if "!SAP_USER!"=="" (
    echo ERROR: SAP username is required.
    pause
    exit /b 1
)

:: Use PowerShell to securely read password (hides input) and escape % for batch
echo   Enter your SAP password (input hidden):
for /f "delims=" %%p in ('powershell -Command "$p = Read-Host -AsSecureString; $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p)); $plain -replace '%%','%%%%'"') do set "SAP_PASS=%%p"

if "!SAP_PASS!"=="" (
    echo ERROR: SAP password is required.
    pause
    exit /b 1
)
echo   Password captured OK.

echo.
set /p INSTALL_SYS2="  Configure a second SAP system (e.g. a sandbox)? (Y/N) [N]: "
if /i not "!INSTALL_SYS2!"=="Y" goto :SKIP_SYS2

echo.
echo   Second SAP system
set /p SYS2_ID="    System ID: "
set /p SYS2_NAME="    System label: "
if "!SYS2_NAME!"=="" set "SYS2_NAME=!SYS2_ID!"
set /p SYS2_HOST="    SAP host: "
set /p SYS2_PORT="    ADT port [8000]: "
if "!SYS2_PORT!"=="" set "SYS2_PORT=8000"
set /p SYS2_CLIENT="    SAP client: "
set /p SYS2_PACKAGE="    Default Z-package [$TMP]: "
if "!SYS2_PACKAGE!"=="" set "SYS2_PACKAGE=$TMP"
set /p SYS2_TEAM="    Team/owner label [none]: "
set /p SYS2_CTS_PROJECT="    CTS project ID, only if required [none]: "
set /p SYS2_TRANSPORT_LAYER="    Transport layer, only if required [none]: "
set /p SAP_USER_SYS2="    Username [same as primary]: "
if "!SAP_USER_SYS2!"=="" set "SAP_USER_SYS2=!SAP_USER!"
echo     Enter password (input hidden):
for /f "delims=" %%p in ('powershell -Command "$p = Read-Host -AsSecureString; $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p)); $plain -replace '%%','%%%%'"') do set "SAP_PASS_SYS2=%%p"

:SKIP_SYS2

echo.
echo   ServiceNow (optional)
echo   Adds a "Service Now" MCP server entry so Kiro can query/update
echo   ServiceNow records. Requires the ServiceNow SDK / Node.js (step 6).
set /p INSTALL_SNOW="  Configure a ServiceNow connection? (Y/N) [N]: "
if /i not "!INSTALL_SNOW!"=="Y" goto :SKIP_SNOW_CFG

set /p SNOW_INSTANCE="    ServiceNow instance URL (e.g. https://oneservicequalna.service-now.com): "
if "!SNOW_INSTANCE!"=="" (
    echo     WARNING: No instance URL given. Skipping ServiceNow configuration.
    set INSTALL_SNOW=N
    goto :SKIP_SNOW_CFG
)
set /p SNOW_USER="    ServiceNow username (integration/service user recommended): "
set /p SNOW_ENV="    Environment label (PRD / QUAL) [QUAL]: "
if "!SNOW_ENV!"=="" set "SNOW_ENV=QUAL"
echo     Enter ServiceNow password (input hidden):
for /f "delims=" %%p in ('powershell -Command "$p = Read-Host -AsSecureString; $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p)); $plain -replace '%%','%%%%'"') do set "SNOW_PASS=%%p"

:SKIP_SNOW_CFG

echo.
echo   DEBUG: Passed second-system question, proceeding to step 3...

:: ============================================================
:: 3. COPY TEMPLATE INTO WORKSPACE
:: ============================================================

echo [3/7] Setting up workspace at !WORKSPACE!...
echo   DEBUG: TEMPLATE_DIR=!TEMPLATE_DIR!
echo   DEBUG: WORKSPACE=!WORKSPACE!
echo   DEBUG: REPO_URL=!REPO_URL!

if exist "!WORKSPACE!" (
    echo   Workspace folder already exists. Merging template files...
) else (
    echo   Creating folder: !WORKSPACE!
    mkdir "!WORKSPACE!"
    if !ERRORLEVEL! neq 0 (
        echo   ERROR: Failed to create workspace folder.
        pause
        exit /b 1
    )
)

:: Decide clone vs local copy
echo   DEBUG: Checking clone vs local copy...
if "!REPO_URL!"=="" goto :LOCAL_COPY
if "!GIT_AVAILABLE!"=="0" goto :LOCAL_COPY

echo   Cloning from !REPO_URL!...
git clone "!REPO_URL!" "!WORKSPACE!" 2>nul
if !ERRORLEVEL! equ 0 goto :COPY_DONE
echo   Clone failed. Falling back to local copy...

:LOCAL_COPY
:: Local copy using robocopy (excludes .git, credentials, and this installer)
echo   Copying template from !TEMPLATE_DIR! to !WORKSPACE!...
robocopy "!TEMPLATE_DIR!" "!WORKSPACE!" /E /XD ".git" "__pycache__" /XF "config-systems.json" "install.bat" /NFL /NDL /R:2 /W:1
echo   DEBUG: robocopy exit code=!ERRORLEVEL!

:: Remove .kiro/settings if it got copied (may contain credentials from template dev)
if exist "!WORKSPACE!\.kiro\settings" rmdir /s /q "!WORKSPACE!\.kiro\settings" 2>nul

:COPY_DONE
echo   OK
echo.

:: ============================================================
:: 4. GENERATE CREDENTIAL FILES (gitignored)
:: ============================================================

echo [4/7] Generating credential files...

:: --- .kiro/settings/mcp.json (workspace-level MCP config) ---
set MCP_DIR=!WORKSPACE!\.kiro\settings
mkdir "!MCP_DIR!" 2>nul
set MCP_FILE=!MCP_DIR!\mcp.json

(
echo {
echo   "mcpServers": {
echo     "sap-!SYS1_ID!": {
echo       "command": "python",
echo       "args": ["server.py"],
echo       "env": {
echo         "SAP_HOST": "!SYS1_HOST!:!SYS1_PORT!",
echo         "SAP_CLIENT": "!SYS1_CLIENT!",
echo         "SAP_USER": "!SAP_USER!",
echo         "SAP_PASSWORD": "!SAP_PASS!",
echo         "SAP_SECURE": "false",
echo         "SAP_SYSTEM_ID": "!SYS1_ID!",
echo         "SAP_CTS_PROJECT": "!SYS1_CTS_PROJECT!",
echo         "SAP_TRANSPORT_LAYER": "!SYS1_TRANSPORT_LAYER!"
echo       },
echo       "timeout": 60000,
echo       "disabled": false,
echo       "autoApprove": [
echo         "sap_ping", "sap_get_program_source", "sap_get_include_source",
echo         "sap_get_class_source", "sap_get_function_module_source",
echo         "sap_search_objects", "sap_get_table_definition",
echo         "sap_syntax_check", "sap_list_transports",
echo         "sap_get_transport_details", "sap_get_transport_xml_raw",
echo         "sap_run_abap_unit", "sap_create_program",
echo         "sap_update_program_source", "sap_update_program_from_file",
echo         "sap_create_interface", "sap_update_interface_source",
echo         "sap_create_class", "sap_update_class_source",
echo         "sap_update_function_module_source", "sap_create_transport",
echo         "sap_activate_object"
echo       ]
echo     }
) > "!MCP_FILE!"

if /i "!INSTALL_SYS2!"=="Y" (
    (
echo     ,
echo     "sap-!SYS2_ID!": {
echo       "command": "python",
echo       "args": ["server.py"],
echo       "env": {
echo         "SAP_HOST": "!SYS2_HOST!:!SYS2_PORT!",
echo         "SAP_CLIENT": "!SYS2_CLIENT!",
echo         "SAP_USER": "!SAP_USER_SYS2!",
echo         "SAP_PASSWORD": "!SAP_PASS_SYS2!",
echo         "SAP_SECURE": "false",
echo         "SAP_SYSTEM_ID": "!SYS2_ID!",
echo         "SAP_CTS_PROJECT": "!SYS2_CTS_PROJECT!",
echo         "SAP_TRANSPORT_LAYER": "!SYS2_TRANSPORT_LAYER!"
echo       },
echo       "timeout": 60000,
echo       "disabled": false,
echo       "autoApprove": [
echo         "sap_ping", "sap_get_program_source", "sap_get_include_source",
echo         "sap_get_class_source", "sap_get_function_module_source",
echo         "sap_search_objects", "sap_get_table_definition",
echo         "sap_syntax_check", "sap_run_abap_unit"
echo       ]
echo     }
    ) >> "!MCP_FILE!"
)

:: --- ServiceNow MCP server entry (optional) ---
if /i "!INSTALL_SNOW!"=="Y" (
    (
echo     ,
echo     "Service Now": {
echo       "command": "python",
echo       "args": ["servicenow_server.py"],
echo       "env": {
echo         "SNOW_INSTANCE": "!SNOW_INSTANCE!",
echo         "SNOW_USER": "!SNOW_USER!",
echo         "SNOW_PASSWORD": "!SNOW_PASS!",
echo         "SNOW_ENV": "!SNOW_ENV!"
echo       },
echo       "timeout": 60000,
echo       "disabled": false,
echo       "autoApprove": [
echo         "snow_ping", "snow_query", "snow_get_record",
echo         "snow_find_user", "snow_list_attachments", "snow_extract_docx"
    ) >> "!MCP_FILE!"
    :: Write tools auto-approved only for non-PRD (test) environments
    if /i not "!SNOW_ENV!"=="PRD" (
        (
echo         ,
echo         "snow_create_record", "snow_update_record", "snow_advance_state", "snow_add_work_note"
        ) >> "!MCP_FILE!"
    )
    (
echo       ]
echo     }
    ) >> "!MCP_FILE!"
)

(
echo   }
echo }
) >> "!MCP_FILE!"

:: --- config-systems.json (not committed) ---
(
echo {
echo   "systems": {
echo     "!SYS1_ID!": {
echo       "name": "!SYS1_NAME!",
echo       "host": "!SYS1_HOST!",
echo       "port": "!SYS1_PORT!",
echo       "client": "!SYS1_CLIENT!",
echo       "description": "!SYS1_NAME!",
echo       "team": "!SYS1_TEAM!",
echo       "default_package": "!SYS1_PACKAGE!",
echo       "cts_project_management": true,
echo       "allow_tmp": false
echo     }
) > "!WORKSPACE!\config-systems.json"

if /i "!INSTALL_SYS2!"=="Y" (
    (
echo     ,"!SYS2_ID!": {
echo       "name": "!SYS2_NAME!",
echo       "host": "!SYS2_HOST!",
echo       "port": "!SYS2_PORT!",
echo       "client": "!SYS2_CLIENT!",
echo       "description": "!SYS2_NAME!",
echo       "team": "!SYS2_TEAM!",
echo       "default_package": "!SYS2_PACKAGE!",
echo       "cts_project_management": false,
echo       "allow_tmp": true
echo     }
    ) >> "!WORKSPACE!\config-systems.json"
)

:: Close the "systems" object
(
echo   }
) >> "!WORKSPACE!\config-systems.json"

:: ServiceNow metadata block (no secrets; credentials live in mcp.json)
if /i "!INSTALL_SNOW!"=="Y" (
    if /i "!SNOW_ENV!"=="PRD" (
        set "SNOW_ALLOW_WRITE=false"
    ) else (
        set "SNOW_ALLOW_WRITE=true"
    )
    (
echo   ,"servicenow": {
echo     "_comment": "Non-secret ServiceNow environment metadata only. SNOW_USER/SNOW_PASSWORD live in .kiro/settings/mcp.json.",
echo     "!SNOW_ENV!": {
echo       "name": "!SNOW_ENV! - ServiceNow",
echo       "instance": "!SNOW_INSTANCE!",
echo       "env": "!SNOW_ENV!",
echo       "description": "ServiceNow !SNOW_ENV! instance",
echo       "allow_write": !SNOW_ALLOW_WRITE!
echo     }
echo   }
    ) >> "!WORKSPACE!\config-systems.json"
)

:: Close the root object
(
echo }
) >> "!WORKSPACE!\config-systems.json"

echo   OK

:: ============================================================
:: 5. INSTALL PYTHON DEPENDENCIES
:: ============================================================

echo [5/7] Installing Python dependencies...

pip install -q mcp requests 2>nul
if %ERRORLEVEL% neq 0 (
    echo   WARNING: pip install failed. Run manually: pip install mcp requests
) else (
    echo   OK
)

:: ============================================================
:: 6. INSTALL SERVICENOW SDK (optional, requires Node.js)
:: ============================================================

echo.
echo [6/7] ServiceNow SDK (optional)
echo.
echo   The ServiceNow SDK (now-sdk) lets you query live ServiceNow
echo   data (incidents, changes, RITM...) from the command line.
echo   See docs\SERVICENOW_SDK_SETUP.md.
echo.

set SNOW_INSTALLED=0

:: Only install the SDK when a ServiceNow connection was configured
if /i not "!INSTALL_SNOW!"=="Y" (
    echo   No ServiceNow connection configured. Skipping SDK install.
    goto :SKIP_SNOW
)

set /p INSTALL_SNOW_SDK="  Install the ServiceNow SDK (now-sdk) now? (Y/N) [Y]: "
if "!INSTALL_SNOW_SDK!"=="" set INSTALL_SNOW_SDK=Y
if /i not "!INSTALL_SNOW_SDK!"=="Y" goto :SKIP_SNOW

:: --- Ensure Node.js is available (portable install under LocalAppData, no admin) ---
if "!NODE_AVAILABLE!"=="1" goto :SNOW_NPM

echo   Node.js not found. Installing portable Node.js under %LOCALAPPDATA%\Programs\nodejs ...
echo   (No administrator rights required.)
set "NODE_VER=v24.19.0"
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { $ver='%NODE_VER%'; $dst='%LOCALAPPDATA%\Programs\nodejs'; $zip=Join-Path $env:TEMP ('node-'+$ver+'-win-x64.zip'); $url='https://nodejs.org/dist/'+$ver+'/node-'+$ver+'-win-x64.zip'; $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing; $parent=Split-Path $dst -Parent; if(!(Test-Path $parent)){New-Item -ItemType Directory -Force -Path $parent | Out-Null}; if(Test-Path $dst){Remove-Item -Recurse -Force $dst}; Expand-Archive -Path $zip -DestinationPath $parent -Force; Rename-Item (Join-Path $parent ('node-'+$ver+'-win-x64')) $dst; Remove-Item $zip -Force; exit 0 } catch { Write-Error $_; exit 1 }"
if !ERRORLEVEL! neq 0 (
    echo   WARNING: Portable Node.js install failed.
    echo   Install Node.js manually ^(see docs\SERVICENOW_SDK_SETUP.md section 2^),
    echo   then run:  npm install -g @servicenow/sdk@latest
    goto :SKIP_SNOW
)

:: Add portable Node to PATH for this session and persist to the user PATH
set "PATH=!NODE_HOME!;!PATH!"
set NODE_AVAILABLE=1
powershell -NoProfile -Command "$dir='%LOCALAPPDATA%\Programs\nodejs'; $u=[Environment]::GetEnvironmentVariable('Path','User'); if($u -notlike ('*'+$dir+'*')){[Environment]::SetEnvironmentVariable('Path', ($u.TrimEnd(';')+';'+$dir), 'User')}"
for /f "delims=" %%v in ('node --version 2^>^&1') do set NODEVER=%%v
echo   Node.js: !NODEVER! (portable, %LOCALAPPDATA%\Programs\nodejs)

:SNOW_NPM
echo   Installing @servicenow/sdk globally (this may take a couple of minutes)...
call npm install -g @servicenow/sdk@latest
if !ERRORLEVEL! neq 0 (
    echo   WARNING: npm install failed. Run manually: npm install -g @servicenow/sdk@latest
) else (
    for /f "delims=" %%v in ('now-sdk --version 2^>^&1') do set SNOWVER=%%v
    echo   ServiceNow SDK installed: !SNOWVER!
    set SNOW_INSTALLED=1
)

:SKIP_SNOW
echo.

:: ============================================================
:: 7. INSTALL GITHUB CLI (portable, no admin) — used by sync skills
:: ============================================================

echo [7/7] GitHub CLI (gh)
echo.
echo   The GitHub CLI (gh) lets the sync-from-repo and sync-template
echo   skills open pull requests automatically. Installed portably under
echo   %LOCALAPPDATA%\Programs\gh (no administrator rights required).
echo.

set GH_INSTALLED=0
if "!GH_AVAILABLE!"=="1" (
    echo   GitHub CLI already available. Skipping install.
    set GH_INSTALLED=1
    goto :SKIP_GH
)

echo   Installing portable GitHub CLI ...
powershell -NoProfile -Command "$ErrorActionPreference='Stop'; try { $ProgressPreference='SilentlyContinue'; $dst=\"$env:LOCALAPPDATA\Programs\gh\"; $rel=Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest' -Headers @{'User-Agent'='kiro-installer'} -UseBasicParsing; $asset=$rel.assets | Where-Object { $_.name -match 'windows_amd64\.zip$' } | Select-Object -First 1; if(-not $asset){throw 'no windows_amd64 asset found'}; $zip=Join-Path $env:TEMP $asset.name; Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing; if(Test-Path $dst){Remove-Item -Recurse -Force $dst}; New-Item -ItemType Directory -Force -Path $dst | Out-Null; Expand-Archive -Path $zip -DestinationPath $dst -Force; Remove-Item $zip -Force; $bin=Join-Path $dst 'bin'; $u=[Environment]::GetEnvironmentVariable('Path','User'); if($u -notlike ('*'+$bin+'*')){[Environment]::SetEnvironmentVariable('Path', ($u.TrimEnd(';')+';'+$bin), 'User')}; exit 0 } catch { Write-Error $_; exit 1 }"
if !ERRORLEVEL! neq 0 (
    echo   WARNING: GitHub CLI install failed. Sync skills will fall back to a manual PR URL.
    echo   You can install it later from https://cli.github.com/ or via: winget install GitHub.cli
    goto :SKIP_GH
)

set "PATH=!GH_HOME!\bin;!PATH!"
set GH_AVAILABLE=1
set GH_INSTALLED=1
for /f "delims=" %%v in ('gh --version 2^>^&1 ^| findstr /r "gh version"') do set GHVER=%%v
echo   GitHub CLI installed: !GHVER! (portable, %LOCALAPPDATA%\Programs\gh)
echo   NOTE: run 'gh auth login' once to enable automatic PR creation.

:SKIP_GH
echo.

:: ============================================================
:: DONE
:: ============================================================

echo.
echo ============================================================
echo   INSTALLATION COMPLETE
echo ============================================================
echo.
echo   Workspace: !WORKSPACE!
echo   MCP Config: !MCP_FILE!
echo   System Config: !WORKSPACE!\config-systems.json (not committed)
echo.
echo   What was copied from template:
echo     - server.py, sap_client.py (MCP server)
echo     - .kiro/steering/ (tech + product rules)
echo     - .kiro/skills/ (plan, execute, verify, ABAP reference)
echo     - .kiro/hooks/ (automation hooks)
echo     - .kiro/specs/_template_CHG/ (change request templates)
echo     - .gitignore, README.md, docs/
echo.
echo   What was generated (credentials, gitignored):
echo     - .kiro/settings/mcp.json
echo     - config-systems.json
echo.
if /i "!INSTALL_SNOW!"=="Y" (
    echo   ServiceNow: "Service Now" MCP entry added to mcp.json ^(env: !SNOW_ENV!^)
    echo     Requires servicenow_server.py / servicenow_client.py in the workspace.
    if "!SNOW_INSTALLED!"=="1" (
        echo     ServiceNow SDK installed: !SNOWVER! ^(now-sdk^)
    ) else (
        echo     ServiceNow SDK not installed. To install later: npm install -g @servicenow/sdk@latest
    )
    echo     See docs\SERVICENOW_SDK_SETUP.md for details.
    echo.
) else (
    echo   ServiceNow: not configured ^(optional^)
    echo     Re-run the installer or see docs\SERVICENOW_SDK_SETUP.md to add it later.
    echo.
)
if "!GH_INSTALLED!"=="1" (
    echo   GitHub CLI: available ^(gh^) — enables auto PR creation for sync skills
    echo     Run 'gh auth login' once if you have not authenticated yet.
    echo.
) else (
    echo   GitHub CLI: not installed — sync skills will fall back to a manual PR URL
    echo     Install later from https://cli.github.com/ or via: winget install GitHub.cli
    echo.
)
echo   Next steps:
echo     1. Open Kiro
echo     2. File ^> Open Folder ^> !WORKSPACE!
echo     3. Restart Kiro to load the MCP server
echo     4. Type "Verify connection with SAP !SYS1_ID!" in chat
echo.
echo   To start a new change request:
echo     1. Copy .kiro\specs\_template_CHG to .kiro\specs\CHG04XXXXX
echo     2. Fill WRICEF.md and VISION.md
echo     3. Activate #plan to generate the roadmap, reply ROADMAP_APPROVED
echo     4. Create micro-specs, activate #execute, then #verify
echo.
echo ============================================================
pause
