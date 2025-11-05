#!/bin/bash
# Build and push completely separated multi-platform Docker images
set -e

REGISTRY=${1:-"your-registry"}
TAG=${2:-"latest"}

echo "Building and pushing completely separated multi-platform images to $REGISTRY..."

# Create and use buildx builder
docker buildx create --use --name multi-platform-builder || docker buildx use multi-platform-builder

# Build and push base images for multiple platforms
echo "Building and pushing base images..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --file base.Dockerfile \
    --tag $REGISTRY/agno:base-$TAG \
    --push \
    .

# Build and push application images for multiple platforms (inherit from base)
echo "Building and pushing application images..."
# For multi-platform app builds, we need to ensure the base image is available
# The app image will inherit from the registry base image
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --file Dockerfile \
    --build-arg BASE_IMAGE=$REGISTRY/agno:base-$TAG \
    --tag $REGISTRY/agno:$TAG \
    --push \
    .

echo "Completely separated multi-platform build and push complete!"
echo ""
echo "Available images:"
echo "  - $REGISTRY/agno:base-$TAG (multi-platform base image with dependencies)"
echo "  - $REGISTRY/agno:$TAG (multi-platform application image inheriting from base)"
echo ""
echo "Usage: ./build-multiplatform.sh [registry] [tag]"
echo "Example: ./build-multiplatform.sh myregistry.com v1.0.0"
echo ""
echo "Note: Base images can be built once and reused, app images inherit from base."