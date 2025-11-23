#!/bin/bash
# Renew Let's Encrypt certificates

DOMAIN="${DOMAIN:-aimagelab-app.ing.unimore.it}"
WEBROOT="${WEBROOT:-/var/www/html}"

echo "Renewing SSL certificates for $DOMAIN..."

certbot renew --webroot -w "$WEBROOT" --quiet

if [ $? -eq 0 ]; then
    echo "Certificate renewal completed successfully!"
else
    echo "Certificate renewal check completed (no renewal needed or failed)"
fi
