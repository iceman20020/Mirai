ARCH = {
    "arm":    "node_arm",
    "mips":   "node_mips",
    "x86":    "node_x86",
    "x86_64": "node_x64",
    "aarch64": "node_arm64",
}


def for_arch(arch):
    return ARCH.get(arch, "node_x86")
