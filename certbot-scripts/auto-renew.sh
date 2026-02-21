#!/bin/bash
# Auto-renew certificates (runs in a loop, checking every 12 hours)
# When certificates are renewed, Apache is automatically reloaded

while true; do
    echo "Checking for certificate renewals at $(date)"
    
    # Run certbot renew with deploy hook
    certbot renew --webroot -w /var/www/html \
        --deploy-hook "docker exec aimagelab-apache-prod-1 apache2ctl graceful" \
        --quiet 2>&1 || echo "Renewal check completed"
    
    echo "Next check in 12 hours"
    sleep 43200  # Sleep for 12 hours
done
