import psycopg2  
import sys

from googleapiclient.errors import HttpError  
from googleapiclient import sample_tools  
from oauth2client.service_account import ServiceAccountCredentials  
from httplib2 import Http  
from apiclient.discovery import build

# Main

def main():  
    # Authenticate and create the service for the Core Reporting API
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
    'Compose-GA-xxxxxx.json', ['https://www.googleapis.com/auth/analytics.readonly'])
    http_auth = credentials.authorize(Http())
    service = build('analytics', 'v3', http=http_auth)

    # Define the connection string and connect
    conn_string = "host='aws-us-east-1-portal.8.dblayer.com' port=10221 dbname='ga_data' user='admin' password='password'"
    conn = psycopg2.connect(conn_string)

    # Open a cursor
    cursor = conn.cursor()

    # Run the query function using the API service
    traffic_results = get_api_traffic_query(service).execute()

    # Insert each row of the result set
    if traffic_results.get('rows', []):
        for row in traffic_results.get('rows'):
            #print(row)
            cursor.execute("""INSERT INTO traffic (yearMonth, users, sessions)
                            VALUES(%s, %s, %s)""", [row[0], row[1], row[2]])
    else:
        print('No Rows Found')

    # Commit changes
    conn.commit()

    # Select and retrieve results
    #cursor.execute("SELECT * FROM traffic")
    #records = cursor.fetchall()
    #print(records)

    # Close the cursor and the connection
    cursor.close()
    conn.close()

# Query function
def get_api_traffic_query(service):  
    return service.data().ga().get(
        ids='ga:xxxxxx',
        start_date='2014-01-01',
        end_date='2014-01-31',
        metrics='ga:users,ga:sessions',
        dimensions='ga:yearMonth',
        # sort='-ga:yearMonth',
        # filters='ga:pagePath=~signup',
        segment='sessions::condition::ga:hostname!~mongo|app|help|docs|staging|googleweblight',
        start_index='1',
        max_results='25')

if __name__ == '__main__':  
    main()