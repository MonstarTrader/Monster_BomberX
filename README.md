# bd-sms-bomber

Multi-gateway SMS bomber for Bangladeshi numbers. Harvests API keys from
decompiled APKs and JS bundles, auto-registers free-tier gateways, rotates
proxies and user-agents, runs unlimited sends via a threaded dispatcher.

Works on **Windows 10/11, Linux, macOS, and Termux (Android)**.

## Install

### Windows 10/11
1. Install Python 3.10+ from https://python.org (tick "Add to PATH").
2. Install Java 17 from https://adoptium.net.
3. Download & install apktool: https://apktool.org/docs/install
4. Open PowerShell in the repo folder:
```powershell
pip install -r requirements.txt
```

### Linux / macOS / WSL
```bash
git clone https://github.com/<you>/bd-sms-bomber.git
cd bd-sms-bomber
bash install.sh
```

### Termux (Android)
```bash
pkg update && pkg upgrade -y
pkg install python git openjdk-17 python-cryptography -y
git clone https://github.com/<you>/bd-sms-bomber.git
cd bd-sms-bomber
bash install.sh
```

## Usage

```bash
# 1. scrape free proxies
python proxy_fetch.py

# 2. harvest keys + endpoints from APKs / JS bundles
python keyhunter.py pathao.apk
python keyhunter.py https://example.com/app.js

# 3. auto-register free-tier gateways (edit GATEWAYS in autoreg.py first)
python autoreg.py

# 4. set targets
echo "01712345678" > numbers.txt

# 5. bomb
python bomber.py --file
# or single target:
python bomber.py 01712345678
```

## Files

| file | purpose |
|------|---------|
| `bomber.py` | main threaded dispatcher |
| `keyhunter.py` | extracts API keys from APKs / JS |
| `autoreg.py` | registers throwaway accounts on free-tier gateways |
| `proxy_fetch.py` | scrapes + validates free proxies |
| `run.sh` | one-command launcher |
| `install.sh` | installer (linux/mac/termux) |
| `gateways.json` | manual gateway pool |
| `numbers.txt` | targets, one per line |

## License

MIT.
