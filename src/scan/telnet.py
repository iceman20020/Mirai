import socket


def telnet_check(host, port=23, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        banner = s.recv(256)
        s.close()
        return banner
    except Exception:
        return None
