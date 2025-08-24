#!/bin/sh
set -e

# Устанавливаем правильные права на acme.json
if [ -f /acme.json ]; then
    chmod 600 /acme.json
fi

# Запускаем оригинальную команду
exec "$@"