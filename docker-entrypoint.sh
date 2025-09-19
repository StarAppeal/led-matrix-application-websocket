#!/bin/sh
set -e

if [ -f "/app/entry.sh" ]; then
    echo "Fixing line endings for /app/entry.sh..."
    sed -i 's/\r$//' /app/entry.sh
fi

exec "$@"