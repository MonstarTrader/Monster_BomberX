#!/usr/bin/env python3
"""Auto-register throwaway accounts on free-tier SMS gateways, save keys."""
import json
import os
import random
import re
import string
import sys

import requests

GATEWAYS = [
    # template — fill with real provider details
    # {
    #     "name": "bulksmsbd",
    #     "reg_url": "https://bulksmsbd.net/register",
    #     "fields": {
    #         "name": "NAME", "email": "EMAIL",
    #         "password": "PASS", "phone": "PHONE",
    #     },
    #     "key_path": "https://bulksmsbd.net/dashboard",
    #     "key_regex": r'api[_-]?key["\'\s:]+([A-Za-z0-9]{20,})',
    # },
]

DUMMY_PHONE = "01700000000"


def fake_email():
    return "".join(random.choices(string.ascii_lowercase, k=10)) + "@mailinator.com"


def fake_pass():
    return "".join(random.choices(string.ascii_letters + string.digits, k=14)) + "!"


def register(gw):
    s = requests.Session()
    data = {}
    for k, v in gw["fields"].items():
        if v == "NAME":
            data[k] = "auto_" + "".join(random.choices(string.digits, k=6))
        elif v == "EMAIL":
            data[k] = fake_email()
        elif v == "PASS":
            data[k] = fake_pass()
        elif v == "PHONE":
            data[k] = DUMMY_PHONE
        else:
            data[k] = v
    try:
        r = s.post(gw["reg_url"], data=data, timeout=20)
    except Exception as e:
        print(f"[!] {gw['name']} register failed: {e}")
        return None

    if r.status_code not in (200, 201, 302):
        print(f"[!] {gw['name']} register status {r.status_code}")
        return None

    try:
        dash = s.get(gw["key_path"], timeout=20)
    except Exception as e:
        print(f"[!] {gw['name']} dashboard fetch failed: {e}")
        return None

    m = re.search(gw["key_regex"], dash.text)
    if m:
        return m.group(1)
    print(f"[!] {gw['name']} key not found in dashboard HTML")
    return None


def main():
    if not GATEWAYS:
        print("[!] GATEWAYS list is empty — edit autoreg.py and add real providers first.")
        sys.exit(1)

    os.makedirs("harvest", exist_ok=True)
    path = "harvest/registered_keys.json"
    found = {}
    if os.path.exists(path):
        try:
            found = json.load(open(path))
        except Exception:
            found = {}

    for gw in GATEWAYS:
        print(f"[+] registering on {gw['name']}...")
        key = register(gw)
        if key:
            print(f"[+] got key: {key}")
            found[gw["name"]] = key
        else:
            print(f"[-] no key for {gw['name']}")

    with open(path, "w") as f:
        json.dump(found, f, indent=2)
    print(f"\n[+] {len(found)} keys in {path}")


if __name__ == "__main__":
    main()
