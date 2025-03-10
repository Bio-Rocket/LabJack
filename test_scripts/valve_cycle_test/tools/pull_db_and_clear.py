import datetime
from pathlib import Path
import sys
import os

from dotenv import load_dotenv
from pocketbase import Client
from pocketbase.errors import ClientResponseError

# PB_URL = 'http://127.0.0.1:8090'
PB_URL = 'http://192.168.0.69:8090' # Database Pi IP


def connect_to_db() -> Client:
    """
    Connect to the database using the admin credentials stored in the environment variables.
    """
    client = Client(PB_URL)

    # Load environment variables from .env file
    load_dotenv()
    # Get admin credentials from environment variables
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASS")

    if not admin_email or not admin_password:
        print("DB - Admin credentials not found in environment variables.")
        return None

    auth_data = client.collection("_superusers").auth_with_password(admin_email, admin_password)

    return client

def get_all_records(client, collection_name):
    """
    Retrieve all records from the specified collection in a paginated manner.
    """
    all_records = []
    page = 1
    per_page = 100  # Adjust as needed

    while True:
        try:
            records = client.collection(collection_name).get_list(page, per_page)
            all_records.extend(records.items)
            if len(records.items) < per_page:
                break
            page += 1
        except ClientResponseError as e:
            print(f"Error retrieving records: {e}")
            break

    return all_records

def main(file_path):
    """
    Main function that processes the given file path.

    Args:
        file_path (str): The path to the file to be processed.
    """

    csv_data_file = os.path.join(Path(__file__).parent, "data_files", file_path)
    os.makedirs(os.path.dirname(csv_data_file), exist_ok=True)

    client = connect_to_db()
    if client is None:
        return

    try:
        all_records = get_all_records(client, 'Plc')
        print(f"{len(all_records)} records found in <Plc>")
    except Exception as e:
        print(f"Could not get records from the collection <Plc>: {e}")
        return

    with open(csv_data_file, 'w') as f:
        f.write("time,PT1,PT2,PT3,PBV1,PBV2\n")

        previous_time = datetime.datetime.now()
        for set_of_records in all_records:
            if previous_time != set_of_records.created:
                previous_time = set_of_records.created
                milliseconds_offset = 0

            for i in range(len(set_of_records.pt1)):
                milliseconds_offset += 1000 / len(set_of_records.pt1)

                pt1 = set_of_records.pt1[i]
                pt2 = set_of_records.pt2[i]
                pt3 = set_of_records.pt3[i]

                pbv1 = set_of_records.pbv1[i]
                pbv2 = set_of_records.pbv2[i]

                time_of_record = set_of_records.created + datetime.timedelta(milliseconds=milliseconds_offset)

                f.write(f"{time_of_record},{pt1},{pt2},{pt3},{pbv1},{pbv2}\n")

    print("Data stored in file:", csv_data_file)

    # Clear the database
    print("Clearing <Plc> collection")
    num_of_records = 0
    while True:
        try:
            record = client.collection('Plc').get_first_list_item("")
            client.collection('Plc').delete(record.id)
            num_of_records += 1
        except ClientResponseError:
            print(f"Deleted {num_of_records} entries")
            return


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pull_db_and_clear.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    main(file_path)