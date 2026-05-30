from src.services.gmail.reader import get_recent_emails
from src.services.gmail.classifier import classify_email

emails = get_recent_emails()

for email in emails:
    result = classify_email(email["from"], email["subject"])

    print("=" * 50)
    print("FROM:", email["from"])
    print("SUBJECT:", email["subject"])
    print("CATEGORY:", result["category"])
    print("PRIORITY:", result["priority"])
    print("RISK:", result["risk"])
