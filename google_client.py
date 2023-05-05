from datetime import datetime, timedelta
from os import path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def google_auth():
    creds = None

    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

    if path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def google_service_builder(credentials, service_name, version):
    service = build(service_name, version, credentials=credentials)
    return service

def get_events(calendar_id):
    credentials = google_auth()
    service = google_service_builder(credentials, 'calendar', 'v3')
    
    # Call the Calendar API
    now = datetime.utcnow()
    now_iso = now.isoformat() + 'Z'  # 'Z' indicates UTC time
    tomorrow = now + timedelta(days=1) 
    tomorrow_iso = tomorrow.isoformat() + 'Z'

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=now_iso,
        timeMax=tomorrow_iso,
        maxResults=100, singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    events_clean = {}

    for event in events:
        date = event['start'].get('dateTime', event['start'].get('date'))
        if events_clean.get(date):
            events_clean[date].append(event['summary'])
        else:
            events_clean[date] = [event['summary']]
    return events_clean