def classify_email(sender: str, subject: str) -> dict:
    text = f"{sender} {subject}".lower()

    category = "review"
    priority = "normal"
    risk = "low"

    if any(x in text for x in ["openai", "security key", "passkey", "login", "password"]):
        category = "security"
        priority = "high"

    elif any(x in text for x in ["netflix", "xda", "newsletter", "deals", "savings", "bonus"]):
        category = "promotions"
        priority = "low"

    elif any(x in text for x in ["robinhood", "vote", "meeting", "bank", "payment", "invoice"]):
        category = "finance"
        priority = "medium"

    elif any(x in text for x in ["immowelt", "immobilien", "apartment", "housing", "hochheim"]):
        category = "housing"
        priority = "medium"

    elif any(x in text for x in ["coding", "developer", "python", "github", "openai"]):
        category = "tech"
        priority = "medium"

    if any(x in text for x in ["urgent", "verify now", "account locked", "gift card"]):
        risk = "possible phishing"

    return {
        "category": category,
        "priority": priority,
        "risk": risk
    }
