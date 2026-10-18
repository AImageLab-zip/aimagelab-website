#!/bin/bash
set -e

echo "🚀 Starting production Apache with Shibboleth..."

DOMAIN="${DOMAIN:-aimagelab-app.ing.unimore.it}"
EMAIL="${CERTBOT_EMAIL:-admin@unimore.it}"

# Watch the live certificate and gracefully reload Apache when it changes.
#
# This replaces the old mechanism, where the certbot-renew container was given
# a bind-mount of /var/run/docker.sock so its --deploy-hook could run
# `docker exec ... apache2ctl graceful`. Access to the Docker socket is
# equivalent to root on the host, which is far too much authority for a
# certificate renewal sidecar. Apache now notices the new cert by itself.
watch_certificate() {
    local cert="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    local last=""
    # Resolve the symlink too: certbot swaps live/ symlinks to a new archive/
    # directory on renewal, so the target path changes even when mtime is coarse.
    last="$(readlink -f "$cert" 2>/dev/null):$(stat -c %Y "$cert" 2>/dev/null)"
    while true; do
        sleep 3600
        local now
        now="$(readlink -f "$cert" 2>/dev/null):$(stat -c %Y "$cert" 2>/dev/null)"
        if [ -n "$now" ] && [ "$now" != "$last" ]; then
            echo "🔁 Certificate for $DOMAIN changed, reloading Apache..."
            apache2ctl graceful || echo "⚠️  Apache graceful reload failed"
            last="$now"
        fi
    done
}

# Start Shibboleth daemon if configuration is present
if [ -f /etc/shibboleth/shibboleth2.xml ]; then
    echo "Starting shibd..."
    /usr/sbin/shibd -f -c /etc/shibboleth/shibboleth2.xml &
    sleep 2
else
    echo "⚠️  Shibboleth configuration not found, skipping shibd startup."
fi

# Ensure Let's Encrypt directories exist
mkdir -p /etc/letsencrypt/live/$DOMAIN
mkdir -p /var/www/html/.well-known/acme-challenge

# Check if valid Let's Encrypt certificates exist (symlinks indicate real LE certs)
if [ ! -L /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    echo "⚠️  Valid SSL certificates not found. Creating temporary self-signed certificates..."
    
    # Remove any existing self-signed certs to avoid conflicts
    rm -rf /etc/letsencrypt/live/$DOMAIN
    mkdir -p /etc/letsencrypt/live/$DOMAIN
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
        -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
        -subj "/C=IT/ST=Emilia-Romagna/L=Modena/O=UNIMORE/CN=$DOMAIN"

    if [ ! -f /etc/letsencrypt/options-ssl-apache.conf ]; then
        cat >/etc/letsencrypt/options-ssl-apache.conf <<EOF
SSLEngine on
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder off
SSLSessionTickets off
EOF
    fi
    
    # Start Apache in background with self-signed certs
    echo "Starting Apache with self-signed certificates..."
    apache2ctl -D FOREGROUND &
    APACHE_PID=$!
    
    # Wait for Apache to be ready
    echo "Waiting for Apache to serve ACME challenge..."
    sleep 5
    
    # Try to obtain Let's Encrypt certificate
    echo "Attempting to obtain Let's Encrypt certificate for $DOMAIN..."
    if certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email="$EMAIL" \
        --agree-tos \
        --no-eff-email \
        --non-interactive \
        --domains="$DOMAIN" \
        --expand; then
        echo "✅ Let's Encrypt certificate obtained! Reloading Apache..."
        kill -HUP $APACHE_PID
    else
        echo "⚠️  Let's Encrypt certificate request failed. Continuing with self-signed cert."
    fi
    
    # Wait for Apache process
    wait $APACHE_PID
else
    echo "✅ SSL certificates found. Starting Apache..."
    # Reload Apache in-place whenever certbot-renew installs a new certificate.
    watch_certificate &
    # Start Apache in foreground
    exec "$@"
fi
