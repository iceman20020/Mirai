import socket


def ssh_check(host, port=22, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        banner = s.recv(256)
        s.close()
        return banner
    except Exception:
        return None
