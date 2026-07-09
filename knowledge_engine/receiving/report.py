from collections import Counter


def print_report(accepted, rejected):

    print()
    print("=" * 70)
    print("JARVIS RECEIVING REPORT")
    print("=" * 70)

    print()

    print(f"Accepted : {len(accepted)}")
    print(f"Rejected : {len(rejected)}")

    print()

    counts = Counter(reason for _, reason in rejected)

    for reason, count in counts.items():
        print(f"{count:6} {reason}")
