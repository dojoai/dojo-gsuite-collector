from __future__ import print_function

import dateutil.parser
import logging
import re
import time
from apiclient import errors
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

import config
from process_data.get_bigquery import output_bigquery, get_credentials

TABLEID = config.gcp_dataset_id + '.email_list'


def get_email_list(users, start, end, project_id):
    credentials = get_credentials()
    new_end = datetime.strptime(end, '%Y-%m-%d')
    end_date = new_end + timedelta(days=1)
    end_date_str = datetime.strftime(end_date, '%Y-%m-%d')
    query = "before:" + end_date_str + " after:" + start
    rows_list = []
    page_token = None
    for user in users.values():
        try:
            while True:
                delegated_credentials = credentials.with_subject(user)
                service = build('gmail', 'v1', credentials=delegated_credentials)
                emails = service.users().threads().list(userId=user, q=query, pageToken=page_token).execute()
                threads = emails.get('threads', [])
                if not threads:
                    break
                else:
                    for thread in threads:
                        tdata = service.users().threads().get(userId=user, id=thread['id'], format='metadata',
                                                              metadataHeaders=['Date', 'To', 'From', 'Cc',
                                                                               'Bcc']).execute()
                        for message in tdata['messages']:
                            row = {}
                            date_str = ''
                            timestamp = None
                            to_email = ''
                            from_email = ''
                            cc_email = ''
                            headers = message['payload']['headers']
                            for header in headers:
                                if header['name'] == 'Date':
                                    timestamp = header['value']
                                    timestamp = timestamp.split(' (')[0]
                                    has_timezone = re.search(r"[A-Z]{3}(?<![A-Z]{4})(?![A-Z])", timestamp)
                                    has_dow = re.search(r"[A-Za-z]{3}[,](?<![A-Z]{4})(?![A-Z])", timestamp)
                                    if has_timezone:
                                        timestamp = timestamp.split(' ' + has_timezone.group())[0]
                                        date_str = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S").strftime(
                                            '%Y-%m-%d')
                                    elif not has_timezone and has_dow:
                                        date_str = datetime.strptime(timestamp, "%a, %d %b %Y %H:%M:%S %z").strftime(
                                            '%Y-%m-%d')
                                    elif not has_dow:
                                        date_str = datetime.strptime(timestamp, "%d %b %Y %H:%M:%S %z").strftime(
                                            '%Y-%m-%d')
                                if header['name'] == 'To':
                                    to_email = header['value']
                                if header['name'] == 'From':
                                    from_email = header['value']
                                if header['name'] == 'Cc':
                                    cc_email = header['value']

                            if date_str and date_str != '' and (from_email or to_email or cc_email):
                                row.update([('date', date_str), ('datetime', timestamp), ('from_email', from_email),
                                            ('to_email', to_email), ('cc_email', cc_email), ('owner', user)])
                                rows_list.append(row)
                    page_token = emails.get('nextPageToken', None)
                    if not page_token:
                        break
        except Exception as ex:
            print("An error occurred for ", user)
            print("The error is: ", ex)
            continue

    if len(rows_list) > 0:
        output_bigquery(project_id, TABLEID, rows_list)
    return rows_list
