#!/bin/bash
# Build Docker image for x64 (Intel/AMD)
set -e

echo "🔨 Building Docker images for x64 platform..."

# Build base image for x64
echo "📦 Building base image for x64..."
docker buildx create --use || true
docker buildx build --platform linux/amd64 -f base.Dockerfile -t agno:base -t agno:base-x64 . --load

# Build application image for x64 (optional)
echo "🚀 Building application image for x64 (optional, kept for compatibility)..."
# If you prefer to run the app as a standalone image, uncomment the next line.
# docker build -f Dockerfile -t agno:x64 .

echo "✅ Successfully built agno:base-x64 for linux/amd64 (x64) platform."

# Clean up buildkit containers
echo "🧹 Cleaning up buildkit containers..."
docker rm -f $(docker ps -aq --filter "ancestor=moby/buildkit:buildx-stable-1") 2>/dev/null || true
