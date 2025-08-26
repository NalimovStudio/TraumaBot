bash
   #!/bin/bash
   set -e

   echo "Starting Docker cleanup..."

   # Остановка всех контейнеров (если нужно)
   docker-compose -f /home/deploy/app/TraumaBot/docker-compose.yml down

   # Очистка неиспользуемых образов, контейнеров, volumes
   echo "Cleaning unused Docker objects..."
   docker system prune -a --volumes -f

   # Очистка кэша сборки
   echo "Cleaning build cache..."
   docker builder prune -f

   # Проверка и удаление больших логов (если не ограничены)
   echo "Cleaning large log files..."
   find /var/lib/docker/containers/ -type f -name '*-json.log' -size +10M -delete

   echo "Docker cleanup completed."