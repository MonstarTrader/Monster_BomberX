#!/usr/bin/env python3
"""Extract API keys + SMS endpoints from decompiled APKs or JS bundles."""
import os
import re
import shutil
import subprocess
import sys

PATTERNS = [
    r"api[_-]?key['\"\s:=]+([A-Za-z0-9_\-]{16,})",
    r"apikey['\"\s:=]+([A-Za-z0-9_\-]{16,})",
    r"Authorization['\"\s:=]+Bearer\s+([A-Za-z0-9_\-\.]{16,})",
    r"Bearer\s+([A-Za-z0-9_\-\.]{16,})",
    r"token['\"\s:=]+([A-Za-z0-9_\-]{20,})",
    r"secret['\"\s:=]+([A-Za-z0-9_\-]{16,})",
    r"client[_-]?secret['\"\s:=]+([A-Za-z0-9_\-]{16,})",
]
SMS_HINTS = [
    "otp", "send_sms", "sendsms", "sms/send", "verify", "verification",
    "send_otp", "otp/send", "resend", "sms/api", "messages",
]
URL_RE = re.compile(r"https?://[^\s'\"<>]+")


def decompile_apk(apk, outdir):
    if not os.path.exists(outdir):
        if shutil.which("apktool") is None:
            print("[!] apktool not found on PATH. install it first (see README).")
            sys.exit(1)
        subprocess.run(
            ["apktool", "d", "-f", apk, "-o", outdir],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    return outdir


def scan_tree(root):
    keys, urls = set(), set()
    for dirpath, _, files in os.walk(root):
        for f in files:
            p = os.path.join(dirpath, f)
            try:
                data = open(p, "rb").read().decode("utf-8", "ignore")
            except Exception:
                continue
            for pat in PATTERNS:
                keys |= set(re.findall(pat, data, re.I))
            for u in URL_RE.findall(data):
                if any(h in u.lower() for h in SMS_HINTS):
                    urls.add(u)
    return keys, urls


def scan_bundle(src):
    if src.startswith("http"):
        import requests
        data = requests.get(src, timeout=20).text
    else:
        data = open(src, encoding="utf-8", errors="ignore").read()
    keys = set()
    for pat in PATTERNS:
        keys |= set(re.findall(pat, data, re.I))
    urls = {u for u in URL_RE.findall(data) if any(h in u.lower() for h in SMS_HINTS)}
    return keys, urls


def append_lines(path, items):
    existing = set()
    if os.path.exists(path):
        existing = set(l.strip() for l in open(path) if l.strip())
    existing |= set(items)
    with open(path, "w") as f:
        f.write("\n".join(sorted(existing)))
    return len(existing)


def main():
    if len(sys.argv) < 2:
        print("usage: keyhunter.py <apk|js-file|https-url>")
        sys.exit(1)

    target = sys.argv[1]
    os.makedirs("harvest", exist_ok=True)

    if target.lower().endswith(".apk"):
        out = "decompiled_" + os.path.basename(target).replace(".apk", "")
        decompile_apk(target, out)
        keys, urls = scan_tree(out)
    else:
        keys, urls = scan_bundle(target)

    print("== keys ==")
    for k in sorted(keys):
        print(k)
    print("\n== sms endpoints ==")
    for u in sorted(urls):
        print(u)

    nk = append_lines("harvest/keys.txt", keys)
    nu = append_lines("harvest/endpoints.txt", urls)
    print(f"\n[+] harvest now holds {nk} keys, {nu} endpoints")


if __name__ == "__main__":
    main()
