import urllib.request


def http_flood(url, duration=30):
    for _ in range(duration):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            break
