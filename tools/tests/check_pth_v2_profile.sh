#!/usr/bin/env bash
set -euo pipefail

mkdir -p pth-fixtures/aether
ZIP="pth-fixtures/aether/aether-rvc-v2.zip"
MODEL="pth-fixtures/aether/aether-rvc-v2.pth"
SHA256="49d261ca204ceebe19becd0304fb86d549b2f93eef03e222d95e492138823bc6"
URL="https://huggingface.co/Plana-Archive/Anime-Models/resolve/dbccdd6c69d1a678dcb985cf116e6e711d6b8bc9/Anime-RCV/RVC-GENSHIN-IMPACT-TTS/prezipped/v2/aether-jp%20100%20epochs%2048k%20v2.zip"

if [ ! -s "$ZIP" ]; then
  curl --fail --location --retry 3 --silent --show-error "$URL" -o "$ZIP"
fi
echo "$SHA256  $ZIP" | sha256sum --check

if [ ! -s "$MODEL" ]; then
  ENTRY="$(unzip -Z1 "$ZIP" | awk 'tolower($0) ~ /[.]pth$/ { print; exit }')"
  if [ -z "$ENTRY" ]; then
    echo "No PTH checkpoint was found in the public RVC v2 archive." >&2
    exit 1
  fi
  unzip -p "$ZIP" "$ENTRY" > "$MODEL"
fi

test -s "$MODEL"
./pth-check "$MODEL" 768 100
