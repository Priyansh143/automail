# src/gmail_reader.py

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64
import email
from bs4 import BeautifulSoup
from cleaning import clean_email_body

def get_service():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    flow = InstalledAppFlow.from_client_secrets_file('creds/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(service):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=10).execute()
    messages = results.get('messages', [])
    return messages if messages else []

def extract_email_details(service, message_id):
    import re
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    headers = message['payload']['headers']

    def get_header(name):
        return next((h['value'] for h in headers if h['name'].lower() == name.lower()), None)

    subject = get_header('Subject')
    sender = get_header('From')
    date = get_header('Date')
    snippet = message.get('snippet')

    def decode_and_clean(data, mime_type):
        decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        if mime_type == 'text/html':
            soup = BeautifulSoup(decoded, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        else:
            text = decoded

        # Clean up excess whitespace and artifacts
        text = re.sub(r'\s+', ' ', text)
        text = text.replace(u'\xa0', ' ').strip()
        return text

    # Recursive part traversal
    def get_body(payload):
        if 'parts' in payload:
            for part in payload['parts']:
                result = get_body(part)
                if result:
                    return result
        else:
            body_data = payload.get('body', {}).get('data')
            mime_type = payload.get('mimeType', '')
            if body_data and ('text/plain' in mime_type or 'text/html' in mime_type):
                return decode_and_clean(body_data, mime_type)
        return ""

    body = get_body(message['payload'])

    return {
        'subject': subject,
        'from': sender,
        'date': date,
        'snippet': snippet,
        'body': body
    }


if __name__ == "__main__":
    service = get_service()
    unread_messages = get_unread_emails(service)

    if not unread_messages:
        print("No unread messages.")
    else:
        print(f"Found {len(unread_messages)} unread messages.\n")
        for msg in unread_messages:
            msg_id = msg['id']
            email_data = extract_email_details(service, msg_id)
            print("="*40)
            print(f"From: {email_data['from']}")
            print(f"Subject: {email_data['subject']}")
            print(f"Date: {email_data['date']}")
            print(f"Body:\n{clean_email_body(email_data['body'][:500])}")  # Preview first 500 chars
