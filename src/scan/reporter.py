def report(host, port, banner):
    try:
        print(f"[scan] {host}:{port} {banner[:60]!r}")
    except Exception:
        pass
