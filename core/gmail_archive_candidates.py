from googleapiclient.discovery import build

from src.services.gmail.auth import gmail_authenticate
from src.services.gmail.classifier import classify_email


MAX_EMAILS = 200


def main():
    creds = gmail_authenticate()

    service = build(
        "gmail",
        "v1",
        credentials=creds
    )

    print(f"\n[JARVIS] Reviewing latest {MAX_EMAILS} emails...\n")

    results = service.users().messages().list(
        userId="me",
        maxResults=MAX_EMAILS
    ).execute()

    messages = results.get("messages", [])

    archive_candidates = []

    for i, msg in enumerate(messages, start=1):

        print(f"[JARVIS] Processing {i}/{len(messages)}")

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

            result = classify_email(sender, subject)

            category = result["category"]
            priority = result["priority"]

            SAFE_ARCHIVE = [
                "promotions"
            ]

            if category in SAFE_ARCHIVE and priority != "high":

                archive_candidates.append({
                    "id": msg["id"],
                    "sender": sender,
                    "subject": subject,
                    "category": category
                })

        except Exception as e:
            print(f"[ERROR] {e}")

    print("\n" + "=" * 60)
    print("SAFE ARCHIVE CANDIDATES")
    print("=" * 60)

    for email in archive_candidates:

        print(f"\nFROM: {email['sender']}")
        print(f"SUBJECT: {email['subject']}")
        print(f"CATEGORY: {email['category']}")

    print("\n")
    print(f"[JARVIS] Found {len(archive_candidates)} safe archive candidates.")


if __name__ == "__main__":
    main()
