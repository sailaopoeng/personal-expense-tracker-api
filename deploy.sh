#!/bin/bash

# Deploy script for Google Cloud Run
# Make sure you have gcloud CLI installed and authenticated

set -e

# Configuration
PROJECT_ID="personal-expense-bot"  # Replace with your GCP project ID
SERVICE_NAME="personal-expense-api"
REGION="us-central1"  # or your preferred region
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting deployment to Google Cloud Run..."

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📤 Pushing image to Google Container Registry..."
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300 \
    --set-env-vars "ENVIRONMENT=production,STATIC_PASSWORD=your-password,JWT_SECRET_KEY=your-jwt-secret,GOOGLE_SHEET_ID=your-sheet-id,GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/json,GOOGLE_AI_API_KEY=your-ai-key"
    --project $PROJECT_ID

echo "✅ Deployment complete!"
echo "🌐 Your API is available at:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"