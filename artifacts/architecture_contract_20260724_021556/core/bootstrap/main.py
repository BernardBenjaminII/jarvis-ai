from __future__ import annotations

from .runner import BootstrapRunner


def main():

    ok = BootstrapRunner().run()

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":

    main()
