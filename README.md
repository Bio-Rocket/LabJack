<!-- markdownlint-disable MD029 -->

# LabJack

## Setup

1. First create a .venv for to insure the correct modules are installed

- In the repo's root directory run ```python -m venv .venv``` to create the venv folder
- The activate the venv:
  - windows ```.venv\Scripts\activate```
  - mac/linux ```source .venv/bin/activate```
- Install the necessary modules ```pip install -r requirements.txt```

2. You will also need a .env file which will contain the database admin email and password

- Create a .env file in the root repo directory
- Populate the .env with vars ADMIN_EMAIL, ADMIN_PASS
  - eg: ADMIN_EMAIL="<ethan.subasic@gmail.com>"

3. Not to use the Labjack, the proper drivers will need to be installed as well

- Visit <https://support.labjack.com/docs/ljm-software-installer-downloads-t4-t7-t8-digit> ensure the driver is intended for your system architecture are for the lj7pro labjack.

4. This repo is also intended to be ran with the database repo so ensure the database is running see README.md from <https://github.com/Bio-Rocket/Database>

- ENSURE YOU HAVE THE 0.25.0 VERSION OF THE POCKETBASE EXECUTABLE DOWNLOADED

## Running main.py

- Run main.py from the root directory, after activating the venv run ```python src/main.py```
  - Running from this directory ensures all the imports and data files are correct
