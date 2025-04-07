# GOAL: this code creates an .sh file which allows you to run the Webex Space Archive script
#       for ALL of your spaces.
# version: 0.1
# Space archive script:     https://github.com/DJF3/Webex-Message-space-archiver/
# How to run it? 
#       0. install python requests ("pip3 install requests")
#       0. check python version "python3 -V" - should be 3.10 or above
#       0. download 'webex-space-archive.py' from the github url above.
#       0. get your Webex dev token: https://developer.webex.com/docs/getting-your-personal-access-token (login)
#       1. Edit this file:
#           a. put your ACCESS_TOKEN in this variable _OR_ 
#              (optional) set the token in an environment variable: (MacOS): set WEBEX_ARCHIVE_TOKEN='TOKENHERE'
#           b. edit variable archive_script if the archive .py file is different than webex-space-archive.py 
#       2. In a terminal window:         python3 generate_space_batch.py
#              this will generate a file called "webex-space-archive-ALL.sh" and display the content.
#       3. (optional) Edit the generated .sh script to remove spaces you don't want archived.
#       3. Execute the generated script: sh webex-space-archive-ALL.sh
# NOTE: that when the .sh file is executed it will use the standard .ini file for the configuration. (what to download, max files, etc)
# Tested on Macos 14.6.1 and Python 3.12. 
# 2025 -  DJ Uittenbogaard
# 
import requests
import os
import sys

# Replace with your Webex API access token
ACCESS_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
# archive_script = "webex-space-archive.py"
archive_script = "webex-space-archive-v31pub.py"
#_____ below: no changes needed


# Check if Webex token in environment variable 'WEBEX_ARCHIVE_TOKEN'
if "WEBEX_ARCHIVE_TOKEN" in os.environ:
    ACCESS_TOKEN = os.environ['WEBEX_ARCHIVE_TOKEN']

# Set the headers with your token
HEADERS = { "Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json" }
count_total = 0
count_direct = 0
count_group = 0
my_output = ""

try:
    # Make the GET request
    response = requests.get("https://webexapis.com/v1/rooms?max=1000", headers=HEADERS)
    response.raise_for_status()  # Raise exception for HTTP errors
    rooms = response.json().get("items", [])
    # Output each room's title and ID
    for room in rooms:
        my_output += f"\n# {count_total}. {room['title']}"
        my_output += f"\npython3 {archive_script} {room['id']}"
        count_total += 1
        if room['type'] == "direct":
            count_direct += 1
        else:
            count_group += 1
except requests.exceptions.RequestException as e:
    print(f"# Error fetching rooms: {e}")
    print(my_output)
    sys.exit(1)


my_output += f"\n\n"
my_output += f"\n#   TOTAL  space: {count_total}"
my_output += f"\n#   Direct space: {count_direct}"
my_output += f"\n#   Group  space: {count_group}"
if count_total > 990: 
    my_output += f"\n# ---> CAREFUL, you may have more than 1000 spaces. This code only generates archive commands for the first 1000 spaces!"
# Print output to screen
print(my_output)
# Write output to .sh file. Existing files will be overwritten
with open("webex-space-archive-ALL.sh", "w") as file:
    file.write(my_output)
