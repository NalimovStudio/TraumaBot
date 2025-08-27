#!/bin/bash

echo "🔍 Checking Docker disk usage before cleanup..."
docker system df

echo "🧹 Cleaning up unused Docker resources..."

# Удаляем остановленные контейнеры
echo "🗑️ Removing stopped containers..."
CONTAINERS_OUTPUT=$(docker container prune -f)
echo "$CONTAINERS_OUTPUT"

# Удаляем неиспользуемые образы
echo "🖼️ Removing dangling images..."
IMAGES_OUTPUT=$(docker image prune -f)
echo "$IMAGES_OUTPUT"

# Удаляем неиспользуемые сети
echo "🌐 Removing unused networks..."
NETWORKS_OUTPUT=$(docker network prune -f)
echo "$NETWORKS_OUTPUT"

# Удаляем строительный кэш
echo "🧱 Removing build cache..."
BUILDER_OUTPUT=$(docker builder prune -f)
echo "$BUILDER_OUTPUT"

echo "🔍 Checking Docker disk usage after cleanup..."
docker system df

echo "✅ Docker cleanup completed successfully!"