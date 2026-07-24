from __future__ import annotations

import sys

from ..check import BootstrapCheck


class PythonCheck(BootstrapCheck):

    stage = "Preflight"
    name = "Python Version"

    def execute(self):

        version = sys.version_info

        ok = version >= (3, 10)

        return ok, f"{version.major}.{version.minor}.{version.micro}"
