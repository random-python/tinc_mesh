"""
"""

import os

this_dir = os.path.dirname(os.path.abspath(__file__))

service_list = [
    "/etc/systemd/system/tinc.service",
    "/etc/systemd/system/tinc@.service",
]


def service_install():
    ""
    for service in service_list:
        source = f"{this_dir}{service}"
        target = f"{service}"
        os.system(f"cp --force --verbose --preserve=mode {source} {target}")


def service_uninstall():
    ""
    for service in service_list:
        os.system(f"rm --force --verbose {service}")
