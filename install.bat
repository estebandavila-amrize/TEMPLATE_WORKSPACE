@echo off
setlocal EnableDelayedExpansion
title SAP MCP Workspace Installer
color 0A

:: ============================================================
:: EDIT THIS after you create your new GitHub repo, so
:: teammates running this installer clone from the right place.
:: Leave blank to skip cloning and just scaffold a local folder.
:: ============================================================
set REPO_URL=

echo.
echo ============================================================
echo   SAP MCP Workspace Installer
echo   Kiro + SAP ADT (spec-driven ABAP development)
echo ============================================================
echo.
echo This will set up your local development workspace with:
echo   - Python MCP Server (SAP ADT connection)
echo   - Kiro steering files (tech + product rules)
echo   - Skills (plan + execute + verify)
echo   - Change template structure
echo   - MCP server configuration
echo.

:: ============================================================
:: 1. CHECK PREREQUISITES
:: ============================================================

echo [1/6] Checking prerequisites...

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
    echo WARNING: Git is not installed. You will need to copy the workspace manually.
    set GIT_AVAILABLE=0
) else (
    echo   Git: Available
    set GIT_AVAILABLE=1
)

echo   OK
echo.

:: ============================================================
:: 2. COLLECT WORKSPACE + SYSTEM INFO
:: ============================================================

echo [2/6] Workspace
echo.

set /p WORKSPACE_NAME="  Workspace folder name [sap-mcp-workspace]: "
if "!WORKSPACE_NAME!"=="" set WORKSPACE_NAME=sap-mcp-workspace
set WORKSPACE=%USERPROFILE%\!WORKSPACE_NAME!

echo.
echo [2/6] Primary SAP system
echo.

set /p SYS1_ID="  System ID (e.g. DEV, BZD, QAS): "
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

:: Use PowerShell to securely read password (hides input)
echo   Enter your SAP password (input hidden):
for /f "delims=" %%p in ('powershell -Command "$p = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))"') do set SAP_PASS=%%p

if "!SAP_PASS!"=="" (
    echo ERROR: SAP password is required.
    pause
    exit /b 1
)

echo.
set /p INSTALL_SYS2="  Configure a second SAP system (e.g. a sandbox)? (Y/N) [N]: "
if /i "!INSTALL_SYS2!"=="Y" (
    echo.
    echo   Second SAP system
    set /p SYS2_ID="    System ID: "
    set /p SYS2_NAME="    System label: "
    if "!SYS2_NAME!"=="" set SYS2_NAME=!SYS2_ID!
    set /p SYS2_HOST="    SAP host: "
    set /p SYS2_PORT="    ADT port [8000]: "
    if "!SYS2_PORT!"=="" set SYS2_PORT=8000
    set /p SYS2_CLIENT="    SAP client: "
    set /p SYS2_PACKAGE="    Default Z-package [$TMP]: "
    if "!SYS2_PACKAGE!"=="" set SYS2_PACKAGE=$TMP
    set /p SYS2_TEAM="    Team/owner label [none]: "
    set /p SYS2_CTS_PROJECT="    CTS project ID, only if required [none]: "
    set /p SYS2_TRANSPORT_LAYER="    Transport layer, only if required [none]: "
    set /p SAP_USER_SYS2="    Username [same as primary]: "
    if "!SAP_USER_SYS2!"=="" set SAP_USER_SYS2=!SAP_USER!
    echo     Enter password (input hidden):
    for /f "delims=" %%p in ('powershell -Command "$p = Read-Host -AsSecureString; [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($p))"') do set SAP_PASS_SYS2=%%p
)

echo.
echo [2/6] Project context (fills the Kiro steering files)
echo.
set /p BUSINESS_DOMAIN="  Business domain (e.g. \"Finance module enhancements\"): "
if "!BUSINESS_DOMAIN!"=="" set BUSINESS_DOMAIN=[Fill in your business domain]
set /p NETWEAVER_VERSION="  Target NetWeaver version [7.50]: "
if "!NETWEAVER_VERSION!"=="" set NETWEAVER_VERSION=7.50

echo.

:: ============================================================
:: 3. SET UP WORKSPACE DIRECTORY
:: ============================================================

echo [3/6] Setting up workspace at %WORKSPACE%...

if exist "%WORKSPACE%" (
    echo   Workspace already exists. Updating files...
) else (
    if not "%REPO_URL%"=="" if %GIT_AVAILABLE%==1 (
        echo   Cloning repository...
        git clone %REPO_URL% "%WORKSPACE%" 2>nul
        if %ERRORLEVEL% neq 0 (
            echo   Git clone failed. Creating workspace manually...
            mkdir "%WORKSPACE%"
        )
    ) else (
        mkdir "%WORKSPACE%"
    )
)

:: ============================================================
:: 4. CREATE .kiro STRUCTURE
:: ============================================================

echo [4/6] Creating Kiro workspace structure...

set KIRO=%WORKSPACE%\.kiro
mkdir "%KIRO%\steering" 2>nul
mkdir "%KIRO%\skills" 2>nul
mkdir "%KIRO%\docs" 2>nul
mkdir "%KIRO%\specs\_template_CHG\micro-specs" 2>nul
mkdir "%KIRO%\hooks" 2>nul

:: --- steering/tech.md ---
(
echo # Global Technical Constraints
echo.
echo - Target Environment: SAP NetWeaver !NETWEAVER_VERSION!.
echo - ABAP Rules: Strict classic ABAP syntax. Inline declarations ^(DATA, FIELD-SYMBOLS^) are permitted. NO ABAP Cloud, RAP, or Steampunk syntax.
echo - DDIC Rules: Use classical Dictionary objects ^(SE11^).
echo - Python MCP Rules: Flat input schemas for tools ^(no top-level Union, oneOf, or anyOf^).
) > "%KIRO%\steering\tech.md"

:: --- steering/product.md ---
(
echo # Global Product Context
echo.
echo - Objective: Python-based Model Context Protocol ^(MCP^) server interfacing with SAP NetWeaver !NETWEAVER_VERSION!.
echo - Business Domain: !BUSINESS_DOMAIN!
echo - Development Standard: All modifications are tracked via Change Requests ^(CHGxxxxxx^) and WRICEF IDs. Objects must be grouped into designated Z-packages corresponding to their WRICEF ID.
) > "%KIRO%\steering\product.md"

:: --- skills/plan.md ---
(
echo # Skill: Plan
echo.
echo ## Context
echo - Always read: `.kiro/steering/product.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, `.kiro/specs/{CHG_ID}/VISION.md`
echo - Always modify: `.kiro/specs/{CHG_ID}/ROADMAP.md`
echo.
echo ## Objective
echo Act as an ABAP Solution Architect. Review the functional requirements in VISION.md and the WRICEF metadata. Generate a step-by-step technical implementation checklist in ROADMAP.md. Break down the requirements into necessary ABAP objects. Ensure all planned objects belong inside the target WRICEF package. Do not generate code.
echo.
echo ## Halt gate
echo Present the roadmap and stop. Do not begin execution until the user replies with the literal string `ROADMAP_APPROVED`.
) > "%KIRO%\skills\plan.md"

:: --- skills/execute.md ---
(
echo # Skill: Execute
echo.
echo ## Context
echo - Always read: `.kiro/steering/tech.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, and the targeted Micro-Spec file.
echo.
echo ## Objective
echo Act as a Senior ABAP Developer. Read the provided micro-spec and implement the exact ABAP or Python syntax requested. Ensure all custom objects align structurally with the package specified in WRICEF.md. Ensure strict compliance with the NetWeaver constraints outlined in tech.md.
echo On completion, hand off to the `verify` skill. Do not self-certify the implementation as correct.
) > "%KIRO%\skills\execute.md"

:: --- skills/verify.md ---
(
echo # Skill: Verify
echo.
echo ## Context
echo - Always read: `.kiro/specs/{CHG_ID}/VISION.md`, `.kiro/specs/{CHG_ID}/WRICEF.md`, the targeted Micro-Spec file, and the implemented object^(s^) it produced.
echo.
echo ## Objective
echo Act as an independent ABAP reviewer. Re-derive correctness from VISION.md and the micro-spec, not from the executor's own reasoning. Check for swallowed failures ^(TRY/CATCH absorbing an exception, ignored SY-SUBRC^) and mechanism mismatches ^(an object whose name/comment claims one behavior but does another^). Confirm package/tech.md compliance. State PASS or FAIL explicitly with the specific lines it's based on.
echo.
echo ## Output
echo Append a dated entry to VISION.md's Bug Tracking section. Do not run the push-to-GitHub hook, or mark the step complete, until this returns PASS.
) > "%KIRO%\skills\verify.md"

:: --- specs/_template_CHG/WRICEF.md ---
(
echo # Change Registry: CHG[Number]
echo.
echo ## SAP Metadata
echo - WRICEF ID: [e.g., I002] ^([Description]^)
echo - Target Package: Z[Module]_[WRICEF]
echo - Transport Request: [TR Number]
echo - Functional Consultant: [Name]
echo.
echo ## Object Inventory
echo - [ ] [Object Type]: [Object Name] ^(New/Modified^)
) > "%KIRO%\specs\_template_CHG\WRICEF.md"

:: --- specs/_template_CHG/VISION.md ---
(
echo # Vision: Functional Specification for CHG[Number]
echo.
echo ## Business Goal
echo [Insert functional requirements here]
echo.
echo ## Process Flow
echo [Insert step-by-step business flow]
echo.
echo ## Bug Tracking ^(If applicable^)
echo Each entry from `verify`: date, verdict, what was checked, root cause if FAIL, what changed.
echo [Append entries here — do not overwrite prior ones]
) > "%KIRO%\specs\_template_CHG\VISION.md"

:: --- specs/_template_CHG/ROADMAP.md ---
(
echo # Technical Roadmap
echo.
echo ## Implementation Steps
echo [To be populated by `plan`]
echo.
echo ## Approval
echo Status: PENDING — reply `ROADMAP_APPROVED` to authorize execution.
) > "%KIRO%\specs\_template_CHG\ROADMAP.md"

:: --- specs/_template_CHG/micro-specs/_template-micro-spec.md ---
(
echo # Micro-Spec: [Object Name]
echo.
echo ## Roadmap Reference
echo - Task mapping: [e.g., Step 1.1]
echo.
echo ## Technical Implementation
echo - Target Object/File: [e.g., ZCL_CUSTOM_CLASS]
echo - Inputs:
echo - Outputs:
echo - Logic:
echo.
echo ## Constraints
echo - Adhere to tech.md rules ^(NetWeaver compatibility^).
) > "%KIRO%\specs\_template_CHG\micro-specs\_template-micro-spec.md"

:: --- hooks/push-to-github.kiro.hook ---
(
echo {
echo   "enabled": true,
echo   "name": "Push to GitHub",
echo   "description": "Runs git add, commit, and push for all workspace changes.",
echo   "version": "1",
echo   "when": { "type": "userTriggered" },
echo   "then": {
echo     "type": "runCommand",
echo     "command": "powershell -ExecutionPolicy Bypass -File scripts/git-push.ps1",
echo     "timeout": 60
echo   }
echo }
) > "%KIRO%\hooks\push-to-github.kiro.hook"

:: --- config-systems.json (generated from your answers, not committed) ---
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
) > "%WORKSPACE%\config-systems.json"

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
    ) >> "%WORKSPACE%\config-systems.json"
)

(
echo   }
echo }
) >> "%WORKSPACE%\config-systems.json"

echo   OK

:: ============================================================
:: 5. CONFIGURE MCP SERVER
:: ============================================================

echo [5/6] Configuring MCP server connection...

set MCP_DIR=%USERPROFILE%\.kiro\settings
mkdir "%MCP_DIR%" 2>nul

:: Build mcp.json with user credentials
set MCP_FILE=%MCP_DIR%\mcp.json

(
echo {
echo   "mcpServers": {
echo     "sap-!SYS1_ID!": {
echo       "command": "python",
echo       "args": ["%WORKSPACE:\=\\%\\server.py"],
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
echo         "sap_check_adt_capabilities", "sap_test_endpoint",
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
) > "%MCP_FILE%"

if /i "!INSTALL_SYS2!"=="Y" (
    (
echo     ,
echo     "sap-!SYS2_ID!": {
echo       "command": "python",
echo       "args": ["%WORKSPACE:\=\\%\\server.py"],
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
    ) >> "%MCP_FILE%"
)

(
echo   }
echo }
) >> "%MCP_FILE%"

echo   OK

:: ============================================================
:: 6. INSTALL PYTHON DEPENDENCIES
:: ============================================================

echo [6/6] Installing Python dependencies...

pip install -q mcp requests 2>nul
if %ERRORLEVEL% neq 0 (
    echo   WARNING: pip install failed. Run manually: pip install mcp requests
) else (
    echo   OK
)

:: ============================================================
:: DONE
:: ============================================================

echo.
echo ============================================================
echo   INSTALLATION COMPLETE
echo ============================================================
echo.
echo   Workspace: %WORKSPACE%
echo   MCP Config: %MCP_FILE%
echo   System Config: %WORKSPACE%\config-systems.json (not committed — see .gitignore)
echo.
echo   Next steps:
echo     1. Open Kiro
echo     2. File ^> Open Folder ^> %WORKSPACE%
echo     3. Restart Kiro to load the MCP server
echo     4. Type "Verify connection with SAP !SYS1_ID!" in chat
echo.
echo   To start a new change request:
echo     1. Copy .kiro\specs\_template_CHG to .kiro\specs\CHG04XXXXX
echo     2. Fill WRICEF.md and VISION.md
echo     3. Activate #plan to generate the roadmap, reply ROADMAP_APPROVED
echo     4. Create micro-specs, activate #execute, then #verify before transport release
echo.
echo ============================================================
pause
