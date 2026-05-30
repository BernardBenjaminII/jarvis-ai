from googleapiclient.discovery import build
from src.services.gmail.auth import gmail_authenticate

creds = gmail_authenticate()

service = build('gmail', 'v1', credentials=creds)

results = service.users().labels().list(userId='me').execute()

labels = results.get('labels', [])

for label in labels:
    print(label['name'])
