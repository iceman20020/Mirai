import os


def stage(target_path, source_bytes):
    # writes staged payload to disk on target (executed via remote_exec)
    try:
        with open(target_path, "wb") as f:
            f.write(source_bytes)
        return True
    except Exception:
        return False
