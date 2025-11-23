#!/bin/bash
# Obtain Let's Encrypt certificate using certbot

DOMAIN=${DOMAIN:-aimagelab-app.ing.unimore.it}
EMAIL=${EMAIL:-admin@unimore.it}

echo "Obtaining SSL certificate for ${DOMAIN}..."

certbot certonly \
    --webroot \
    -w /var/www/html \
    -d ${DOMAIN} \
    --non-interactive \
    --agree-tos \
    --email ${EMAIL} \
    --no-eff-email

echo "Certificate obtained successfully!"
