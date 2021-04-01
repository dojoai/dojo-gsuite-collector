from __future__ import print_function

import logging
from base64 import urlsafe_b64encode
from email.mime.text import MIMEText
from googleapiclient.discovery import build

import config
from process_data.get_bigquery import get_credentials

def create_message(to, status, id):
    url = 'https://docs.google.com/spreadsheets/d/' + id
    if status == 'Complete':
        message_text = "Hello, <br><br> Your request to load data into BigQuery has been completed. Please check your " \
                       "<a href='" + url + "'>spreadsheet.</a> "
    else:
        message_text = "Hello, <br><br> Your request to load data into BigQuery has failed. Please check your " \
                       "Bigquery table to see if any data has been populated and your <a href='" + url + \
                       "'>spreadsheet.</a> "
    subject = 'Dojo Collector'
    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['from'] = config.ADMIN_EMAIL
    message['subject'] = subject
    encoded_message = urlsafe_b64encode(message.as_bytes())
    return {'raw': encoded_message.decode()}

def send_confirmation_email(to, status, id):
    try:
        credentials = get_credentials()
        message = create_message(to, status, id)
        user_id = config.ADMIN_EMAIL
        delegated_credentials = credentials.with_subject(user_id)
        service = build('gmail', 'v1', credentials=delegated_credentials)
        service.users().messages().send(userId=user_id, body=message).execute()
    except:
        pass
