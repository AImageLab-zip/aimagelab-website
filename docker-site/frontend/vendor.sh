#!/bin/sh
# Download the third-party browser libraries into main/static/main/vendor/.
#
# The downloaded files ARE committed: the site must not depend on a CDN at
# run time, and there is no Node.js toolchain to rebuild them from. This
# script is the record of where each file came from, and the way to upgrade:
#
#   1. change the version in the URL *and* in the destination directory
#   2. run   frontend/vendor.sh --print-hashes   and paste the new sha256
#   3. run   frontend/vendor.sh                  (verifies every file)
#   4. update the {% static %} paths in the templates, delete the old directory
#
# Format of the list:  <sha256>  <destination under vendor/>  <url>
set -eu

HERE="$(cd "$(dirname "$0")" && pwd)"
VENDOR="$(dirname "$HERE")/main/static/main/vendor"
NPM=https://cdn.jsdelivr.net/npm

LIST="
ed271ffbe31f0905af8a6ef7b45a70831a517a70909795e637135e218a543c5e lucide-1.73.0/lucide.min.js $NPM/lucide@1.73.0/dist/umd/lucide.min.js
a9c9e2aa36d4d5b63b131f27c1272f1a28883eeecc0eddd1e0dbfae4033bc7c9 maplibre-gl-5.24.1/maplibre-gl.js $NPM/maplibre-gl@5.24.1/dist/maplibre-gl.js
ab1e70d59ec40465bae7e7030da2f3ccf28133fd502e62bd598eefbadfd7a732 maplibre-gl-5.24.1/maplibre-gl.css $NPM/maplibre-gl@5.24.1/dist/maplibre-gl.css
2c06bddfd0c89176db08ccf9d42e2beaa9b4f1a4ff8fb2ec0bf1bed25ce08e05 easymde-2.21.0/easymde.min.js $NPM/easymde@2.21.0/dist/easymde.min.js
6eee36340432776d682e7372ec4a7eb29be4fdb3ffada32c0bfa5e31a5ef34a2 easymde-2.21.0/easymde.min.css $NPM/easymde@2.21.0/dist/easymde.min.css
799aeb25cc0373fdee0e1b1db7ad6c2f6a0e058dfadaa3379689f583213190bd font-awesome-4.7.0/css/font-awesome.min.css $NPM/font-awesome@4.7.0/css/font-awesome.min.css
2adefcbc041e7d18fcf2d417879dc5a09997aa64d675b7a3c4b6ce33da13f3fe font-awesome-4.7.0/fonts/fontawesome-webfont.woff2 $NPM/font-awesome@4.7.0/fonts/fontawesome-webfont.woff2
ba0c59deb5450f5cb41b3f93609ee2d0d995415877ddfa223e8a8a7533474f07 font-awesome-4.7.0/fonts/fontawesome-webfont.woff $NPM/font-awesome@4.7.0/fonts/fontawesome-webfont.woff
615835110d07d9842d1c0a995e9fc79fb4dfa8d2c1b879ff0d648570714ee1c7 cropperjs-1.5.13/cropper.min.js $NPM/cropperjs@1.5.13/dist/cropper.min.js
055b9c1ce54007be24408e3d02e584e82c60a9a52cd1c780e5ff08318a1d787f cropperjs-1.5.13/cropper.min.css $NPM/cropperjs@1.5.13/dist/cropper.min.css
40703cceb4b468e72ae1eda73afdebdff4acc184b76a047bdd8dd487dd837ae5 tributejs-5.1.3/tribute.min.js $NPM/tributejs@5.1.3/dist/tribute.min.js
7754a027c308b6c3f6afefb9aefba01d62a59c69a33c4dab632e67c7edd09e9c tributejs-5.1.3/tribute.css $NPM/tributejs@5.1.3/dist/tribute.css
277ed9b63130f78a1604d67dc3f5c2ef7ada19713db75d3ffd71c97cacf64023 fullcalendar-6.1.10/index.global.min.js $NPM/fullcalendar@6.1.10/index.global.min.js
693b77d4f32ee9b8bfc995589b5fad5e99adf2832738661f5402f9978429a8e3 inter-4.1/InterVariable.woff2 https://rsms.me/inter/font-files/InterVariable.woff2
e564f652916db6c139570fefb9524a77c4d48f30c92928de9db19b6b5c7a262a inter-4.1/InterVariable-Italic.woff2 https://rsms.me/inter/font-files/InterVariable-Italic.woff2
"

MODE="${1:-verify}"
echo "$LIST" | while read -r sha dest url; do
    [ -n "$sha" ] || continue
    mkdir -p "$VENDOR/$(dirname "$dest")"
    curl -fsSL -o "$VENDOR/$dest" "$url"
    got="$(sha256sum "$VENDOR/$dest" | cut -d' ' -f1)"
    if [ "$MODE" = "--print-hashes" ]; then
        printf '%s %s\n' "$got" "$dest"
    elif [ "$got" != "$sha" ]; then
        echo "CHECKSUM MISMATCH: $dest" >&2
        echo "  expected $sha" >&2
        echo "  got      $got" >&2
        exit 1
    else
        echo "ok  $dest"
    fi
done
