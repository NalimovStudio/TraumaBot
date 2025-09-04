#!/bin/sh
set -e

# Устанавливаем правильные права на acme.json
if [ -f /acme/acme.json ]; then
    chmod 600 /acme/acme.json
    echo "✅ Fixed permissions for /acme/acme.json"
fi

echo "🚀 Starting Traefik..."
exec /usr/local/bin/traefik "$@"