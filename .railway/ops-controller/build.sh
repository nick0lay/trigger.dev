#!/bin/bash
# Build and publish ops-controller Docker image

set -e

# Configuration
DOCKER_USERNAME="${DOCKER_USERNAME:-nick0lay}"
IMAGE_NAME="trigger-ops-controller"
VERSION="${VERSION:-1.0.0}"

echo "🔨 Building ops-controller Docker image..."
echo "   Repository: $DOCKER_USERNAME/$IMAGE_NAME"
echo "   Version: $VERSION"

# Build the image
docker build -t $DOCKER_USERNAME/$IMAGE_NAME:$VERSION .
docker tag $DOCKER_USERNAME/$IMAGE_NAME:$VERSION $DOCKER_USERNAME/$IMAGE_NAME:latest

echo "✅ Build complete"

# Ask if user wants to push
read -p "Push to Docker Hub? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📤 Pushing to Docker Hub..."
    docker push $DOCKER_USERNAME/$IMAGE_NAME:$VERSION
    docker push $DOCKER_USERNAME/$IMAGE_NAME:latest
    echo "✅ Push complete"
    echo ""
    echo "Run with:"
    echo "  docker run --env-file .env $DOCKER_USERNAME/$IMAGE_NAME:latest"
else
    echo "ℹ️ Skipping push"
    echo ""
    echo "Run locally with:"
    echo "  docker run --env-file .env $DOCKER_USERNAME/$IMAGE_NAME:latest"
fi