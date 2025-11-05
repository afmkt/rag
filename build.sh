#!/bin/bash
# Build script for completely separated base and app Docker images with multi-platform support

set -e

PLATFORM=${1:-"both"}  # Default to building both platforms

echo "🏗️ Building completely separated Agno Docker images for platform: $PLATFORM"

if [ "$PLATFORM" = "x64" ] || [ "$PLATFORM" = "both" ]; then
    echo "🔧 Building for x64 platform..."
    ./buildx64.sh
fi

if [ "$PLATFORM" = "m3" ] || [ "$PLATFORM" = "both" ]; then
    echo "🔧 Building for M3 platform..."
    ./buildm3.sh
fi

echo "🎉 Build complete!"
echo ""
echo "📋 Available images:"
if [ "$PLATFORM" = "x64" ] || [ "$PLATFORM" = "both" ]; then
    echo "  - agno:base-x64 (base image with dependencies ~4.5GB)"
    echo "  - agno:x64 (full application image ~4.5GB)"
    echo "  - agno:app-x64 (application code only ~875KB)"
fi
if [ "$PLATFORM" = "m3" ] || [ "$PLATFORM" = "both" ]; then
    echo "  - agno:base-m3 (base image with dependencies ~4.2GB)"
    echo "  - agno:m3 (full application image ~4.2GB)"
    echo "  - agno:app-m3 (application code only ~875KB)"
fi
echo ""
echo "💡 Deployment options:"
echo "  - Deploy agno:base-x64 once, then update app code with agno:app-x64"
echo "  - Or deploy full images agno:x64/agno:m3 for traditional deployment"