# mirai-gen

Botnet source builder — scans, brutes, stages a node, reports back to cnc.

## layout

- `src/attack/` — flood vectors
- `src/scan/` — telnet/ssh/adb/http scanners
- `src/loader/` — payload staging
- `src/persist/` — node persistence + health
- `src/cnc.py` — c2 listener
- `cnc/` — dashboard helpers
- `out/` — generated node

## usage
