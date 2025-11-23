#!/bin/bash
# Auto-renew certificates (for cron job)

certbot renew --webroot -w /var/www/html --quiet --deploy-hook "docker exec aimagelab-apache apache2ctl graceful"
