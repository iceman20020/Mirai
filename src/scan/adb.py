import socket


def adb_check(host, port=5555, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"\x00\x00\x00\x04host")
        banner = s.recv(256)
        s.close()
        return banner
    except Exception:
        return None
