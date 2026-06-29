#!/usr/bin/env python3

from dev.doctor.registry import discover
from dev.doctor.report import Report


def main():

    report = Report()

    for check_cls in discover():
        report.add(check_cls().run())

    report.print()


if __name__ == "__main__":
    main()
