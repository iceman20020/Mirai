import socket


def tcp_flood(host, port, duration=30):
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.sendall(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
        s.close()
    except Exception:
        pass
