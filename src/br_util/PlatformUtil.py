import platform


def is_raspberry_pi():
    # Check CPU architecture (most Pis are arm or aarch64)
    arch = platform.machine().lower()
    if "arm" not in arch and "aarch64" not in arch:
        return False

    # Check /proc/device-tree/model (exists on Linux SBCs)
    try:
        with open("/proc/device-tree/model", "r") as f:
            model = f.read().lower()
        if "raspberry pi" in model:
            return True
    except FileNotFoundError:
        pass

    return False