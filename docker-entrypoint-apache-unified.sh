#!/bin/bash
set -e

echo "🚀 Starting Apache with Shibboleth..."

# Start Shibboleth daemon
echo "Starting shibd..."
/usr/sbin/shibd -f -c /etc/shibboleth/shibboleth2.xml &

# Wait a moment for shibd to start
sleep 2

# Check if SSL certificates exist, if not create self-signed ones for initial setup
if [ ! -f /etc/letsencrypt/live/aimagelab-app.ing.unimore.it/fullchain.pem ]; then
    echo "⚠️  SSL certificates not found. Creating self-signed certificates for initial setup..."
    mkdir -p /etc/letsencrypt/live/aimagelab-app.ing.unimore.it
    
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/letsencrypt/live/aimagelab-app.ing.unimore.it/privkey.pem \
        -out /etc/letsencrypt/live/aimagelab-app.ing.unimore.it/fullchain.pem \
        -subj "/C=IT/ST=Emilia-Romagna/L=Modena/O=UNIMORE/CN=aimagelab-app.ing.unimore.it"
    
    # Create a minimal options-ssl-apache.conf if it doesn't exist
    if [ ! -f /etc/letsencrypt/options-ssl-apache.conf ]; then
        cat > /etc/letsencrypt/options-ssl-apache.conf <<EOF
SSLEngine on
SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder off
SSLSessionTickets off
EOF
    fi
    
    echo "✓ Self-signed certificates created. Replace with Let's Encrypt certificates in production."
fi

# Start Apache
echo "Starting Apache..."
exec "$@"
