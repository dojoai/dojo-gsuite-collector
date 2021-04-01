import os

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/calendar.events.readonly',
          'https://www.googleapis.com/auth/spreadsheets.readonly', 'https://www.googleapis.com/auth/gmail.send']
SERVICE_ACCOUNT_FILE = 'credential.json'
gcp_dataset_id = "Dojo_Table"
ADMIN_EMAIL = os.environ['ADMIN_EMAIL']
CREDENTIALS_FILE = os.environ['CREDENTIALS_FILE']
