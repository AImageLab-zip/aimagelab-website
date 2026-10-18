#!/bin/bash
# Auto-renew certificates (runs in a loop, checking every 12 hours)
# When certificates are renewed, Apache is automatically reloaded

while true; do
    echo "Checking for certificate renewals at $(date)"
    
    # Run certbot renew. No deploy hook is needed: the apache-prod container
    # watches /etc/letsencrypt/live/$DOMAIN/fullchain.pem on the shared
    # letsencrypt_data volume and reloads itself when the cert changes.
    # This container therefore no longer needs /var/run/docker.sock, which
    # granted it root-equivalent control of the host.
    certbot renew --webroot -w /var/www/html \
        --quiet 2>&1 || echo "Renewal check completed"
    
    echo "Next check in 12 hours"
    sleep 43200  # Sleep for 12 hours
done
