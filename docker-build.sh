#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t teic:latest .

echo "Verifying Docker image file structure..."
# Run a temporary container to verify file structure
docker run --rm teic:latest ls -la /app/frontend/build
docker run --rm teic:latest ls -la /app/frontend/build/assets

echo "All checks passed! You can now run the container with:"
echo "docker run -e ENV=production -p 7860:7860 teic:latest" 