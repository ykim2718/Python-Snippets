@echo off
setlocal enabledelayedexpansion

REM === 1. Generate timestamp for commit message ===
for /f "tokens=1-4 delims=/ " %%a in ("%date%") do (
    set TODAY=%%a-%%b-%%c
)
for /f "tokens=1-2 delims=:." %%a in ("%time%") do (
    set NOWTIME=%%a-%%b
)
set NOW=%TODAY%_%NOWTIME%

echo Commit message: Auto commit at %NOW%

REM === 2. Initialize Git repo if .git does not exist ===
if not exist .git (
    echo Initializing new git repository...
    git init
)

REM === 3. Detect current branch ===
for /f "delims=" %%b in ('git branch --show-current') do set BRANCH=%%b

if "%BRANCH%"=="" (
    echo No branch detected. Creating main branch...
    git checkout -b main
    set BRANCH=main
)

echo Current branch: %BRANCH%

REM === 4. Stage all changes ===
git add .

REM === 5. Check if there are staged changes ===
git diff --cached --quiet
if %errorlevel%==0 (
    echo No changes to commit.
) else (
    git commit -m "Auto commit at %NOW%"
)

REM === 6. Add remote origin only if it does not exist ===
git remote | find "origin" >nul
if %errorlevel% neq 0 (
    echo Adding remote origin...
    git remote add origin https://github.com/ykim2718/Python.git
)

REM === 7. Push to remote ===
echo Pushing to origin %BRANCH%...
git push -u origin %BRANCH%

echo Done.
pause
