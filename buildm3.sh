#!/bin/bash
# Build Docker image for Mac M3 (Apple Silicon, ARM64)
set -e

echo "🔨 Building Docker images for M3 platform..."

# Build base image for M3
echo "📦 Building base image for M3..."
docker buildx create --use || true
docker buildx build --platform linux/arm64 -f base.Dockerfile -t agno:base -t agno:base-m3 . --load

# Build application image for M3 (inherits from base)
echo "🚀 Building application image for M3..."
docker build -f Dockerfile -t agno:m3 .

# Build application code image for M3 (source code only)
echo "📄 Building application code image for M3..."
docker build -f app.Dockerfile -t agno:app-m3 .

echo "✅ Successfully built agno:m3 for linux/arm64 (Mac M3) platform."
