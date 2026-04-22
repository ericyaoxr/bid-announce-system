@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Bid Announce System - QA ^& Deploy
echo ==========================================

echo.
echo Step 1: Backend QA
echo ------------------------------------------
echo Running ruff lint...
ruff check src\ scripts\ tests\
if errorlevel 1 (
    echo [WARN] Ruff lint found issues, continuing...
)

echo Running ruff format check...
ruff format --check src\ scripts\ tests\
if errorlevel 1 (
    echo [WARN] Ruff format found issues, continuing...
)

echo Running pytest...
pytest tests\ -v --cov=src --cov-report=term-missing
if errorlevel 1 (
    echo [ERROR] Backend tests failed!
    exit /b 1
)

echo.
echo Step 2: Frontend QA
echo ------------------------------------------
echo Installing frontend dependencies...
cd frontend
call npm ci
if errorlevel 1 (
    echo [ERROR] npm ci failed!
    exit /b 1
)

echo Running TypeScript type check...
npx tsc --noEmit
if errorlevel 1 (
    echo [ERROR] TypeScript check failed!
    exit /b 1
)

echo Running ESLint...
npx eslint src\
echo [INFO] ESLint complete

echo Running Vitest tests...
call npm run test:run
if errorlevel 1 (
    echo [ERROR] Frontend tests failed!
    exit /b 1
)

echo Building frontend...
call npm run build
if errorlevel 1 (
    echo [ERROR] Frontend build failed!
    exit /b 1
)

cd ..

echo.
echo Step 3: Deploy
echo ------------------------------------------
echo Copying frontend build to web directory...
if exist web rmdir /s /q web
xcopy /e /i /y frontend\dist web

echo.
echo ==========================================
echo   QA ^& Deploy Complete!
echo   Frontend: http://localhost:8000/
echo   API Docs: http://localhost:8000/docs
echo ==========================================
