from __future__ import print_function

import logging
from apiclient import errors
from googleapiclient.discovery import build

import config
from process_data.get_bigquery import get_credentials

def get_user_list(spreadsheet_id, range_name):
    credentials = get_credentials()
    users = {}
    try:
        delegated_credentials = credentials.with_subject(config.ADMIN_EMAIL)
        service = build('sheets', 'v4', credentials=delegated_credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        count = 0
        if not values:
            pass
        else:
            for row in values:
                count += 1
                if count != 1:
                    users.update([(count, row[0])])

    except:
        return {'msg': 'failed to get user list'}
    return users
