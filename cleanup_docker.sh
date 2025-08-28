#!/bin/bash
echo "🧹 Starting aggressive Docker cleanup..."

docker rmi $(docker images -aq) 2>/dev/null || true
docker network prune -f
docker builder prune -a -f

echo "✅ Aggressive cleanup completed!"