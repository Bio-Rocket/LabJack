import json
import os
import time
from typing import Union
from pocketbase import Client
from dotenv import load_dotenv
import requests
import random

PB_URL = 'http://127.0.0.1:8090'
EXPECTED_SCHEMA_JSON = "DatabaseSchema.json"

def admin_login(client: Client, email: str, password: str) -> Union[str, None]:
    """
    Authenticate as an admin to the database.

    Args:
        email (str): The email of the admin.
        password (str): The password of the admin.

    Returns:
        str: The token if the login is successful, None otherwise.
    """
    # Clear Previous Auth
    client.auth_store.clear()

    # Create a new admin token using an http request
    admin_auth_url = PB_URL + "/api/admins/auth-with-password"
    payload = {
        "identity": email,
        "password": password
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(admin_auth_url, json=payload, headers=headers)

    # Check if the login was successful
    if response.status_code == 200:
        data = response.json()
        token = data['token']
        client.auth_store.save(token)
        return token
    else:
        print(f"DB - Auth failed err{response.status_code}: {response.text}")
        return None

def create_collection(client, collection_name, schema):
    new_schema = []
    for field in schema:
        new_schema.append({"name": field, "type": schema[field], "required": False, "options":  {"maxSize": 100000}})

    collection_data = {
        "name": collection_name,
        "schema": new_schema,
        "listRule": "", # Optional access rules
        "viewRule": "",
        "createRule": "",
        "updateRule": "",
        "deleteRule": "",
        "options": {} # Optional collection-specific options
    }

    client.collections.create(collection_data)

def delete_collection(client, collection_name):
    for record in client.collection(collection_name).get_full_list():
        client.collection(collection_name).delete(record.id)

    # Update the collection with the new schema.
    collection_to_update = client.collections.get_one(collection_name)

    # Delete the existing collection
    client.collections.delete(collection_to_update.id)

def updated_collections(client, token) -> bool:
    if not token:
        print("DB - No auth token to update collections")
        return False

    # Get the current collections and their schemas from pocket base
    # Pass the token in the Authorization header
    headers = {"Authorization": f"Bearer {token}"}
    # Assuming client is set to a proper instance, request collections
    collections_url = PB_URL + "/api/collections"
    response = requests.get(collections_url, headers=headers)

    if response.status_code != 200:
        print(f"DB - Could not retrieve collection list, err{response.status_code}: {response.text}")
        return False

    current_schema = {}
    expected_schema = {}

    # Format the current schema for comparison to the expected schema
    collections_data = response.json()
    for collection in collections_data["items"]:
        if collection["system"]: # Skip system collections
            continue

        current_collection_schema = {}

        for field in collection["schema"]:
            current_collection_schema[field["name"]] = field["type"]

        current_schema[collection["name"]] = current_collection_schema

    # Load the expected database schema from the json file
    # and format to match current schema format for comparison.
    try:
        with open(EXPECTED_SCHEMA_JSON, "r") as file:
            expected_data = json.load(file)

            for collection in expected_data["collections"]:
                collection_name = collection["name"]
                collection_schema = collection["schema"]

                expected_collection_schema = {}
                for field in collection_schema:
                    expected_collection_schema[field["name"]] = field["type"]

                expected_schema[collection_name] = expected_collection_schema
    except Exception as e:
        print(f"DB - Could not load expected schema: {e}")
        return False

    # Update and create collections as needed
    for expected_collection in expected_schema:
        # If no collection matches expected collection, create it
        if expected_collection not in current_schema:
            print(f"DB - Creating collection {expected_collection}")
            create_collection(client, expected_collection, expected_schema[expected_collection])
            continue

        if expected_schema[expected_collection] != current_schema[expected_collection]:
            print(f"DB - Clearing and updating collection {expected_collection}")
            # Drop the collection and recreate it with the new schema.
            delete_collection(client, expected_collection)
            # Create the new schema by combining the default schema with the expected schema.
            create_collection(client, expected_collection, expected_schema[expected_collection])
            continue

    # Remove any collections that are not in the expected schema
    for current_collection in current_schema:
        if current_collection not in expected_schema:
            print(f"DB - Removing deprecated collection {current_collection}")
            delete_collection(client, current_collection)

def create_plc_record(client):
    entry = {}

    entry["TC1"] = round(random.uniform(0, 100), 2)
    entry["TC2"] = round(random.uniform(0, 100), 2)
    entry["TC3"] = round(random.uniform(0, 100), 2)
    entry["TC4"] = round(random.uniform(0, 100), 2)
    entry["TC5"] = round(random.uniform(0, 100), 2)
    entry["TC6"] = round(random.uniform(0, 100), 2)
    entry["TC7"] = round(random.uniform(0, 100), 2)
    entry["TC8"] = round(random.uniform(0, 100), 2)
    entry["TC9"] = round(random.uniform(0, 100), 2)

    entry["LC1"] = round(random.uniform(0, 10), 2)
    entry["LC2"] = round(random.uniform(0, 10), 2)
    entry["LC7"] = round(random.uniform(0, 10), 2)

    entry["PT1"] = round(random.uniform(0, 50), 2)
    entry["PT2"] = round(random.uniform(0, 50), 2)
    entry["PT3"] = round(random.uniform(0, 50), 2)
    entry["PT4"] = round(random.uniform(0, 50), 2)
    entry["PT5"] = round(random.uniform(0, 50), 2)
    entry["PT13"] = round(random.uniform(0, 50), 2)
    entry["PT14"] = round(random.uniform(0, 50), 2)

    entry["PBV1"] = random.choice([True, False])
    entry["PBV2"] = random.choice([True, False])
    entry["PBV3"] = random.choice([True, False])
    entry["PBV4"] = random.choice([True, False])
    entry["PBV5"] = random.choice([True, False])
    entry["PBV6"] = random.choice([True, False])
    entry["PBV7"] = random.choice([True, False])
    entry["PBV8"] = random.choice([True, False])
    entry["PBV9"] = random.choice([True, False])
    entry["PBV10"] = random.choice([True, False])
    entry["PBV11"] = random.choice([True, False])

    entry["SOL1"] = random.choice([True, False])
    entry["SOL2"] = random.choice([True, False])
    entry["SOL3"] = random.choice([True, False])
    entry["SOL4"] = random.choice([True, False])
    entry["SOL5"] = random.choice([True, False])
    entry["SOL6"] = random.choice([True, False])
    entry["SOL7"] = random.choice([True, False])
    entry["SOL8"] = random.choice([True, False])
    entry["SOL9"] = random.choice([True, False])

    entry["HEATER"] = random.choice([True, False])

    entry["PMP3"] = random.choice([True, False])

    entry["IGN1"] = random.choice([True, False])
    entry["IGN2"] = random.choice([True, False])

    client.collection("Plc").create(entry)


def create_lj_record(client):

    entry = {}
    entry["LC3"] = [round(random.uniform(0, 10), 2)] * 4
    entry["LC4"] = [round(random.uniform(0, 10), 2)] * 4
    entry["LC5"] = [round(random.uniform(0, 10), 2)] * 4
    entry["LC6"] = [round(random.uniform(0, 10), 2)] * 4

    entry["PT6"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT7"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT8"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT9"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT10"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT11"] = [round(random.uniform(0, 50), 2)] * 4
    entry["PT12"] = [round(random.uniform(0, 50), 2)] * 4

    client.collection("LabJack").create(entry)

    client.collection("LabJack").create(entry)


if __name__ == "__main__":

    load_dotenv()

    # Get admin credentials from environment variables
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASS")

    client = Client(PB_URL)
    token = admin_login(client, admin_email, admin_password)
    if token is None:
        print("DB - Failed to authenticate as admin.")
        exit()

    updated_collections(client, token)

    while True:
        create_plc_record(client)
        create_lj_record(client)
        time.sleep(5)
        pass

