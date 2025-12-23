#!/bin/bash

SRC="../media/uploadedImages"
DEST="docker-site/media/blog_covers"

for file in "$SRC"/*; do
    filename=$(basename "$file")

    # Skip files containing "thumb"
    if [[ "$filename" == *thumb* ]]; then
        continue
    fi

    # Remove leading zeros from filename
    newname=$(echo "$filename" | sed 's/^0\+//')

    # Copy file with new name
    sudo cp "$file" "$DEST/$newname"
done
