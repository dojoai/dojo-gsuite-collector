from __future__ import print_function

import dateutil.parser
import logging
from apiclient import errors
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build

import config
from process_data.get_bigquery import output_bigquery, get_credentials

TABLEID = config.gcp_dataset_id + '.calendar_list'

def get_calendar_list(users, start, end, intext, domain_list, project_id):
    credentials = get_credentials()
    rows_list = []
    page_token = None
    format_start = datetime.strptime(start, '%Y-%m-%d')
    format_end = datetime.strptime(end, '%Y-%m-%d')
    start_isoformat = datetime.combine(format_start, datetime.min.time()).isoformat() + 'Z'
    end_isoformat = datetime.combine(format_end, datetime.max.time()).isoformat() + 'Z'
    for user in users.values():
        try:
            while True:
                delegated_credentials = credentials.with_subject(user)
                service = build('calendar', 'v3', credentials=delegated_credentials)
                events_result = service.events().list(calendarId=user, timeMin=start_isoformat, timeMax=end_isoformat,
                                                      singleEvents=True, orderBy='startTime',
                                                      pageToken=page_token).execute()
                events = events_result.get('items', [])
                if not events:
                    break
                else:
                    for event in events:
                        attendees_list = ''
                        attendee = 0
                        organizer = event['organizer']['email']
                        if organizer == user:
                            get_attendees = event.get('attendees', [])
                            if len(get_attendees) > 1:
                                for j in range(len(get_attendees)):
                                    if get_attendees[j]['responseStatus'] == 'accepted':
                                        attendee_email = get_attendees[j]['email']
                                        if intext == 'int':
                                            attendee_email = mask_email(attendee_email, domain_list)
                                        attendees_list += attendee_email + ', '
                                        attendee = attendee + 1

                                if attendee > 1:
                                    if 'start' in event:
                                        if 'dateTime' in event['start']:
                                            list = {}
                                            location = ''
                                            event_start = event['start'].get('dateTime', event['start'].get('date'))
                                            event_end = event['end'].get('dateTime', event['end'].get('date'))
                                            date = datetime.strptime(event_start, "%Y-%m-%dT%H:%M:%S%z").strftime(
                                                '%Y-%m-%d')
                                            hour = (dateutil.parser.isoparse(event_end) - dateutil.parser.isoparse(
                                                event_start)).seconds
                                            if 'location' in event:
                                                location = event['location']
                                            duration = float(hour) / 3600
                                            list.update(
                                                [('date', date), ('datetime', event_start), ('num_attendees', attendee),
                                                 ('duration', duration), ('location', location),
                                                 ('attendees_list', attendees_list.rstrip(', ')), ('owner', user)])
                                            rows_list.append(list)
                    page_token = events_result.get('nextPageToken', None)
                    if not page_token:
                        break
        except Exception as ex:
            print("An error occurred for ", user)
            print("The error is: ", ex)
            continue
    if len(rows_list) > 0:
        output_bigquery(project_id, TABLEID, rows_list)
    return rows_list

def mask_email(attendee_email, domain_list):
    if not any(x in attendee_email for x in domain_list):
        attendee_email = 'EXTERNAL'
    return attendee_email
