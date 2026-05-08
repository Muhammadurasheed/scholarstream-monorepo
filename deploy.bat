@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   ScholarStream Cloud Run Deployment (Windows)
echo ========================================================

REM --- Configuration ---
set REGION=us-central1
set BACKEND_SERVICE_NAME=scholarstream-backend
set FRONTEND_SERVICE_NAME=scholarstream-frontend

REM --- Check for gcloud ---
where gcloud >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] gcloud CLI is not installed or not in PATH.
    echo Please install Google Cloud SDK and run "gcloud auth login" first.
    exit /b 1
)

echo [1/5] Getting Project ID...
for /f "tokens=*" %%a in ('gcloud config get-value project') do set PROJECT_ID=%%a
if "%PROJECT_ID%"=="" (
    echo [ERROR] No active project selected. Run "gcloud config set project [YOUR_PROJECT_ID]"
    exit /b 1
)
echo Project ID: %PROJECT_ID%

echo.
echo [2/5] Building & Deploying Backend...
echo This may take a few minutes (especially for Playwright install)...

cd backend
call gcloud run deploy %BACKEND_SERVICE_NAME% ^
    --source . ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --port 8080 ^
    --memory 2Gi ^
    --cpu 2 ^
    --min-instances 0 ^
    --max-instances 5
cd ..

if %errorlevel% neq 0 (
    echo [ERROR] Backend deployment failed.
    exit /b 1
)

echo.
echo [3/5] Retrieving Backend URL...
for /f "tokens=*" %%i in ('gcloud run services describe %BACKEND_SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set BACKEND_URL=%%i
echo Backend deployed at: %BACKEND_URL%

echo.
echo [4/5] Building & Deploying Frontend...
echo Injecting API URL: %BACKEND_URL%

REM We use Cloud Build manually here to pass the build-arg
call gcloud builds submit ^
    --tag gcr.io/%PROJECT_ID%/%FRONTEND_SERVICE_NAME% ^
    --substitutions=_API_URL=%BACKEND_URL% ^
    --config cloudbuild.yaml .
    
REM Wait, creating cloudbuild.yaml on the fly to handle build-arg cleaner
echo steps: > cloudbuild.yaml
echo   - name: 'gcr.io/cloud-builders/docker' >> cloudbuild.yaml
echo     args: ['build', '--build-arg', 'VITE_API_BASE_URL=%BACKEND_URL%', '-t', 'gcr.io/%PROJECT_ID%/%FRONTEND_SERVICE_NAME%', '-f', 'Dockerfile.frontend', '.'] >> cloudbuild.yaml
echo images: ['gcr.io/%PROJECT_ID%/%FRONTEND_SERVICE_NAME%'] >> cloudbuild.yaml

echo Submitting build to Cloud Build...
call gcloud builds submit --config cloudbuild.yaml .
del cloudbuild.yaml

if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed.
    exit /b 1
)

echo Deploying Frontend image to Cloud Run...
call gcloud run deploy %FRONTEND_SERVICE_NAME% ^
    --image gcr.io/%PROJECT_ID%/%FRONTEND_SERVICE_NAME% ^
    --region %REGION% ^
    --allow-unauthenticated ^
    --port 8080

echo.
echo ========================================================
echo   DEPLOYMENT COMPLETE!
echo ========================================================
echo Backend: %BACKEND_URL%
for /f "tokens=*" %%i in ('gcloud run services describe %FRONTEND_SERVICE_NAME% --region %REGION% --format "value(status.url)"') do set FRONTEND_URL=%%i
echo Frontend: %FRONTEND_URL%
echo.
echo Please update your environment variables (Firebase, etc.) if needed.
pause
