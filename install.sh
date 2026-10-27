#!/usr/bin/env bash
set -e

echo "[+] installing bd-sms-bomber deps"

if [ -n "$PREFIX" ] && [ -d "$PREFIX" ]; then
    # --- Termux ---
    echo "[+] termux environment detected"
    pkg install -y python git openjdk-17 python-cryptography curl >/dev/null 2>&1 || true
    pip install --upgrade pip
    pip install -r requirements.txt

    if ! command -v apktool >/dev/null 2>&1; then
        mkdir -p "$PREFIX/share" "$PREFIX/bin"
        if [ ! -f "$PREFIX/share/apktool.jar" ]; then
            curl -sLo "$PREFIX/share/apktool.jar" \
                https://github.com/iBotPeaches/Apktool/releases/latest/download/apktool.jar
        fi
        cat > "$PREFIX/bin/apktool" <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
exec java -jar "$PREFIX/share/apktool.jar" "$@"
EOF
        chmod +x "$PREFIX/bin/apktool"
        echo "[+] apktool wrapper installed"
    fi
else
    # --- Linux / macOS / WSL ---
    echo "[+] linux/mac/wsl detected"
    if command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y python3 python3-pip openjdk-17-jre curl unzip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip java-17-openjdk curl unzip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip jre17-openjdk curl unzip
    elif command -v brew >/dev/null 2>&1; then
        brew install python openjdk curl unzip
    fi
    pip3 install --upgrade pip
    pip3 install -r requirements.txt

    if ! command -v apktool >/dev/null 2>&1; then
        sudo curl -sLo /usr/local/bin/apktool \
            https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool
        sudo curl -sLo /usr/local/bin/apktool.jar \
            https://github.com/iBotPeaches/Apktool/releases/latest/download/apktool.jar
        sudo chmod +x /usr/local/bin/apktool
        echo "[+] apktool installed"
    fi
fi

mkdir -p harvest
touch harvest/.gitkeep
echo "[+] done."
echo "[+] next: python proxy_fetch.py && python bomber.py --help"
