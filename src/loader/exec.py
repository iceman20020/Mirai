import subprocess


def remote_exec(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
    except Exception as e:
        return str(e).encode()
