"""Device networking gate. The host test runner injects its own adapter."""


def create_transport():
    # Do not enable synchronous requests or threads on unverified firmware.
    # Host-only Azure tests replace this module; no host networking code is
    # included in the deployable app or executed on a physical badge.
    return None
