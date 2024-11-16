import datetime
import sys
from pocketbase import Client
import matplotlib.pyplot as plt
import csv

NUM_LJ_INPUTS = 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 plot_pt_data.py <filename>")
        sys.exit(1)
    filename = sys.argv[1]

    # client = Client('http://192.168.0.69:8090')
    client = Client('http://127.0.0.1:8090')

    try:
        all_records = client.collection('LabJack').get_full_list()
        print(f"{len(all_records)} records found")
    except Exception:
        print("NOT GOOD")
        raise

    with open(filename, 'w') as f:
        f.write("time, pt\n")

        previous_time = datetime.datetime.now()
        for set_of_records in all_records:

            if previous_time != set_of_records.created:
                previous_time = set_of_records.created
                milliseconds_offset = 0

            for pressure_data in set_of_records.lj_data:

                pressure_data

                milliseconds_offset += 1000/len(set_of_records.lj_data)
                time_of_record = set_of_records.created + datetime.timedelta(milliseconds=milliseconds_offset)

                pt = pressure_data
                f.write(f"{time_of_record}, {pt}\n")

    x = []
    y = []

    with open(filename,'r') as csv_file:
        plots = csv.reader(csv_file, delimiter = ',')

        header_row = True
        for row in plots:
            if header_row:
                header_row = False
                continue
            x.append(row[0])
            y.append(float(row[1]))

    plt.plot(x, y, label='pt')

    plt.xlabel('time')
    plt.ylabel('pressure')

    plt.title('Pressure Transducer Data')
    plt.legend()
    plt.show()


