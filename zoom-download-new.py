import jwt
import requests
import itertools
import json
from time import time
import sys
import os
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()
api_token = os.environ.get('JWT_TOKEN')
APP_VERSION = "2.1"
  
  
# JWT_TOKEN now lives in .env
ACCESS_TOKEN = 'Bearer ' + api_token
AUTHORIZATION_HEADER = {'Authorization': ACCESS_TOKEN}
DOWNLOAD_DIRECTORY = 'downloads'

  
  
def download_recording(download_url, meetingid, filename):
    print(download_url)
    dl_dir = os.sep.join([DOWNLOAD_DIRECTORY, meetingid])
    full_filename = os.sep.join([dl_dir, filename])
    os.makedirs(dl_dir, exist_ok=True)
    response = requests.get(download_url, stream=True)

    # total size in bytes.
    total_size = int(response.headers.get('content-length', 0))
    block_size = 32 * 1024  # 32 Kibibytes

    # create TQDM progress bar
    t = tqdm(total=total_size, unit='iB', unit_scale=True)
    try:
        with open(full_filename, 'wb') as fd:
            # with open(os.devnull, 'wb') as fd:  # write to dev/null when testing
            for chunk in response.iter_content(block_size):
                t.update(len(chunk))
                fd.write(chunk)  # write video chunk to disk
        t.close()
        return True
    except Exception as e:
        # if there was some exception, print the error and return False
        print(e)
        return False
  
# send a request with headers including 
# a token and meeting details
def getrecordingurl(meetingid):
    headers = {'authorization': 'Bearer ' + api_token,
               'content-type': 'application/json'}
    r = requests.get(
        "https://api.zoom.us/v2/meetings/{}/recordings".format(meetingid), 
      headers=headers)
    
    print("\n downloading zoom recording ... \n")
    # print(r.text)
    # converting the output into json and extracting the details
    y = r.json()
    for recordings in y['recording_files']:
        if recordings['recording_type'] == "shared_screen_with_speaker_view":
            return recordings["download_url"]
    return None 
    # download_URL = y["download_url"]
  
    # print(
    #     f'\n here is your zoom meeting link {join_URL}
  
  
# run the create meeting function
# print(getrecordingurl('3569323013'))

if __name__ == "__main__":
    download_recording(getrecordingurl('3569323013'),'3569323013','testfile.mp4')
    

  
