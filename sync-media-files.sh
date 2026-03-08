#!/bin/bash
#
# Script to sync media files from gsalici development environment to production
# This script copies blog_covers, blog_thumbnails, and project_logos directories
# and ensures proper permissions for Django access.
#

set -e  # Exit on any error

echo "Starting media files synchronization..."

# Source and destination paths
GSALICI_MEDIA_PATH="/home/gsalici/aimagelab-dev-gsalici/docker-site/media"
PRODUCTION_MEDIA_PATH="/var/lib/docker/volumes/aimagelab_media_volume/_data"

# Directories to sync
MEDIA_DIRS=("blog_covers" "blog_thumbnails" "project_logos")

# Check if source directory exists
if [ ! -d "$GSALICI_MEDIA_PATH" ]; then
    echo "Error: Source media directory not found: $GSALICI_MEDIA_PATH"
    exit 1
fi

# Check if destination directory exists
if [ ! -d "$PRODUCTION_MEDIA_PATH" ]; then
    echo "Error: Production media directory not found: $PRODUCTION_MEDIA_PATH"
    exit 1
fi

# Sync each media directory
for dir in "${MEDIA_DIRS[@]}"; do
    echo "Syncing $dir directory..."
    
    # Check if source directory exists
    if [ ! -d "$GSALICI_MEDIA_PATH/$dir" ]; then
        echo "Warning: Source directory not found: $GSALICI_MEDIA_PATH/$dir - skipping"
        continue
    fi
    
    # Create destination directory if it doesn't exist
    mkdir -p "$PRODUCTION_MEDIA_PATH/$dir"
    
    # Copy files using bash with proper globbing
    if bash -c "cd '$GSALICI_MEDIA_PATH/$dir' && ls * &>/dev/null"; then
        bash -c "cd '$GSALICI_MEDIA_PATH/$dir' && cp * '$PRODUCTION_MEDIA_PATH/$dir/'"
        echo "✓ Copied files from $dir"
    else
        echo "Warning: No files found in $dir - skipping"
    fi
done

# Set proper ownership and permissions
echo "Setting proper ownership and permissions..."

# Set ownership to root:root (Django runs as root)
chown -R root:root "$PRODUCTION_MEDIA_PATH"

# Set directory permissions (readable/executable by all)
find "$PRODUCTION_MEDIA_PATH" -type d -exec chmod 755 {} \;

# Set file permissions (readable by all)
find "$PRODUCTION_MEDIA_PATH" -type f -exec chmod 644 {} \;

echo "✓ Media files synchronization completed successfully!"

# Print summary
echo ""
echo "Summary:"
for dir in "${MEDIA_DIRS[@]}"; do
    if [ -d "$PRODUCTION_MEDIA_PATH/$dir" ]; then
        file_count=$(find "$PRODUCTION_MEDIA_PATH/$dir" -type f | wc -l)
        echo "  $dir: $file_count files"
    fi
done