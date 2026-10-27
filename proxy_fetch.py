#!/usr/bin/env python3
"""Scrape + validate free HTTP proxies into proxies.txt."""
import concurrent.futures as cf
import requests

SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
]

CHECK_URL = "http://httpbin.org/ip"
TIMEOUT = 6
WORKERS = 32


def fetch():
    out = set()
    for u in SOURCES:
        try:
            r = requests.get(u, timeout=15)
            for line in r.text.splitlines():
                line = line.strip()
                if line and ":" in line and not line.startswith("#"):
                    out.add("http://" + line)
        except Exception:
            pass
    return sorted(out)


def check(p):
    try:
        r = requests.get(CHECK_URL, proxies={"http": p, "https": p}, timeout=TIMEOUT)
        return p if r.status_code == 200 else None
    except Exception:
        return None


def main():
    raw = fetch()
    print(f"[+] scraped {len(raw)} candidate proxies, validating with {WORKERS} workers...")
    live = []
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for r in ex.map(check, raw):
            if r:
                live.append(r)
                if len(live) % 10 == 0:
                    print(f"\r[+] {len(live)} live", end="", flush=True)
    with open("proxies.txt", "w") as f:
        f.write("\n".join(live))
    print(f"\n[+] wrote {len(live)} live proxies to proxies.txt")


if __name__ == "__main__":
    main()
