from pathlib import Path
import time
from pocketbase import Client
from pocketbase.errors import ClientResponseError
import datetime

from dotenv import load_dotenv
import os

PB_URL = 'http://192.168.8.68:8090' # Database Pi IP

PLC_FILE_NAME = "plc_data.csv"
PLC_FILE_PATH = os.path.join(Path(__file__).parent, "data_files", PLC_FILE_NAME)

LJ_FILE_NAME = "lj_data.csv"
LJ_FILE_PATH = os.path.join(Path(__file__).parent, "data_files", LJ_FILE_NAME)

SET_ALLOWED_READ_LIMIT = True  # Limit for the number of records to read from the database
ALLOWED_READ_LIMIT = 50000

def verify_connection(client) -> bool:
    """
    Verify the connection to the database.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        client.health.check()
        return True
    except ClientResponseError as e:
        return False

def get_all_records(client, collection_name):
    """
    Retrieve all records from the specified collection in a paginated manner.
    """
    all_records = []
    page = 1
    per_page = 100  # Adjust as needed
    num_read = 0

    while True:
        try:
            records = client.collection(collection_name).get_list(page, per_page)
            all_records.extend(records.items)
            num_read += len(records.items)
            if len(records.items) < per_page:
                break
            if SET_ALLOWED_READ_LIMIT and num_read > ALLOWED_READ_LIMIT:
                print(f"DB - Read limit reached: {num_read} records.")
                break
            page += 1
        except ClientResponseError as e:
            print(f"Error retrieving records: {e}")
            break

    return all_records


# MAIN ++++++++++++++++++++++++++++++++++++++++++++++++++++++

# Connect
client = Client(PB_URL, timeout=5)
token = None

# Wait for the database to be available
while not verify_connection(client):
    print(f"DB - Failed to connect to the database @{PB_URL}, retrying in 5s...")
    time.sleep(5)

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

print("DB - READING PLC DATA")

plc_all_records = get_all_records(client, 'Plc')
print(f"{len(plc_all_records)} records found in <Plc>")

print("DB - READING LJ DATA")

lj_all_records = get_all_records(client, 'LabJack')
print(f"{len(lj_all_records)} records found in <Plc>")

print(f"DB - WRITE PLC DATA TO {PLC_FILE_PATH}")

os.makedirs(os.path.dirname(PLC_FILE_PATH), exist_ok=True)

with open(PLC_FILE_PATH, 'w') as f:
    f.write("time,TC1,TC2,TC3,TC4,TC5,TC6,TC7,TC8,TC9,LC1,LC2,LC7,PT1,PT2,PT3,PT4,PT5,PBV1,PBV2,PBV3,PBV4,PBV5,PBV6,PBV7,PBV8,PBV9,PBV10,PBV11,SOL1,SOL2,SOL3,SOL4,SOL5,IGN1,IGN2,CFV1,CFV2,CFV3,CFV4,CFV5\n")

    previous_time = None
    current_time = 0
    all_current_time_entries = []
    current_entries = []
    total_time_count = -1
    for set_of_records in plc_all_records:

        current_time = set_of_records.created

        if previous_time is None:
            previous_time = current_time

        for i in range(len(set_of_records.pt1)):
            tc1 = set_of_records.tc1[i]
            tc2 = set_of_records.tc2[i]
            tc3 = set_of_records.tc3[i]
            tc4 = set_of_records.tc4[i]
            tc5 = set_of_records.tc5[i]
            tc6 = set_of_records.tc6[i]
            tc7 = set_of_records.tc7[i]
            tc8 = set_of_records.tc8[i]
            tc9 = set_of_records.tc9[i]
            lc1 = set_of_records.lc1[i]
            lc2 = set_of_records.lc2[i]
            lc7 = set_of_records.lc7[i]
            pt1 = set_of_records.pt1[i]
            pt2 = set_of_records.pt2[i]
            pt3 = set_of_records.pt3[i]
            pt4 = set_of_records.pt4[i]
            pt5 = set_of_records.pt5[i]

            pbv1 = set_of_records.pbv1[i]
            pbv2 = set_of_records.pbv2[i]
            pbv3 = set_of_records.pbv3[i]
            pbv4 = set_of_records.pbv4[i]
            pbv5 = set_of_records.pbv5[i]
            pbv6 = set_of_records.pbv6[i]
            pbv7 = set_of_records.pbv7[i]
            pbv8 = set_of_records.pbv8[i]
            pbv9 = set_of_records.pbv9[i]
            pbv10 = set_of_records.pbv10[i]
            pbv11 = set_of_records.pbv11[i]
            sol1 = set_of_records.sol1[i]
            sol2 = set_of_records.sol2[i]
            sol3 = set_of_records.sol3[i]
            sol4 = set_of_records.sol4[i]
            sol5 = set_of_records.sol5[i]

            ign1 = set_of_records.ign1[i]
            ign2 = set_of_records.ign2[i]

            cfv1 = set_of_records.cold_flow_valve_1[i]
            cfv2 = set_of_records.cold_flow_valve_2[i]
            cfv3 = set_of_records.cold_flow_valve_3[i]
            cfv4 = set_of_records.cold_flow_valve_4[i]
            cfv5 = set_of_records.cold_flow_valve_5[i]

            current_entries.append(
                f"{tc1},{tc2},{tc3},{tc4},{tc5},{tc6},{tc7},{tc8},{tc9},"
                f"{lc1},{lc2},{lc7},{pt1},{pt2},{pt3},{pt4},{pt5},"
                f"{pbv1},{pbv2},{pbv3},{pbv4},{pbv5},{pbv6},{pbv7},"
                f"{pbv8},{pbv9},{pbv10},{pbv11},"
                f"{sol1},{sol2},{sol3},{sol4},{sol5},"
                f"{ign1},{ign2},{cfv1},{cfv2},{cfv3},{cfv4},{cfv5}\n"
            )

        if current_time != previous_time:

            num_entries = len(all_current_time_entries)
            time_step = 1000 / num_entries
            entry_time = previous_time

            for entry in all_current_time_entries:
                f.write(f"{entry_time}," + entry)
                entry_time += datetime.timedelta(milliseconds=time_step)

            all_current_time_entries.clear()

        all_current_time_entries.extend(current_entries)
        current_entries.clear()
        previous_time = current_time

print("DB - Data stored in file:", PLC_FILE_PATH)


# print(f"DB - WRITE LJ DATA TO {LJ_FILE_PATH}")

# os.makedirs(os.path.dirname(LJ_FILE_PATH), exist_ok=True)

# with open(LJ_FILE_PATH, 'w') as f:
#     f.write("time,LC3,LC4,LC5,LC6,PT6,PT7,PT8,PT9,PT10,PT11,PT12,PT13,PT14\n")

#     previous_time = datetime.datetime.now()
#     for set_of_records in lj_all_records:
#         if previous_time != set_of_records.created:
#             previous_time = set_of_records.created
#             milliseconds_offset = 0

#         for i in range(len(set_of_records.lc3)):
#             milliseconds_offset += 1000 / len(set_of_records.lc3)

#             lc3 = set_of_records.lc3[i]
#             lc4 = set_of_records.lc4[i]
#             lc5 = set_of_records.lc5[i]
#             lc6 = set_of_records.lc6[i]
#             pt6 = set_of_records.pt6[i]
#             pt7 = set_of_records.pt7[i]
#             pt8 = set_of_records.pt8[i]
#             pt9 = set_of_records.pt9[i]
#             pt10 = set_of_records.pt10[i]
#             pt11 = set_of_records.pt11[i]
#             pt12 = set_of_records.pt12[i]
#             pt13 = set_of_records.pt13[i]
#             pt14 = set_of_records.pt14[i]

#             time_of_record = set_of_records.created + datetime.timedelta(milliseconds=milliseconds_offset)

#             f.write(f"{time_of_record},{lc3},{lc4},{lc5},{lc6},"
#                     f"{pt6},{pt7},{pt8},{pt9},{pt10},{pt11},{pt12},{pt13},{pt14}\n")

# print("DB - Data stored in file:", LJ_FILE_PATH)

