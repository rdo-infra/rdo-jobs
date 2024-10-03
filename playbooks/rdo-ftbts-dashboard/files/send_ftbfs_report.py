#!/usr/bin/env python3
import csv
import datetime
from opensearchpy import OpenSearch, helpers
now = datetime.date.today()
opensearch_host = 'https://opensearch.rdoproject.org'
username = {{ ftbfs_es_creds.user }}
password = {{ ftbfs_es_creds.password }}
csv_file = '/tmp/ftbfs_report.csv'
index_name = 'ftbfs-rdoproject_org-{}'.format(now.strftime("%Y.%m.%d"))
urlprefix = 'opensearch'
# Connect to OpenSearch
client = OpenSearch(
    hosts=[opensearch_host],
    http_auth=(username, password),
    use_ssl=True,
    verify_certs=True,
    url_prefix=urlprefix
)
def format_date(date_str):
    try:
        # Convert the date string (e.g., '2024-10-09 08:52:34') to ISO 8601 (e.g., '2024-10-09T08:52:34Z')
        return datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').isoformat() + 'Z'
    except ValueError:
        return date_str
# Prepare bulk data for OpenSearch
def generate_bulk_data(csv_file, index_name):
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            formatted_date = format_date(row["Date of FTBFS"])
            # Create an action for each row
            yield {
                "_index": index_name,
                "_source": {
                    "project": row["Project"],
                    "component": row["Component"],
                    "status": row["Status"],
                    "release": row["Release"],
                    "review": row["Review"],
                    "logs": row["Logs"],
                    "@timestamp": formatted_date
                }
            }
# Index the data to OpenSearch using the bulk API
try:
    response = helpers.bulk(client, generate_bulk_data(csv_file, index_name))
    print(f"Successfully indexed: {response[0]} documents")
except Exception as e:
    print(f"Failed to index documents: {e}")
