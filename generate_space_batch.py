"""
Webex Message Space Archive Script.

This helper script generates an .sh file which allows you to run the Archive
script for ALL of your spaces. When the .sh file is executed, the configuration
(what to download, max files, etc) will be retrieved from the standard .ini file.

Project home: https://github.com/DJF3/Webex-Message-space-archiver

Copyright (c) 2025 Dirk-Jan Uittenbogaard

Released under the MIT License.

Usage:
  0. install python requests ("pip3 install requests")
  0. check python version "python3 -V" - should be 3.10 or above
  0. download 'webex-space-archive.py' from the github url above.
  0. get your Webex dev token: https://developer.webex.com/docs/getting-your-personal-access-token (login)
  1. Edit this file:
     a. put your ACCESS_TOKEN in this variable
        _OR_
        set the token in the WEBEX_ARCHIVE_TOKEN environment variable:
            export WEBEX_ARCHIVE_TOKEN='TOKENHERE' (MacOS / Linux)
            set WEBEX_ARCHIVE_TOKEN='TOKENHERE' (Windows)
     b. edit variable archive_script if the archive .py file is different than webex-space-archive.py
 2. In a terminal window, run:
          python3 generate_space_batch.py
    this will generate a file called "webex-space-archive-ALL.sh" and display the content.
 3. Edit the generated .sh script to remove spaces you don't want archived.
 4. Execute the generated script: sh webex-space-archive-ALL.sh
"""

from datetime import datetime

import requests
import os
import sys

# Replace with your Webex API access token
ACCESS_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
archive_script = "webex-space-archive.py"
extract_script = "webex-space-archive-ALL.sh"
#_____ below: no changes needed


# Check if Webex token in environment variable 'WEBEX_ARCHIVE_TOKEN'
if "WEBEX_ARCHIVE_TOKEN" in os.environ:
    ACCESS_TOKEN = os.environ['WEBEX_ARCHIVE_TOKEN']

# Set the headers with your token
HEADERS = { "Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json" }
PAGE_SIZE = 1000
count_total = 0
count_direct = 0
count_group = 0
my_output = ""

try:
    # Get user information
    response = requests.get("https://webexapis.com/v1/people/me", headers=HEADERS)
    response.raise_for_status()
    user = response.json()

    # API endpoint to get first page of rooms
    url = f"https://webexapis.com/v1/rooms?max={PAGE_SIZE}"
    rooms = []

    print("Retrieving rooms")
    while url:
        # Progress
        print('.', end='')

        # Get the page, raise exception for HTTP errors
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        # Add retrieved rooms to the results list
        rooms.extend(response.json().get('items', []))

        # Get next page
        url = response.links['next']['url'] if 'next' in response.links else None

except requests.exceptions.RequestException as e:
    print(f"# Error fetching rooms: {e}")
    print(my_output)
    sys.exit(1)

# Sort retrieved rooms list alphabetically
rooms.sort(key=lambda room: room.get("title", "").lower())

# Output each room's title and ID
for room in rooms:
    count_total += 1
    my_output += f"\n# {count_total}. {room['title']}"
    my_output += f"\npython3 {archive_script} {room['id']}"
    if room['type'] == "direct":
        count_direct += 1
    else:
        count_group += 1

header = """# Webex Space Archive script
# ==========================
# Generated on {} for {} ({})
#
""".format(
    datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
    user.get('displayName'),
    user.get('userName')
)
header += f"""# Spaces counts:
#   TOTAL   {count_total}
#   Direct  {count_direct}
#   Group   {count_group}
"""

# Print output to screen
print("\n")
print(header)

header += "# " + "-" * 50 + "\n"

# Write output to .sh file. Existing files will be overwritten
with open(extract_script, "w", encoding="utf-8") as file:
    file.write(header + my_output + "\n")

print(f"Script saved in '{extract_script}'")
