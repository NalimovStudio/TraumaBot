#!/bin/bash
echo "🧹 Starting aggressive Docker cleanup..."

docker stop $(docker ps -aq) 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true

# удаление images
docker rmi -f $(docker images -aq) 2>/dev/null || true

# удаление сборок
docker builder prune -a -f

# Но НЕ удаляем volumes папку
echo "✅ Preserving volumes: /var/lib/docker/volumes"

docker image prune -a -f || true
docker images purge --all --force
docker system prune -a -f
docker network prune -f


echo "✅ Aggressive cleanup completed!"