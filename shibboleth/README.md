# Shibboleth Configuration Placeholder

This directory should contain your Shibboleth SP configuration files:

- `shibboleth2.xml` - Main Shibboleth configuration
- `attribute-map.xml` - Attribute mapping
- `sp-cert.pem` - Service Provider certificate
- `sp-key.pem` - Service Provider private key
- Additional trust certificates

## Quick Start (Optional)

If you don't need Shibboleth authentication, you can disable it by:

1. Removing Shibboleth-related sections from the Apache config (`apache-dev.conf` / `apache-prod.conf`)
2. Commenting out Shibboleth installation in the Apache Dockerfiles (`Dockerfile.apache.dev` / `Dockerfile.apache.prod`)

## With Shibboleth

If you need Shibboleth authentication:

1. Copy your Shibboleth configuration files to this directory
2. Update `shibboleth2.xml` with your entity ID and metadata
3. Ensure certificates have proper permissions (sp-key.pem should be 600)

For more information, see your organization's Shibboleth documentation.
