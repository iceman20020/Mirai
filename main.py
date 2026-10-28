#!/usr/bin/env python3
# main.py — cnc builder entry.
# prints banner, loads config, runs builder.

import os
import sys
import time
import random

BANNER = r"""
 ▄████▄   ▄▄▄        ██████  ██░ ██     ███▄ ▄███▓ ██▓ ██▀███   ▄▄▄       ██▓
▒██▀ ▀█  ▒████▄    ▒██    ▒ ▓██░ ██▒   ▓██▒▀█▀ ██▒▓██▒▓██ ▒ ██▒▒████▄    ▓██▒
▒▓█    ▄ ▒██  ▀█▄  ░ ▓██▄   ▒██▀▀██░   ▓██    ▓██░▒██▒▓██ ░▄█ ▒▒██  ▀█▄  ▒██▒
▒▓▓▄ ▄██▒░██▄▄▄▄██   ▒   ██▒░▓█ ░██    ▒██    ▒██ ░██░▒██▀▀█▄  ░██▄▄▄▄██ ░██░
▒ ▓███▀ ░ ▓█   ▓██▒▒██████▒▒░▓█▒░██▓   ▒██▒   ░██▒░██░░██▓ ▒██▒ ▓█   ▓██▒░██░
░ ░▒ ▒  ░ ▒▒   ▓▒█░▒ ▒▓▒ ▒ ░ ▒ ░░▒░▒   ░ ▒░   ░  ░░▓  ░ ▒▓ ░▒▓░ ▒▒   ▓▒█░░▓
  ░  ▒     ▒   ▒▒ ░░ ░▒  ░ ░ ▒ ░▒░ ░   ░  ░      ░ ▒ ░  ░▒ ░ ▒░  ▒   ▒▒ ░ ▒ ░
░          ░   ▒   ░  ░  ░   ░  ░░ ░   ░      ░    ▒ ░  ░░   ░   ░   ▒    ▒ ░
░ ░            ░  ░      ░   ░  ░  ░          ░    ░     ░           ░  ░ ░
░
"""

RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
GREEN = "\033[38;5;46m"
GREY  = "\033[38;5;240m"
WHITE = "\033[38;5;255m"
RED   = "\033[38;5;196m"
CYAN  = "\033[38;5;51m"
CLEAR = "\033[2J\033[H"
HIDE  = "\033[?25l"
SHOW  = "\033[?25h"


def _supports_color():
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")
    return True


USE_COLOR = _supports_color()


def c(code, text):
    return f"{code}{text}{RESET}" if USE_COLOR else text


def clear():
    if USE_COLOR:
        sys.stdout.write(CLEAR)
        sys.stdout.flush()


def hide_cursor():
    if USE_COLOR:
        sys.stdout.write(HIDE)
        sys.stdout.flush()


def show_cursor():
    if USE_COLOR:
        sys.stdout.write(SHOW)
        sys.stdout.flush()


def glitch_line(line):
    chars = "░▒▓█▄▀#@%&$*"
    out = []
    for ch in line:
        if ch == " ":
            out.append(" ")
        elif random.random() < 0.08:
            out.append(random.choice(chars))
        else:
            out.append(ch)
    return "".join(out)


def print_banner():
    clear()
    hide_cursor()

    lines = BANNER.strip("\n").split("\n")

    for _ in range(3):
        for line in lines:
            sys.stdout.write(c(GREY, glitch_line(line)) + "\n")
        sys.stdout.flush()
        time.sleep(0.06)
        sys.stdout.write("\033[F" * len(lines))
        sys.stdout.flush()

    for line in lines:
        sys.stdout.write(c(GREEN, line) + "\n")
        sys.stdout.flush()
        time.sleep(0.04)

    sys.stdout.write("\033[F" * len(lines))
    for i, line in enumerate(lines):
        sys.stdout.write(c(BOLD + WHITE, line) + "\n")
        sys.stdout.flush()
        time.sleep(0.03)
        sys.stdout.write("\033[F")
    sys.stdout.write("\n")

    sub = "  cnc builder · v2.1.4 · node telemetry relay"
    for ch in sub:
        sys.stdout.write(c(DIM + GREY, ch))
        sys.stdout.flush()
        time.sleep(0.012)
    sys.stdout.write("\n\n")

    show_cursor()


def status(tag, msg, color=GREEN):
    ts = time.strftime("%H:%M:%S")
    print(f"{c(GREY, '['+ts+']')} {c(color, tag.ljust(6))} {msg}")


def load_config(path="config.yaml"):
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    try:
        print_banner()
        status("init", "loading config.yaml")
        cfg = load_config()
        status("init", f"cnc host: {cfg['c2']['host']}:{cfg['c2']['port']}")

        from src import builder
        status("build", "compiling node")
        builder.build(cfg)
        status("build", "node compiled → out/bot.py")

        status("done", "ready. run cnc: python -m cnc.server", color=CYAN)

    except KeyboardInterrupt:
        show_cursor()
        print()
        status("abort", "interrupted by user", color=RED)
        sys.exit(130)
    except Exception as e:
        show_cursor()
        status("error", str(e), color=RED)
        sys.exit(1)
    finally:
        show_cursor()


if __name__ == "__main__":
    main()
