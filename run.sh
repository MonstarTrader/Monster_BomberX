#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

if [ ! -f proxies.txt ]; then
    echo "[+] no proxies.txt — scraping..."
    python proxy_fetch.py || python3 proxy_fetch.py
fi

mkdir -p harvest
touch harvest/.gitkeep

python bomber.py "$@" || python3 bomber.py "$@"
