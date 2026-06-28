from collections import Counter
from googleapiclient.discovery import build

from src.services.gmail.auth import gmail_authenticate
from src.services.gmail.classifier import classify_email


MAX_EMAILS = 50


def main():
    creds = gmail_authenticate()

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    print(f"\n[JARVIS] Scanning latest {MAX_EMAILS} emails...\n")

    results = service.users().messages().list(
        userId="me",
        maxResults=MAX_EMAILS
    ).execute()

    messages = results.get("messages", [])

    category_counter = Counter()
    sender_counter = Counter()
    priority_counter = Counter()
    risk_counter = Counter()

    for i, msg in enumerate(messages, start=1):

        print(f"[JARVIS] Processing email {i}/{len(messages)}")

        try:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"]
            ).execute()

            payload = message.get("payload", {})
            headers = payload.get("headers", [])

            subject = "(no subject)"
            sender = "(unknown sender)"

            for h in headers:

                if h.get("name") == "Subject":
                    subject = h.get("value", "(no subject)")

                elif h.get("name") == "From":
                    sender = h.get("value", "(unknown sender)")

            print("DEBUG SENDER:", sender)
            print("DEBUG SUBJECT:", subject)

            result = classify_email(sender, subject)

            print("DEBUG RESULT:", result)

            category_counter[result["category"]] += 1
            sender_counter[sender] += 1
            priority_counter[result["priority"]] += 1
            risk_counter[result["risk"]] += 1

        except Exception as e:
            print(f"[ERROR] {e}")

    print("\n" + "=" * 60)
    print("CATEGORY BREAKDOWN")
    print("=" * 60)

    for category, count in category_counter.most_common():
        print(f"{category:<20} {count}")

    print("\n" + "=" * 60)
    print("TOP SENDERS")
    print("=" * 60)

    for sender, count in sender_counter.most_common(15):
        print(f"{count:<5} {sender}")

    print("\n" + "=" * 60)
    print("PRIORITY BREAKDOWN")
    print("=" * 60)

    for priority, count in priority_counter.most_common():
        print(f"{priority:<10} {count}")

    print("\n" + "=" * 60)
    print("RISK BREAKDOWN")
    print("=" * 60)

    for risk, count in risk_counter.most_common():
        print(f"{risk:<20} {count}")

    print("\n[JARVIS] Cleanup analysis complete.\n")


if __name__ == "__main__":
    main()
