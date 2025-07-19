import os
from dotenv import load_dotenv
from pocketbase import Client
from pocketbase.errors import ClientResponseError


PB_URL = 'http://192.168.8.68:8090' # Database Pi IP

client = Client(PB_URL, timeout=5)
token = None


# Load environment variables from .env file
load_dotenv()

# Get admin credentials from environment variables
admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASS")

if not admin_email or not admin_password:
    print("DB - Admin credentials not found in environment variables.")
    exit(1)

auth_data = client.collection("_superusers").auth_with_password(admin_email, admin_password)
token = auth_data.token
if token is None:
    print("DB - Failed to authenticate as admin.")
    exit(1)

print("Clearing <Plc> collection")
num_of_records = 0
while True:
    try:
        record = client.collection('Plc').get_first_list_item("")
        client.collection('Plc').delete(record.id)
        num_of_records += 1
    except ClientResponseError:
        print(f"Deleted {num_of_records} entries")
        break

print("Clearing <LabJack> collection")
num_of_records = 0
while True:
    try:
        record = client.collection('LabJack').get_first_list_item("")
        client.collection('LabJack').delete(record.id)
        num_of_records += 1
    except ClientResponseError:
        print(f"Deleted {num_of_records} entries")
        breakgi