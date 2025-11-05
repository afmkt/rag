#!/bin/bash

echo "Cleaning Docker build cache..."
docker buildx prune -a

echo "Removing stopped containers..."
docker container prune -f

echo "Stopping BuildKit containers..."
docker container stop $(docker container ls -q --filter "name=buildx_buildkit" 2>/dev/null) 2>/dev/null || echo "No BuildKit containers running"

echo "Removing BuildKit containers..."
docker container rm $(docker container ls -aq --filter "name=buildx_buildkit" 2>/dev/null) 2>/dev/null || echo "No BuildKit containers to remove"

echo "Docker cleanup complete!"