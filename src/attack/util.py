import socket
import random


def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def rand_port():
    return random.randint(1024, 65535)


def resolve(host):
    try:
        return socket.gethostbyname(host)
    except Exception:
        return host
