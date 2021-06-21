##!/usr/bin/env python3

# Program Name: zoom-recording-downloader.py
# Import TQDM progress bar library
from tqdm import tqdm
# Import app environment variables
from sys import exit
from signal import signal, SIGINT
from dateutil.parser import parse
import datetime
from datetime import date
from dateutil import relativedelta
from datetime import date, timedelta
import itertools
import requests
import time
import sys
import os
from dotenv import load_dotenv
load_dotenv()
api_token = os.environ.get('JWT_TOKEN')
APP_VERSION = "2.1"

# JWT_TOKEN now lives in .env
ACCESS_TOKEN = 'Bearer ' + api_token
AUTHORIZATION_HEADER = {'Authorization': ACCESS_TOKEN}

API_ENDPOINT_USER_LIST = 'https://api.zoom.us/v2/users'

# Start date now split into YEAR, MONTH, and DAY variables (Within 6 month range)
RECORDING_START_YEAR = 2021
RECORDING_START_MONTH = 1
RECORDING_START_DAY = 1
RECORDING_END_DATE = date.today()
DOWNLOAD_DIRECTORY = 'downloads'
COMPLETED_MEETING_IDS_LOG = 'completed-downloads.log'
COMPLETED_MEETING_IDS = set()


# define class for text colouring and highlighting
class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def API_ENDPOINT_RECORDING_LIST(email):
    API_ENDPOINT = 'https://api.zoom.us/v2/users/' + email + '/recordings'
    return API_ENDPOINT


def get_credentials(host_id, page_number, rec_start_date):
    return {
        'host_id': host_id,
        'page_number': page_number,
        'from': rec_start_date,
    }


def get_user_ids():
    # get total page count, convert to integer, increment by 1
    response = requests.get(url=API_ENDPOINT_USER_LIST,
                            headers=AUTHORIZATION_HEADER)
    page_data = response.json()
    total_pages = int(page_data['page_count']) + 1

    # results will be appended to this list
    all_entries = []

    # loop through all pages and return user data
    for page in range(1, total_pages):
        url = API_ENDPOINT_USER_LIST + "?page_number=" + str(page)
        user_data = requests.get(url=url, headers=AUTHORIZATION_HEADER).json()
        user_ids = [(user['email'], user['id'], user['first_name'],
                     user['last_name']) for user in user_data['users']]
        all_entries.extend(user_ids)
        data = all_entries
        page += 1
    return data


def format_filename(recording, file_type, recording_type):
    uuid = recording['uuid']
    topic = recording['topic'].replace('/', '&')
    rec_type = recording_type.replace("_", " ").title()
    meeting_time = parse(recording['start_time'])
    return '{} - {} UTC - {}.{}'.format(
        meeting_time.strftime('%Y.%m.%d'), meeting_time.strftime('%I.%M %p'), topic+" - "+rec_type, file_type.lower())

def get_recordings(email, page_size, rec_start_date, rec_end_date):
    return {
        'userId':       email,
        'page_size':    page_size,
        'from':         rec_start_date,
        'to':           rec_end_date
    }


# Generator used to create deltas for recording start and end dates
def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr, min(curr + delta, end)
        curr += delta


def list_recordings(email):
    recordings = []

    for start, end in perdelta(date(RECORDING_START_YEAR, RECORDING_START_MONTH, RECORDING_START_DAY), date.today(), timedelta(days=30)):
        post_data = get_recordings(email, 300, start, end)
        response = requests.get(url=API_ENDPOINT_RECORDING_LIST(
            email), headers=AUTHORIZATION_HEADER, params=post_data)
        recordings_data = response.json()
        recordings.extend(recordings_data['meetings'])
    return recordings

def load_completed_meeting_ids():
    try:
        with open(COMPLETED_MEETING_IDS_LOG, 'r') as fd:
            for line in fd:
                COMPLETED_MEETING_IDS.add(line.strip())
    except FileNotFoundError:
        print("Log file not found. Creating new log file: ",
              COMPLETED_MEETING_IDS_LOG)
        print()


def handler(signal_received, frame):
    # handle cleanup here
    print(color.RED + "\nSIGINT or CTRL-C detected. Exiting gracefully." + color.END)
    exit(0)


# ################################################################
# #                        MAIN                                  #
# ################################################################

def main():

    # clear the screen buffer
    os.system('cls' if os.name == 'nt' else 'clear')

    load_completed_meeting_ids()

    print(color.BOLD + "Getting user accounts..." + color.END)
    users = get_user_ids()

    for email, user_id, first_name, last_name in users:
        print(color.BOLD + "\nGetting recording list for {} {} ({})".format(first_name,
                                                                            last_name, email) + color.END)
        # wait n.n seconds so we don't breach the API rate limit
        # time.sleep(0.1)
        recordings = list_recordings(user_id)
        total_count = len(recordings)
        print("==> Found {} recordings".format(total_count))

        for index, recording in enumerate(recordings):
            success = False
            meeting_id = recording['uuid']
            if meeting_id in COMPLETED_MEETING_IDS:
                print("==> Skipping already downloaded meeting: {}".format(meeting_id))
                continue

            if success:
                # if successful, write the ID of this recording to the completed file
                with open(COMPLETED_MEETING_IDS_LOG, 'a') as log:
                    COMPLETED_MEETING_IDS.add(meeting_id)
                    log.write(meeting_id)
                    log.write('\n')
                    log.flush()

    print(color.BOLD + color.GREEN + "\n*** All done! ***" + color.END)
    save_location = os.path.abspath(DOWNLOAD_DIRECTORY)
    print(color.BLUE + "\nRecordings have been saved to: " +
          color.UNDERLINE + "{}".format(save_location) + color.END + "\n")


if __name__ == "__main__":
    # tell Python to run the handler() function when SIGINT is recieved
    signal(SIGINT, handler)

    main()

