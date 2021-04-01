from google.cloud import bigquery

import config
from process_data.get_bigquery import get_bigquery_client

def create_tables(project_id):
    bigquery_client = get_bigquery_client(project_id)
    datasetId_gcp = config.gcp_dataset_id
    datasetId = "{}.{}".format(bigquery_client.project, datasetId_gcp)
    resource_names = ['calendar_list', 'email_list']
    output = ""

    try:
        dataset = bigquery.Dataset(datasetId)
        bigquery_client.create_dataset(dataset, timeout=30)
    except:
        error_output = "Dataset already created " + datasetId

    for i in range(len(resource_names)):
        table_id = datasetId + '.' + resource_names[i]
        file_path = "bigquery_schema/" + resource_names[i] + "_schema.json"
        schema = bigquery_client.schema_from_json(file_path)
        table = bigquery.Table(table_id, schema=schema)

        try:
            bigquery_client.create_table(table)
            create_output = "Created table " + table_id
            output += create_output
            output += '\n'
        except:
            error_output = "Table already created " + table_id
            output += error_output
            output += '\n'

    return output
