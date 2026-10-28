# cnc/state.py — per-node state cache.

STATE = {}


def get(addr):
    return STATE.setdefault(addr, {"last": 0, "tasks": []})


def update(addr, **kw):
    STATE.setdefault(addr, {}).update(kw)
