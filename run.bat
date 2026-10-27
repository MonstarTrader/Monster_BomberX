@echo off
cd /d "%~dp0"
if not exist proxies.txt (
    echo [+] no proxies.txt — scraping...
    python proxy_fetch.py
)
if not exist harvest mkdir harvest
type nul > harvest\.gitkeep
python bomber.py %*
