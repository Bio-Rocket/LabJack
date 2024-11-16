import csv
from datetime import datetime
import sys

from matplotlib import pyplot as plt
import numpy as np

if len(sys.argv) != 2:
    print("Usage: python3 plot_pt_data.py <filename>")
    sys.exit(1)

filename = sys.argv[1]
file_only = filename.split('/')[-1]

time = []
pt1 = []
pt2 = []
valve_state = []

with open(filename,'r') as csv_file:
        plots = csv.reader(csv_file, delimiter = ',')

        header_row = True
        for row in plots:
            if header_row:
                header_row = False
                continue

            time.append(row[0])
            pt1.append(float(row[1]))
            pt2.append(float(row[2]))
            valve_state.append(int(row[3]))

pt1_arr = np.array(pt1)
pt2_arr = np.array(pt2)

initial_state = valve_state[0]
valve_open_index = valve_state.index(0 if initial_state else 1)




def reject_outliers(data, m=2):
    return data[abs(data - np.mean(data)) < m * np.std(data)]

corrected_pt2_before_open = reject_outliers(pt2_arr[:valve_open_index])
downstream_pressure_min_before_open = min(corrected_pt2_before_open)
downstream_pressure_max_before_open = max(corrected_pt2_before_open)



# print(f"Downstream pressure range before valve open: {downstream_pressure_min_before_open}, {downstream_pressure_max_before_open}")
# print(f"Downstream pressure average before valve open: {np.mean(corrected_pt2_before_open)} ")


valve_close_index = valve_state.index(1 if initial_state else 0, valve_open_index)



total_points_where_valve_is_open = valve_state.count(0 if initial_state else 1)

# Get the max and min pressures while the valve is open (for the last 50% of the open data)

corrected_pt2_while_open = reject_outliers(pt2_arr[int(valve_close_index-total_points_where_valve_is_open/2):valve_close_index])

downstream_pressure_min_while_open = min(corrected_pt2_while_open)
downstream_pressure_max_while_open = max(corrected_pt2_while_open)

arr = pt2_arr
window_size = 4

i = 0
# Initialize an empty list to store moving averages
moving_averages = []

# Loop through the array t o
#consider every window of size 3
while i < len(arr) - window_size + 1:

    # Calculate the average of current window
    window_average = round(np.sum(arr[i:i+window_size]) / window_size, 2)

    # Store the average of current
    # window in moving average list
    moving_averages.append(window_average)

    # Shift window to right by one position
    i += 1

# Get the first point where the downstream pressure goes above the max_before_open
begin_rising_index = next((i for i, x in enumerate(moving_averages) if x > downstream_pressure_max_before_open), None)

# Get the first point where the downstream pressure goes below the min_while_open after the the valve is closed
begin_falling_index = next((i for i in range(valve_close_index, len(moving_averages)) if moving_averages[i] < downstream_pressure_min_while_open), None)


print(f"For the {file_only} test:")
print(f"1) Valve open time: {time[valve_open_index]}")
print(f"2) Pressure begins rising time: {time[begin_rising_index]}")
print(f"3) Opening Delay: {datetime.strptime(time[begin_rising_index], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(time[valve_open_index], '%Y-%m-%d %H:%M:%S.%f')}")
print(f"4) Valve close time: {time[valve_close_index]}")
print(f"5) Pressure begins falling time: {time[begin_falling_index]}")
print(f"6) Closing Delay: {datetime.strptime(time[begin_falling_index], '%Y-%m-%d %H:%M:%S.%f') - datetime.strptime(time[valve_close_index], '%Y-%m-%d %H:%M:%S.%f')}")

x = []
for i in range(len(moving_averages)):
    x.append(i)

# print(f"number of data points: {len(x)}")

plt.axhline(y=downstream_pressure_max_before_open, color='r', linestyle='-')
plt.axhline(y=downstream_pressure_min_while_open, color='r', linestyle='-')
plt.axhline(y=downstream_pressure_max_while_open, color='r', linestyle='-')

plt.axvline(x=valve_open_index, color='r')
plt.axvline(x=begin_rising_index, color='g')
plt.axvline(x=valve_close_index, color='b')
plt.axvline(x=begin_falling_index, color='g')


# plt.plot(x, valve_state, label='v_state')
plt.plot(x, moving_averages, label='pt2')

plt.xlabel('time')
plt.ylabel('pressure')

plt.title('Pressure Transducer Data')
plt.legend()
plt.show()
