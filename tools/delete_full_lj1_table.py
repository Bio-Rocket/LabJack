


import datetime
import sys
from pocketbase import Client
import matplotlib.pyplot as plt
import csv

if __name__ == "__main__":

    # client = Client('http://192.168.0.69:8090')
    client = Client('http://127.0.0.1:8090')


    print("Deleting rn")
    num_of_records = 0
    while(True):
        try:
            record = client.collection('LabJack').get_first_list_item("")
            client.collection('LabJack').delete(record.id)
            num_of_records+=1
        except Exception:
            print("NOT GOOD")
            print(f"Deleted {num_of_records} entries before failure")
            raise
