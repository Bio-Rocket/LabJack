# LabJack

## Setup

1. First create a .venv for to insure the correct modules are installed

- In the repo's root directory run ```python -m venv .venv``` to create the venv folder
- The activate the venv:
  - windows ```.venv\Scripts\activate```
  - mac/linux ```source .venv/bin/activate```
- Install the necessary modules ```pip install -r requirements.txt```

2. Not to use the Labjack, the proper drivers will need to be installed as well

- Visit <https://support.labjack.com/docs/ljm-software-installer-downloads-t4-t7-t8-digit> ensure the driver is intended for your system architecture are for the lj7pro labjack.

3. This repo is also intended to be ran with the database repo so ensure the database is running see README.md from <https://github.com/Bio-Rocket/Database>
