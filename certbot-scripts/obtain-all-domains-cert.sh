#!/bin/bash
# Obtain Let's Encrypt certificate for all domain aliases
# Run this to obtain or re-obtain certificates for all domains

EMAIL=${EMAIL:-admin@unimore.it}

echo "=========================================="
echo "Obtaining SSL certificate for all domains"
echo "=========================================="
echo ""

certbot certonly \
    --webroot \
    -w /var/www/html \
    --preferred-challenges http \
    -d aimagelab.unimore.it \
    -d aimagelab-app.ing.unimore.it \
    -d aimagelab.ing.unimore.it \
    -d imagelab.ing.unimo.it \
    -d www.imagelab.unimo.it \
    -d www.imagelab.ing.unimo.it \
    -d imagelab.unimo.it \
    -d www.aimagelab.unimo.it \
    -d www.aimagelab.ing.unimo.it \
    -d aimagelab.unimo.it \
    -d aimagelab.ing.unimo.it \
    --non-interactive \
    --agree-tos \
    --email ${EMAIL} \
    --no-eff-email \
    --expand \
    --force-renewal

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Certificate obtained successfully!"
    echo "=========================================="
    certbot certificates
else
    echo ""
    echo "=========================================="
    echo "Some domains failed validation."
    echo "=========================================="
    echo "This may be due to DNS propagation delays."
    echo "Retry later or remove failing domains from the command."
    exit 1
fi
