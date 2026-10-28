# cnc/webhook.py — helper for posting test embeds from operator side.

import json
import urllib.request


def send(url, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    return urllib.request.urlopen(req, timeout=10).read()
