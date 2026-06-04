from googleapiclient.discovery import build
from src.services.gmail.auth import gmail_authenticate


def get_recent_emails(max_results=10):
    creds = gmail_authenticate()
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me',
        maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    emails = []

    for msg in messages:
        message = service.users().messages().get(
            userId='me',
            id=msg['id']
        ).execute()

        headers = message['payload'].get('headers', [])

        subject = ""
        sender = ""

        for h in headers:
            if h['name'] == 'Subject':
                subject = h['value']

            if h['name'] == 'From':
                sender = h['value']

        emails.append({
            "id": msg['id'],
            "subject": subject,
            "from": sender
        })

    return emails
