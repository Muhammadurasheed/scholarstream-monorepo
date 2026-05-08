#!/bin/bash

echo "========================================================"
echo "  ScholarStream Cloud Run Deployment (Bash/Linux)"
echo "========================================================"

# --- Configuration ---
REGION="us-central1"
BACKEND_SERVICE_NAME="scholarstream-backend"
FRONTEND_SERVICE_NAME="scholarstream-frontend"

# --- Check for gcloud ---
if ! command -v gcloud &> /dev/null; then
    echo "[ERROR] gcloud CLI is not installed or not in PATH."
    echo "Please install Google Cloud SDK and run 'gcloud auth login' first."
    exit 1
fi

echo "[1/5] Getting Project ID..."
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "[ERROR] No active project selected. Run 'gcloud config set project [YOUR_PROJECT_ID]'"
    exit 1
fi
echo "Project ID: $PROJECT_ID"

echo "[2/5] Preparing Environment Variables..."
python prepare_deploy_env.py

if [ ! -f "env.yaml" ]; then
    echo "[ERROR] env.yaml generation failed."
    exit 1
fi

echo ""
echo "[3/5] Building & Deploying Backend..."
echo "This may take a few minutes (especially for Playwright install)..."

cd backend
gcloud run deploy "$BACKEND_SERVICE_NAME" \
    --source . \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 5 \
    --env-vars-file ../env.yaml

if [ $? -ne 0 ]; then
    echo "[ERROR] Backend deployment failed."
    exit 1
fi
cd ..

echo ""
echo "[4/5] Retrieving Backend URL..."
BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE_NAME" --region "$REGION" --format "value(status.url)")
echo "Backend deployed at: $BACKEND_URL"

# Generate cloudbuild.yaml using Python to handle all the quoting logic perfectly
python prepare_deploy_env.py "$PROJECT_ID" "$FRONTEND_SERVICE_NAME" "$BACKEND_URL"

echo "Submitting build to Cloud Build..."
gcloud builds submit --config cloudbuild.yaml .
# Clean up
if [ -f "cloudbuild.yaml" ]; then
    rm cloudbuild.yaml
fi


if [ $? -ne 0 ]; then
    echo "[ERROR] Frontend build failed."
    exit 1
fi

echo "Deploying Frontend image to Cloud Run..."
gcloud run deploy "$FRONTEND_SERVICE_NAME" \
    --image "gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080

echo ""
echo "========================================================"
echo "  DEPLOYMENT COMPLETE!"
echo "========================================================"
echo "Backend: $BACKEND_URL"
FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE_NAME" --region "$REGION" --format "value(status.url)")
echo "Frontend: $FRONTEND_URL"
echo ""
echo "Please update your environment variables (Firebase, etc.) if needed."
