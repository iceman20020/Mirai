import socket


def http_check(host, port=80, timeout=3):
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(b"HEAD / HTTP/1.0\r\n\r\n")
        banner = s.recv(256)
        s.close()
        return banner
    except Exception:
        return None
