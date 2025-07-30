# src/gmail_reader.py
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import base64
import email
from bs4 import BeautifulSoup
from cleaning import clean_email_body
from exception import CustomException
from logger import logging
import os
import re

def get_service():
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('creds/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(service, maxResults):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread", maxResults=maxResults).execute()
    messages = results.get('messages', [])
    return messages if messages else []

def extract_all_email_details(service, messages):
    email_details_list = []

    for msg in messages:
        message_id = msg['id']
        try:
            message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
            # print(message)
            headers = message['payload']['headers']
            # print(headers)

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
                return re.sub(r'\s+', ' ', text).replace(u'\xa0', ' ').strip()

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
            
            print("subject: ", subject)
            print('body', body)
            
            
            email_details_list.append({
                'subject': subject,
                'from': sender,
                'date': date,
                'snippet': snippet,
                'body': body
            })

        except Exception as e:
            logging.error(f"Failed to extract email with ID {message_id}: {str(e)}")

    return email_details_list


# if __name__ == "__main__":

#     service = get_service()
#     messages = get_unread_emails(service, maxResults=10)
#     all_email_data = extract_all_email_details(service, messages)
#     # print(messages)