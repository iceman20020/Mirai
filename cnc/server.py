# cnc/server.py — cli launcher for the c2 listener.

import sys
import yaml
from src import cnc


def main():
    cfg = yaml.safe_load(open("config.yaml"))
    host = cfg["c2"]["host"]
    port = cfg["c2"]["port"]
    secret = cfg["c2"]["secret"]
    cnc.serve(host, port, secret)


if __name__ == "__main__":
    main()
