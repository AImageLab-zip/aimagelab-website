#!/bin/bash
# Auto-renew certificates (runs in a loop, checking every 12 hours)
# Note: Apache will pick up the renewed certs on its next reload/restart
# The certs are shared via volume mount with the apache-prod container

while true; do
    echo "Checking for certificate renewals at $(date)"
    certbot renew --webroot -w /var/www/html --quiet || echo "Renewal check completed with warnings"
    echo "Next check in 12 hours"
    sleep 43200  # Sleep for 12 hours
done
