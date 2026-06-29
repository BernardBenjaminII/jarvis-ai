#!/usr/bin/env python3

from dev.doctor.architecture import run as architecture_check


def main():
    print("JARVIS DOCTOR")
    print("=" * 70)
    architecture_check()


if __name__ == "__main__":
    main()
