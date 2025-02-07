import datetime
from pathlib import Path
import sys
import os

from dotenv import load_dotenv
from pocketbase import Client
from pocketbase.errors import ClientResponseError

PB_URL = 'http://127.0.0.1:8090'
# PB_URL = 'http://192.168.0.69:8090' # Database Pi IP


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
        return

    auth_data = client.collection("_superusers").auth_with_password(admin_email, admin_password)

    return client

def main(file_path):
    """
    Main function that processes the given file path.

    Args:
        file_path (str): The path to the file to be processed.
    """

    csv_data_file = os.path.join(Path(__file__).parent, "data_files" ,file_path)
    os.makedirs(os.path.dirname(csv_data_file), exist_ok=True)

    client = connect_to_db()

    try:
        all_records = client.collection('LabJack').get_full_list()
        print(f"{len(all_records)} records found in  <LabJack>")
    except Exception:
        print("Could not get records from the collection <LabJack>")
        raise


    with open(csv_data_file, 'w') as f:
        f.write("time, PT1, raw_voltage, corrected_voltage\n")

        previous_time = datetime.datetime.now()
        for set_of_records in all_records:

            if previous_time != set_of_records.created:
                previous_time = set_of_records.created
                milliseconds_offset = 0

            for i in range(len(set_of_records.raw_voltage)):

                milliseconds_offset += 1000/len(set_of_records.pt1)

                pt = set_of_records.pt1[i]
                rv = set_of_records.raw_voltage[i]
                cv = set_of_records.corrected_voltage[i]

                time_of_record = set_of_records.created + datetime.timedelta(milliseconds=milliseconds_offset)

                f.write(f"{time_of_record}, {pt}, {rv}, {cv}\n")

    print("Data stored in file:", csv_data_file)

    # Clear the database
    print("Clearing <LabJack> collection")
    num_of_records = 0
    while(True):
        try:
            record = client.collection('LabJack').get_first_list_item("")
            client.collection('LabJack').delete(record.id)
            num_of_records+=1
        except ClientResponseError:
            print(f"Deleted {num_of_records} entries")
            return


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pull_db_and_clear.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    main(file_path)