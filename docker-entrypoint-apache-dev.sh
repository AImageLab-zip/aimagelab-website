#!/bin/bash
set -e

echo "🚀 Starting development Apache (HTTP only)..."

# Allow runtime overrides of ServerName to keep apache quiet
if ! grep -q "ServerName" /etc/apache2/apache2.conf; then
  echo "ServerName dev-apache" >> /etc/apache2/apache2.conf
fi

exec "$@"
