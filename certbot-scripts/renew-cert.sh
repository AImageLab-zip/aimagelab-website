#!/bin/bash
# Manually renew Let's Encrypt certificates

WEBROOT="${WEBROOT:-/var/www/html}"

echo "Renewing SSL certificates..."

certbot renew --webroot -w "$WEBROOT"

if [ $? -eq 0 ]; then
    echo "Certificate renewal completed successfully!"
else
    echo "Certificate renewal failed. Check logs: /var/log/letsencrypt/letsencrypt.log"
    exit 1
fi
