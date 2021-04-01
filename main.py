import gdown
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, request
from google.cloud import storage

import config
from process_data.create_bigquery_tables import create_tables
from process_data.get_bigquery import delete_backend_data
from process_data.get_calendar import get_calendar_list
from process_data.get_email import get_email_list
from process_data.get_user import get_user_list
from process_data.send_email import send_confirmation_email

app = Flask(__name__)

try:
    if not os.path.exists(config.SERVICE_ACCOUNT_FILE) and config.CREDENTIALS_FILE:
        credentials_file = config.CREDENTIALS_FILE
        parts = credentials_file.split('/')
        file_id = parts[5]
        url = 'https://drive.google.com/uc?id={}'.format(file_id)
        output = config.SERVICE_ACCOUNT_FILE
        gdown.download(url, output, quiet=False)
    else:
        print("{} already exists".format(config.SERVICE_ACCOUNT_FILE))
except Exception as ex:
    print(ex)


@app.route('/status')
def status():
    return {"msg": "Your Cloud Run Service is working normally."}

@app.route('/delete_backend_data/<project_id>')
def delete_data(project_id):
    return delete_backend_data(project_id)

@app.route("/create_bigquery_tables/<project_id>")
def create_bigquery_tables(project_id):
    if request.method == 'GET':
        return create_tables(project_id)
    else:
        return {"status": 'An error occurred.'}

@app.route("/get_data")
def main():
    response = {}
    try:
        spreadsheet_id = request.args.get('spreadsheetId')
        range = request.args.get('range')
        start = request.args.get('start')
        end = request.args.get('end')
        intext = request.args.get('intext')
        append_overwrite = request.args.get('appendOverwrite')
        domain = request.args.get('domain')
        calendar = request.args.get('calendar')
        email = request.args.get('email')
        email_address = request.args.get('email_address')
        project_id = request.args.get('project_id')
        users = get_user_list(spreadsheet_id, range)

        num_users = len(users.keys())
        if num_users == 0:
            return {
                "status": "Process aborted because no users have been specified in the Users List tab. Please specify "
                          "for which users the Collector should run."}

        domain_list = []
        response.update(
            [('spreadsheetId', spreadsheet_id), ('range', range), ('start', start), ('end', end), ('intext', intext),
             ('appendOverwrite', append_overwrite), ('domain', domain), ('calendar', calendar), ('email', email)])
        if ',' in domain:
            domain_list = domain.split(",")
        else:
            domain_list.append(domain)

        if append_overwrite == 'overwrite':
            overwrite_status = delete_backend_data(project_id)
            if 'status' in overwrite_status and not 'Successfully cleared' in overwrite_status['status']:
                return {
                    "status": "Process aborted because system was unable to clear data from BigQuery and Overwrite "
                              "data was requested. This is likely because the data has been loaded into BigQuery "
                              "recently. Data is not able to be deleted from BigQuery until after 45 - 90 minutes "
                              "after it has been added."}

        if calendar == 'on':
            get_calendar_list(users, start, end, intext, domain_list, project_id)

        if email == 'on':
            get_email_list(users, start, end, project_id)

        run_status = "Complete"
        send_confirmation_email(email_address, run_status, spreadsheet_id)
        response.update([('status', run_status)])
    except Exception as e:
        run_status = repr(e)
        try:
            send_confirmation_email(email_address, run_status, spreadsheet_id)
        except:
            run_status += ": Failed to send email"
        response.update([('status', run_status)])

    return {"status": response['status']}
