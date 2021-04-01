from google.cloud import bigquery
from google.oauth2 import service_account

import config

SERVICE_ACCOUNT_FILE = config.SERVICE_ACCOUNT_FILE
SCOPES = config.SCOPES

def output_bigquery(project_id, table_id, rows_list):
    bigquery_client = get_bigquery_client(project_id)

    list_table = bigquery_client.get_table(table_id)
    errors = bigquery_client.insert_rows_json(list_table, rows_list)
    print("ERRORS: ", errors)
    return errors

def delete_backend_data(project_id):
    bigquery_client = get_bigquery_client(project_id)
    query = "DELETE FROM `" + project_id + ".Dojo_Table.calendar_list` WHERE true; " \
                                           "DELETE FROM `" + project_id + ".Dojo_Table.email_list` WHERE true;"
    query_job = bigquery_client.query(query)
    try:
        query_job.result()
        return {"status": "Successfully cleared data from BigQuery."}
    except Exception as e:
        return {
            "status": "Failed to clear data from BigQuery. This is likely because the data has been loaded into "
                      "BigQuery recently. Data is not able to be deleted from BigQuery until after 45 - 120 minutes "
                      "after it has been added."}

def get_bigquery_client(project_id):
    client = bigquery.Client(project=project_id)
    return client

def get_credentials():
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return credentials
