#!/bin/bash

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-personal-expense-bot}"
SERVICE_NAME="${SERVICE_NAME:-personal-expense-api}"
REGION="${REGION:-us-central1}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.5-flash-lite}"

echo "Deploying $SERVICE_NAME to Google Cloud Run..."

gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 1 \
    --timeout 300 \
    --update-env-vars "GEMINI_MODEL=$GEMINI_MODEL"

echo "Deployment complete:"
gcloud run services describe "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --region "$REGION" \
    --format="value(status.url)"
