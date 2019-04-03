# -*- coding: utf-8 -*-
"""Webex Teams Space Archive Script.
Creates a single HTML file with the messages of a Webex Teams space
Info/Requirements/release-notes: https://github.com/DJF3/Webex-Teams-Space-Archive-v2/
And here: https://tools.sparkintegration.club/sparkarchive

Copyright (c) 2019 Cisco and/or its affiliates.

This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at

               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.

"""

import json
import requests
import codecs
import datetime
import urllib.request
import re
import time
import traceback
import sys
import os
import string
from pathlib import Path
import configparser


#--------- DO NOT CHANGE ANYTHING BELOW ---------
__author__ = "Dirk-Jan Uittenbogaard"
__email__ = "duittenb@cisco.com"
__version__ = "0.17g"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
sleepTime = 3
currentDate = datetime.datetime.now().strftime("%x %X")
configFile = "webexteamsarchive-config.ini"
myMemberList = dict()
myErrorList = list()


def beep(count): # PLAY SOUND (for errors)
    for x in range(0,count):
        print(chr(7))
    return

print("\n\n\n #0 ========================= START =========================")
# ----------- CHECK if config file exists and if the mandatory settings entries are present.
config = configparser.ConfigParser(allow_no_value=True)
if os.path.isfile("./" + configFile):
    try:
        config.read('./' + configFile)
        downloadFiles = config['Archive Settings']['downloadfiles'].lower().strip() # make sure that it's all lowercase
        sortOldNew = config['Archive Settings']['sortoldnew']
        myToken = config['Archive Settings']['mytoken']
        myRoom = config['Archive Settings']['myroom']
        outputFileName = config['Archive Settings']['outputfileName']
        maxTotalMessages = int(config['Archive Settings']['maxTotalMessages'])
        userAvatar = config['Archive Settings']['useravatar']
    except Exception as e:  # Error: keys missing from .ini file
        print(" **ERROR** reading webexteamsarchive-config.ini file settings.\n    ERROR: " + str(e))
        print("    Check if your .ini file contains the following keys: \n        downloadfiles, sortoldnew, mytoken, myroom, outputfilename")
        print("    Rename your .ini file, re-run this script (generating correct file)\n    and put your settings in the new .ini file")
        print(" ---------------------------------------\n\n")
        beep(3)
        exit()
else:  # CREATE config file (when it does not exist)
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.add_section('Archive Settings')
        config.set('Archive Settings', '; ---- Your Cisco Webex Teams developer token')
        config.set('Archive Settings', 'mytoken', '__YOUR_TOKEN_HERE__')
        config.set('Archive Settings', ';')
        config.set('Archive Settings', '; ---- Room ID: Can be found on the URL below, list all rooms, "max 900"')
        config.set('Archive Settings', ';               https://developer.webex.com/endpoint-rooms-get.html')
        config.set('Archive Settings', 'myroom', '__YOUR_SPACE_ID_HERE__')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; downloadFiles:  "no"      : (default) only show text "file attachment"')
        config.set('Archive Settings', ';                 "images"  : download images only')
        config.set('Archive Settings', ';                 "files"   : download files & images')
        config.set('Archive Settings', '; First try the script with downloadFiles set to "no".')
        config.set('Archive Settings', '; Downloading Large spaces with many files will take a LOT of time')
        config.set('Archive Settings', 'downloadfiles', 'no')
        config.set('Archive Settings', ';  ')
        config.set('Archive Settings', ';  ')
        config.set('Archive Settings', '; ---- download/show user avatar (new SDK version in 0.17b Feb 2019)')
        config.set('Archive Settings', ';           link (default) - link to avatar image')
        config.set('Archive Settings', ';           no')
        config.set('Archive Settings', 'useravatar', 'link')
        config.set('Archive Settings', ';   ')
        config.set('Archive Settings', ';   ')
        config.set('Archive Settings', '; ---- Max Messages: The Maximum number of messages you want to download.')
        config.set('Archive Settings', ';                    Important if you want to limit archiving HUGE spaces')
        config.set('Archive Settings', 'maxTotalMessages', '5000')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', '; ---- Output filename: Name of the generated HTML file. EMPTY: use spacename')
        config.set('Archive Settings', ';      (downloadFiles enabled? this also defines the attachment foldername)')
        config.set('Archive Settings', 'outputfilename', '')
        config.set('Archive Settings', ';     ')
        config.set('Archive Settings', ';     ')
        config.set('Archive Settings', '; ---- Sorting of messages. "yes" (default) means: last message at the bottom,')
        config.set('Archive Settings', ';      just like in the Webex Teams client. "no" = latest message at the top')
        config.set('Archive Settings', 'sortoldnew', 'yes')
        config.set('Archive Settings', ';      ')
        config.set('Archive Settings', ';      ')
        with open('./' + configFile, 'w') as configfile:
            config.write(configfile)
    except Exception as e:  # Error creating config file
        print(" ** ERROR ** creating config file")
        print("             Error message: " + str(e))
        beep(3)
    print("\n\n ------------------------------------------------------------------ \n ** WARNING ** Config file '" + configFile + "' does not exist.  \n               Creating empty configuration file. \n --> EDIT the configuration in this file and re-run this script.\n ------------------------------------------------------------------\n\n")
    # STOP - the script because you have to update the configuration file first
    exit()

# ----------- CHECK if the configuration VALUES are valid. If not, print error messsage and exit
goExitError = "\n\n ------------------------------------------------------------------"
if not downloadFiles in ['no', 'images', 'files']:
    goExitError += "\n   **ERROR** downloadFiles variable must be: 'no', 'images' or 'files'"
if not sortOldNew in ['yes', 'no']:
    sortOldNew = "yes"
if not myToken or len(myToken) < 55:
    goExitError += "\n   **ERROR** your token is not set or not long enough"
if not myRoom or len(myRoom) < 70:
    goExitError += "\n   **ERROR** your room ID is not set or not long enough"
if not outputFileName or len(outputFileName) < 3:
    outputFileName = "webexteams-space-archive"
if not userAvatar in ['no', 'link', 'download']:
    goExitError += "\n   **ERROR** useravatar variable must be: 'no', 'link' or 'download'"
print("    download files:" + downloadFiles + " - Max messages:" + str(maxTotalMessages) + " - Avatars: " + userAvatar)
if len(goExitError) > 76:   # length goExitError = 66. If error: it is > 76 characters --> print errors + exit
    print(goExitError + "\n ------------------------------------------------------------------\n\n")
    beep(3)
    exit()

# Set variables that are used in the rest of this script
myAttachmentFolder = outputFileName + "-attachments"

# ----------- HTML header code containing images, styling info (CSS)
htmlheader = """<!DOCTYPE html><html><head><meta charset="utf-8"/><style media='screen' type='text/css'>
body { font-family: 'HelveticaNeue-Light', 'Helvetica Neue Light', 'Helvetica Neue', 'Helvetica', 'Arial', 'Lucida Grande', 'sans-serif';
}
.cssRoomName {
    height: 66px;
    background-color: #029EDB;
    font-size: 34px;
    color: #fff;
    padding-left: 30px;
    align-items: center;
    padding-top: 8px;
}
.message-avatar {
    width: 36px;
    height: 36px;
    position: relative;
    overflow: hidden;
    border-radius: 50%;
    float: left;
    margin-left:15px;
}
.message-avatar2 {
  display: block;
  background-size: 32px 32px;
  width: 32px;
  height: 32px;
  float:left;
  margin-left:15px;
}
#message-bubble { background-image: url('data:image/png;base64,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');
  display: block;
  background-size: 32px 32px;
  width: 32px;
  height: 32px;
  float:left;
  margin-left:15px;
}
#message-bubble-small  { background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAABfGlDQ1BJQ0MgUHJvZmlsZQAAKJFjYGAqSSwoyGFhYGDIzSspCnJ3UoiIjFJgv8PAzcDDIMRgxSCemFxc4BgQ4MOAE3y7xsAIoi/rgsxK8/x506a1fP4WNq+ZclYlOrj1gQF3SmpxMgMDIweQnZxSnJwLZOcA2TrJBUUlQPYMIFu3vKQAxD4BZIsUAR0IZN8BsdMh7A8gdhKYzcQCVhMS5AxkSwDZAkkQtgaInQ5hW4DYyRmJKUC2B8guiBvAgNPDRcHcwFLXkYC7SQa5OaUwO0ChxZOaFxoMcgcQyzB4MLgwKDCYMxgwWDLoMjiWpFaUgBQ65xdUFmWmZ5QoOAJDNlXBOT+3oLQktUhHwTMvWU9HwcjA0ACkDhRnEKM/B4FNZxQ7jxDLX8jAYKnMwMDcgxBLmsbAsH0PA4PEKYSYyjwGBn5rBoZt5woSixLhDmf8xkKIX5xmbARh8zgxMLDe+///sxoDA/skBoa/E////73o//+/i4H2A+PsQA4AJHdp4IxrEg8AAAAJcEhZcwAACxMAAAsTAQCanBgAAAICaVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA1LjQuMCI+CiAgIDxyZGY6UkRGIHhtbG5zOnJkZj0iaHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyI+CiAgICAgIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICAgICAgICAgIHhtbG5zOmV4aWY9Imh0dHA6Ly9ucy5hZG9iZS5jb20vZXhpZi8xLjAvIgogICAgICAgICAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyI+CiAgICAgICAgIDxleGlmOlBpeGVsWURpbWVuc2lvbj4zOTwvZXhpZjpQaXhlbFlEaW1lbnNpb24+CiAgICAgICAgIDxleGlmOlBpeGVsWERpbWVuc2lvbj4zOTwvZXhpZjpQaXhlbFhEaW1lbnNpb24+CiAgICAgICAgIDx0aWZmOk9yaWVudGF0aW9uPjE8L3RpZmY6T3JpZW50YXRpb24+CiAgICAgIDwvcmRmOkRlc2NyaXB0aW9uPgogICA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgqdfEsEAAAB6UlEQVQ4EZVTvY7aQBCeXXuJQGAQ3IHhckeRQ0e6a+AN8gqp8gpJkTzHNSnyACnzCum5yJFSpLkiShUhbDechA1Ctncz3wafgkROZKSVd2e+b/48I2gnxhhR3rMsexVF0cckSayqXq9Tp9N5V61W37NC8zF8HCFE/kACkp2oIAhuFovF66IooHoQx3FoMBh8nkwmL5l4DwPjXYHILIZJp1+D4HteFL5yFQkpALAO2E5GG8ryjJRS2XQ6fd7r9X6CK3eefI78SxvjV1SF8zOktbYO4MTeWQcbZ6aCL8Ed61vMtQ6ub2e3d7rQT1zHJW1Q4mGBDZi8yNVsNvvEKOlyo75FcYTUHiWXLuEE2DiOX6Rp+kaGi9CmWAKO/aIs7tuNXN4vSXIlqPtYARac5ZK5x5IO4ZCFbDVbtnZBeyNxCL+nQy8ajQbJk9MTsv/5P0oAHsf3/QvZbrdF02vi/+5F+NcDRB518jzvA3PnfwZpFx3Gx6SMzMHi4XD4lt9artO1wdK4Lg8RN8U2hjv8tzPcpZQ2y+12u+J9GI9Goy2CuWEYEivtrKuKIizNZrOxiYAEwR6gabVaLR6Px1cc3S4TbG6SJnT57JLOL86p2+3aGnhAzHw+p9VqxWR026Ozp2c/+v3+NWezBrGU33869aLI6RUXAAAAAElFTkSuQmCC');
    display: block;
    background-size: 16px 16px;
    width: 32px;
    height: 32px;
    background-repeat: no-repeat;
    margin-left: 30px;
    float:left;
}
.cssNewMonth {
    height: 65px;
    background-color: #DFE7F1;
    font-size: 50px;
    color: #C3C4C7;
    padding-left: 50px;
}
.css_email {            /*  ---- NAME  ----- */
    font-size: 14px;
    color: rgb(133, 134, 136);
    padding-left: 6px;
    padding-top: 6px;
}
.css_email_external {   /*  ---- NAME  ----- */
    font-size: 14px;
    color: #F0A30B;
    padding-left: 6px;
    padding-top: 6px;
}
.css_created {          /*  ---- DATE  ----- */
    color: #C0C0C1;
    font-size: 11px;
}
.css_messagetext {      /*  ---- MESSAGE TEXT  ----- */
    color: rgb(51, 51, 51);
    font-size: 16px;
    font-weight: 400;
    margin-bottom: 20px;
    margin-top: 6px;
    margin-left: 20px;
    padding-bottom: 8px;
}
.css_message:hover {
    background-color: #F5F5F5;
    border-radius: 8px;
}
.css_message {
    margin-left: 50px;
}
#myheader
#myheader table,
#myheader td,
#myheader tbody {
    width: 900px;
    vertical-align: top;
    padding-left: 30px;
}
#myheader tr { /* to fix HTML code used in text messages */
    background-color: #fff !important;
}

#mytoc table,
#mytoc td,
#mytoc tbody {
    width: 150px !important;
    vertical-align: top !important;
}
/* IMAGE POPUP */
.image-animate-zoom {
   animation: animatezoom 0.6s
}

@keyframes animatezoom {
   from {
      transform: scale(0)
   }

   to {
      transform: scale(1)
   }
}
      .image-opacity,
      .image-hover-opacity:hover {
         opacity: 0.60
      }

      .image-opacity-off,
      .image-hover-opacity-off:hover {
         opacity: 1
      }

      .image-modal-content {
         margin: auto;
         background-color: #fff;
         position: relative;
         padding: 0;
         outline: 0;
         width: 90%;
         height:90%;
         max-height: 100vh;
         overflow: auto;
      }

      .image-modal {
         // THIS IS THE SHIT MAN!
         z-index: 3;
         display: none;
         padding-top: 50px;
         position: fixed;
         left: 0;
         top: 0;
         width: 100%;
         height: 100%;
         overflow: auto;
         background-color: rgb(0, 0, 0);
         background-color: rgba(0, 0, 0, 0.4)
      }
      /* TOOLTIP CSS (email address at member name) */
      .tooltip {
  position: relative;
  display: inline-block;
}

.tooltip .tooltiptext {
  visibility: hidden;

  background-color: lightgray;
  color: #000;
  font-size: 14px;
  text-align: center;
  border-radius: 6px;
  padding: 5px 5px;
  position: absolute;
  z-index: 1;
  bottom: 125%;
  left: 50%;
  margin-left: -60px;
  opacity: 0;
  transition: opacity 0.3s;
}

.tooltip .tooltiptext::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: #555 transparent transparent transparent;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}

/* For message quotes */
blockquote {
    font-size: 16px;
    display: inline-block;
    text-align: left;
    color: #000;
    word-wrap: break-word;
    white-space: pre-wrap;
    width: 95%;
    border-left: 4px solid #999;
    margin: 1em 0 1em .5em;
    padding-left: 30px
}

</style>
</head><body><div id='top'></div>"""



# FUNCTION convert date to format displayed with each message.
def convertDate(inputdate):
    return datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b %d, %H:%M  %A  (%Y)")


# FUNCTION used in the lay-out and statistics
#          takes a date and outputs "2018" (year), "Feb" (short month), "2" (month number)
def get_monthday(inputdate):
    myyear = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y")
    mymonth = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b")
    mymonthnr = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%m")
    return myyear, mymonth, mymonthnr


# FUNCTION finds URL's in message text and convert them to a hyperlink
def convertURL(inputtext):
    outputtext = inputtext
    urls = re.findall('(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&!:/~+#-]*[\w@?^=%&/~+#-])?', inputtext)
    if len(urls) > 0:
        for replaceThisURL in urls:
            replaceNewURL = replaceThisURL[0] + "://" + replaceThisURL[1] + replaceThisURL[2]
            outputtext = outputtext.replace(replaceNewURL, "<a href='" + str(replaceNewURL) + "' target='_blank'>" + str(replaceNewURL) + "</a>")
    return outputtext


def get_memberships(mytoken, myroom, myMaxMessages):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': myMaxMessages}
    resultjson = list()
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/memberships', headers=headers, params=payload)
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=")+len("cursor="):headerLink.rfind("==>")]
                payload = {'roomId': myroom, 'max': myMaxMessages, 'cursor': myCursor}
                resultjson = resultjson + result.json()["items"]
                continue
            else:
                resultjson = resultjson + result.json()["items"]
                print("          Number of members in messages: " + str(len(resultjson)))
                break
        except requests.exceptions.RequestException as e: # A serious problem, like an SSLError or InvalidURL
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                break
    return resultjson


def get_messages(mytoken, myroom, myMaxMessages):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': myMaxMessages}
    resultjsonmessages = list()
    messageCount = 0
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/messages', headers=headers, params=payload)
            messageCount += len(result.json()["items"])
            if "Link" in result.headers and messageCount < maxTotalMessages:  # there's MORE messages
                headerLink = result.headers["Link"]
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                print("          messages retrieved: " + str(messageCount) + "      (status: " + str(result.status_code) + ")")
                myBeforeMessage = result.headers.get('Link').split("beforeMessage=")[1].split(">")[0]
                payload = {'roomId': myroom, 'max': myMaxMessages, 'beforeMessage': myBeforeMessage}
                continue
            else:
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                print("          FINISHED total messages: " + str(messageCount))
                if "Link" in result.headers:   # There ARE more messages but the maxTotalMessages has been reached
                    print("          Reached configured maximum # messages (" + str(maxTotalMessages) + ")")
                break
        except requests.exceptions.RequestException as e: # A serious problem, like an SSLError or InvalidURL
            print("          EXCEPT status_code: " + str(e.status_code))
            print("          EXCEPT text: " + str(e.text))
            print("          EXCEPT headers", e.headers)
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                print("          EXCEPT ELSE e:" + e + " e.code:" + e.code)
                break
    return resultjsonmessages[0:maxTotalMessages]

# FUNCTION to turn Teams Space name into a valid filename string
def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

# FUNCTION get the Space-name (displayed in the header)
def get_roomname(mytoken, myroom):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    returndata = "webexteams-space-archive"
    try:
        result = requests.get('https://api.ciscospark.com/v1/rooms/' + myroom, headers=headers)
        if result.status_code == 401: #and "valid access token" in str(result.text):  # WRONG ACCESS TOKEN
            print("       **ERROR** 401 - Please check your Access Token in the .ini file.")
            print("           Note that your Access Token is only valid for 12 hours.")
            print("           Go here to get a new token:")
            print("           https://developer.webex.com/docs/api/getting-started")
            print("    ========================= STOPPED ======================= \n\n\n")
            exit()
        elif result.status_code == 404: #and "resource could not be found" in str(result.text):  # WRONG SPACE ID
            print("       **ERROR** 404 - Please check if the Space ID in your .ini file is correct.")
            print("    ========================= STOPPED ======================= \n\n\n")
            exit()
        elif result.status_code != 200:
            print("       **ERROR** <>200 Unknown Error occurred. status code: " + str(result.status_code) + "\n       Info: \n " + result.text)
            exit()
        elif result.status_code == 200:
            returndata = result.json()['title']
    except Exception as e:
        print(" ********* EXCEPTION *********" + str(e))
        if result.status_code == 429:
            print("       **ERROR** #1 get_roomname API call 429 - too many requests!! : " + str(result.status_code))
        else:
            print("       **ERROR** #1 get_roomname API call status_code: " + str(result.status_code))
            print("       **ERROR** #1 get_roomname API call status text: " + str(result.text))
        beep(3)
        exit()
    return str(returndata)


# FUNCTION get your details. Name: displayed in the header, email domain: to mark _other_ domains as 'external' messages
def get_me(mytoken):
    header = {'Authorization': "Bearer " + mytoken,'content-type': 'application/json; charset=utf-8'}
    result = requests.get(url='https://api.ciscospark.com/v1/people/me', headers=header)
    return result.json()


# FUNCTION get file URL
def get_WebexTeamsFile(url):
    print(".", end='', flush=True)  #Progress indicator
    request = urllib.request.Request(url, headers={"Accept": "application/json", "Content-Type": "application/json"})
    request.add_header("Authorization", "Bearer " + myToken)
    try:
        contents = urllib.request.urlopen(request)
    except Exception as e:
        myErrorList.append("     ** ERROR ** def get_WebexTeamsFile: " + str(e))
        contents = "**FileERROR**"
        beep(1)
    return contents


# FUNCTION download the actual file, if download files is enabled
def process_Files(fileData, msgid):
    filelist = list()
    for file_url in fileData:
        if downloadFiles not in ['images', 'files']:
            filelist.append("attachment")
            continue
        try:
            response = get_WebexTeamsFile(file_url)
        except Exception as e:
            print("    def process_Files: ** Problem with get_WebexTeamsFile file ")
            print("             Error message: " + str(e))
            continue
            beep(1)
        # if there was a problem retrieving the file (get_WebexTeamsFile) - skip
        if response == "**FileERROR**":
            print("X", end='', flush=True) # Progress indicator
            myErrorList.append("    def process_Files: Problem in message: " + str(msgid))
            continue
        content_disp = response.headers.get('Content-Disposition', None)
        if content_disp is not None:
            filename = content_disp.split("filename=")[1]
            filename = filename.replace('"', '')  # removing quotes from the filename
            filename = filename.replace('%', '-') # removing % signs from filename
            filename = filename.replace(':', '.') # replace Webex Teams screenshot ":" in filename with "."
            filename = filename.replace('/','-')  # Fix filesnames with slashes in it
            filename = filename.replace('\\','-') # replace back-slash with dash
            isImage = filename[-3:].lower() in ['png', 'jpg','bmp', 'gif', 'tif']
            if "image" in downloadFiles and not isImage:
                continue
            if downloadFiles in ['images', 'files']:
                if os.path.isfile(myAttachmentFolder + "/" + filename): # File exist? add '-<number>' to the filename.
                    filepartName = os.path.splitext(
                        os.path.basename(filename))[0]
                    filepartExtension = os.path.splitext(
                        os.path.basename(filename))[1]
                    filepartCounter = 1
                    while os.path.isfile(myAttachmentFolder + "/" + filepartName + "-" + str(filepartCounter) + filepartExtension):
                        filepartCounter += 1
                    filename = filepartName + "-" + str(filepartCounter) + filepartExtension
                with open(myAttachmentFolder + "/" + filename, 'wb') as f:
                    f.write(response.read())
                print(".", end='', flush=True) # Progress indicator
            filelist.append(filename)
        else:
            print("    ** ERROR ** def process_Files: Cannot save file- no Content-Disposition header received.")
            beep(1)
    return filelist


# FUNCTION download member avatar
def get_persondetails(mytoken, personlist):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    personlist = str(personlist)[2:-2].replace("', '",",")
    payload = {'id': personlist}
    resultjsonmessages = list()
    messageCount = 0
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/people', headers=headers, params=payload)
            if result.status_code != 200 and result.status_code != 429:
                print("     ** ERROR ** def get_persondetails. result.status_code: " + str(result.status_code))
            resultjsonmessages = resultjsonmessages + result.json()["items"]
            break
        except requests.exceptions.RequestException as e:
            print(e)
            print("\n\n get_persondetails Exception e: " + e + "\n\n")
            if "e.status_code" == "429":
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                break
    return resultjsonmessages

# ------------------------------------------------------------------------
#    Start of non-function code !
#
# ------------------------------------------------------------------------
# =====  GET SPACE NAME
try:
    roomName = get_roomname(myToken, myRoom)
    print(" #1 ----- Get SPACE NAME: '" + roomName + "'")
    outputFileName = format_filename(roomName)
    myAttachmentFolder = outputFileName + "-attachments"
except Exception as e:
    print(" #1 ----- get SPACE NAME: **ERROR** getting space name")
    print("             Error message: " + str(e))
    beep(3)
    exit()


# =====  CREATE FOLDER FOR ATTACHMENTS
print(" #2 ----- Create ATTACHMENT folder?: " + downloadFiles)
if len(downloadFiles) > 3: # that means it's not 'no' but 'images' or 'files'
    print("             folder exists? " + str(os.path.exists(myAttachmentFolder)))
    if not os.path.exists(myAttachmentFolder):
        print("             folder does NOT exist: " + myAttachmentFolder)
    else:   # check if folder-1 exists, if yes, check if folder-2 exists, etc.
        folderCounter = 1
        print("             folder EXISTS. Checking if " + myAttachmentFolder + "-" + str(folderCounter) + " exists!")
        while os.path.exists(myAttachmentFolder + "-" + str(folderCounter)):
            folderCounter += 1
        myAttachmentFolder += "-" + str(folderCounter)
    print("             Attachment Folder: " + myAttachmentFolder)
    os.makedirs(myAttachmentFolder)


# =====  GET MESSAGES
print(" #3 ----- Get MESSAGES")
try:
    WebexTeamsMessages = get_messages(myToken, myRoom, 900)
except Exception as e:
    print(" **ERROR** STEP #3: getting Messages")
    print("             Error message: " + str(e))
    traceback.print_exc()
    beep(3)
    exit()

# =====  GET MEMBER NAMES
print(" #4 ----- Get MEMBER List")
#     Put all members in a dictionary that contains: "email + fullname"
myPersonIdList = list() # used in avatar download
try:
    myMembers = get_memberships(myToken, myRoom, 500)
    for members in myMembers:
        try:
            myMemberList[str(members['personEmail'])] = str(members['personDisplayName'])
            if userAvatar == "link" and "personId" in members: # sometimes there's a member without person ID
                myPersonIdList.append(members['personId'])
        except Exception as e:
            myMemberList[str(members['personEmail'])] = str(members['personEmail'])
            print(" **ERROR** #4: Assigning personDisplayName for user: " + str(members.personId))
except Exception as e:
    print(" **ERROR** STEP #4: getting Memberlist (email address)")
    print("             Error message: " + str(e))
    beep(1)


# =====  GET MEMBER AVATARS
print(" #4b----- Get MEMBER Avatars: " + userAvatar + "  ", end='', flush=True)
if userAvatar == "link":
    userAvatarDict = dict()
    x=0
    y=len(myPersonIdList)
    chunksize = 80
    if y < 80:
        chunksize = y
    for i in range(x,y,chunksize): # ---- LOOPING OVER MemberDataList
        x=i
        abc = get_persondetails(myToken, myPersonIdList[x:x+chunksize])
        print(".", end='', flush=True)  # Progress indicator
        for persondetails in abc:
            try:
                userAvatarDict[persondetails['emails'][0]] = persondetails['avatar'].replace("~1600","~80")
            except:
                pass
    print("")
elif userAvatar == "":
    print("")
elif userAvatar == "download":
    print(" !! User Avatar download not supported yet.")
else:
    print("")

# =====  GET MY DETAILS
try:
    myOwnDetails = get_me(myToken)
    myEmail = "".join(myOwnDetails['emails'])
    myName = myOwnDetails['displayName']
    myDomain = myEmail.split("@")[1]
    print(" #5 ----- Get MY details: " + myEmail)
except Exception as e:
    print(" #5 ----- Get MY details: **ERROR** : " + str(e))


# =====  SET/CREATE VARIABLES
tocList = "<div class=''>"
statTotalFiles = 0
statTotalImages = 0
statTotalMessages = len(WebexTeamsMessages)
myDomainStats = dict()
statMessageMonth = dict()
previousEmail = ""
previousMonth = ""


# ======  GENERATE HTML HEADER
print(" #6 ----- Generate HTML header")
print("          Messages Processed:  " + str(statTotalMessages))
htmlheader += "<div class='cssRoomName'>   " + roomName + "&nbsp;&nbsp;&nbsp;<br><span style='float:left;margin-top:8px;font-size:10px;color:#fff'> CREATED: <span style='color:yellow'>" + \
    str(currentDate) + "</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; File Download: <span style='color:yellow'>" + str(downloadFiles).upper() + \
    "</span>&nbsp;&nbsp; Generated by: <span style='color:yellow'>" + \
    myName + "</span> &nbsp;&nbsp;&nbsp; Sort old-new: <span style='color:yellow'>" + \
    sortOldNew.replace("yes", "yes (default)") + "</span> &nbsp;&nbsp;&nbsp; Script version: " + __version__ + "</span> </div><br>"
htmldata = ""


# ====== GENERATE HTML FOR EACH MESSAGE
print(" #7 ----- Generate HTML code for each message")
if sortOldNew == "yes":  # Sorting messages 'old to new', unless configured otherwise
    WebexTeamsMessages = sorted(WebexTeamsMessages, key=lambda k: k['created'])
if downloadFiles in ['images', 'files']:
    print("          + download files ", end='', flush=True)

for msg in WebexTeamsMessages:
    if len(msg) < 5:
        continue        # message empty
    if 'text' not in msg:
        continue        # message without 'text' key
    data_created = convertDate(str(msg['created']))
    if "html" in msg:   # if html is there, use it to automatically deal with markdown
        data_text = convertURL(str(msg['html']))
    else:
        data_text = convertURL(str(msg['text']))
        if "<code>" in data_text:
            if "</code>" not in data_text:
                data_text += "</code>"
    try:  # Put email & name in variable
        data_email = str(msg['personEmail'])
        data_name = myMemberList[msg['personEmail']]
    except:
        data_name = data_email
    if '@' in data_email and "error.com" not in data_email:
        domain = str(data_email.split('@')[1])
        myDomainStats[domain] = myDomainStats.get(domain, 0) + 1
    messageYear, messageMonth, messageMonthNr = get_monthday(msg['created'])
    # ====== GENERATE MONTH STATISTICS
    statMessageMonthKey = messageYear + " - " + messageMonthNr + "-" + messageMonth
    statMessageMonth[statMessageMonthKey] = statMessageMonth.get(
        statMessageMonthKey, 0) + 1
    if messageMonth != previousMonth:
        htmldata += "<div class='cssNewMonth' id='" + statMessageMonthKey + "'>   " + messageYear + "    <span style='color:#C3C4C7'>" + \
            messageMonth + "</span><span style='float:right; font-size:16px; padding-top:24px;margin-right: 15px'><a href='#top'>back to top</a></span></div>&nbsp;&nbsp;"
    # ====== if PREVIOUS email equals current email, then skip header
    if data_email != previousEmail:  # Currently only displaying time/date if the message author CHANGES
        if userAvatar == "link" and data_email in userAvatarDict:
            htmldata += "<img src='" + userAvatarDict[data_email] + "' class='message-avatar'  width='36px' height='36px'/><div class='css_message'>"
        else:
            htmldata += "<div id='message-bubble'></div><div class='css_message'>"
        msgDomain = data_email.split("@")[1]    # Get message sender domain
        if myDomain == msgDomain:               # If domain <> own domain, use different color
            htmldata += "<span class='css_email' title='" + data_email + "'>" + data_name + "   </span>"
        else:
            htmldata += "<span class='css_email_external' title='" + data_email + "'>" + data_name + "   </span>"
        htmldata += "<span class='css_created'>" + data_created + "   </span>"
    else:
        htmldata += "<div id='message-bubble-small'></div><div class='css_message'>"
    # ====== DEAL WITH MENTIONS IN A MESSAGE
    if 'mentionedPeople' in msg:
        try:
            mentionstep1 = str(msg['html']).split("</spark-mention>")[0]
            mentionstep2 = mentionstep1.rsplit(">")[-1]
            data_text = data_text.replace(mentionstep2, "<div style='color:red;display:inline;'>@" + mentionstep2 + "</div>")
        except:
            print(" **ERROR** processing mentions, don't worry, I will continue")

    htmldata += "<div class='css_messagetext'>" + data_text
    # ====== DEAL WITH FILE ATTACHMENTS IN A MESSAGE
    if 'files' in msg:
        htmldata += "<span style='color:brown'> "
        for myfilename in msg['files']:
            myFiles = process_Files(msg['files'],msg['id']) # sending msg id for troubleshooting purposes
            for filename in myFiles:
                # IMAGE POPUP
                if filename[-3:].lower() in ['png', 'jpg', 'bmp', 'gif', 'tif'] and (downloadFiles == "images" or downloadFiles == "files"):
                    htmldata += "<br><div style='padding-left: 50px;'><img src='" + myAttachmentFolder + "/" + filename + \
                        "' title='click to zoom' style='max-width:700px;max-height:100px;cursor:pointer' onclick='onClick(this)' class='image-hover-opacity'/></div>"
                    statTotalImages += 1
                elif downloadFiles == "files":
                    htmldata += "<br>attached file: <a href='" + myAttachmentFolder + \
                        "/" + filename + "'>" + myAttachmentFolder + "/" + filename + "</a>"
                    statTotalFiles += 1
                else:
                    htmldata += "<br>attached file: " + filename + "</a>"
                    statTotalFiles += 1
        htmldata += "</span>"
    htmldata += "</div>"
    htmldata += "</div>"
    previousEmail = data_email
    previousMonth = messageMonth


# ======  SORT DOMAIN USER STATISTICS
myDomainStatsSorted = sorted(
    [(v, k) for k, v in myDomainStats.items()], reverse=True)
myDomainStatsSorted = myDomainStatsSorted[0:10]  # only want the top 10
returntextDomain = ""
returntextMsgMonth = ""


# ======  TABLE OF CONTENTS
tocList += "<table id='mytoc' style='width: 95%;'>"
if sortOldNew == "yes":
    mytest = sorted(statMessageMonth.items(), reverse=False)
else:
    mytest = sorted(statMessageMonth.items(), reverse=True)
for k, v in mytest:
    # indents for all months except January (easy to see new years)
    if "Jan" not in k[10:]:
        tocList += "<tr><td>&nbsp;&nbsp;&nbsp;"
    else:
        tocList += "<tr><td>"
    tocList += "<a href='#" + k + "'>" + k[0:6] + " " + k[10:] + "</a></td>"
    tocList += "<td><span style='color:grey;display:inline-block;font-size:12px;'>" + str(
        v) + "</span></td></tr>"
# If message sorting is old-to-new, also sort the TOC
messageType = "latest"
if sortOldNew == "no": messageType = "oldest"
tocList += "<tr><td colspan='2'>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'><a href='#endoffile'>" + messageType + " message</a></span></td></tr>"
tocList += "</table>"


# ======  DOMAIN MESSAGE STATISTICS
returntextDomain += "<table id='mytoc'>"
for domain in myDomainStatsSorted:
    returntextDomain += "<tr><td>" + domain[1] + "</td><td>" + str(domain[0]) + "</td>"
returntextDomain += "</table>"


# ======  MESSAGE & FILE STATISTICS
tocStats = "<table id='mytoc'>"
tocStats += "<tr><td># of messages: </td><td>" + str(statTotalMessages) + "</td></tr>"
if downloadFiles in ['images', 'files']:
    tocStats += "<tr><td> # images: </td><td>" + str(statTotalImages) + "</td></tr>"
    tocStats += "<tr><td> # files: </td><td>" + str(statTotalFiles) + "</td></tr>"
else:
    tocStats += "<tr><td><span style='color:grey'># files or images: </td><td>" + str(statTotalFiles) + "</span></td></tr>"
# if not ALL messages have been archived: show message
if statTotalMessages > maxTotalMessages -10:
    tocStats += "<tr><td colspan='2'><br><span style='color:grey;font-size:10px;'>space contains more than " + str(statTotalMessages) + " messages</td></tr>"
tocStats += "</table>"


# ======  HEADER
newtocList = "<table id='myheader'> <tr>"
newtocList += "<td> <strong>Index</strong><br>" + tocList + " </td>"
newtocList += "<td> <strong>Numbers</strong><br>" + tocStats + " </td>"
newtocList += "<td> <strong>Message Stats</strong><br>" + returntextDomain + " </td>"
newtocList += "</tr> </table></div><br><br>"
# ====== IMAGE POPUP
imagepopuphtml = """      <div id="modal01" class="image-modal" onclick="this.style.display='none'">
         <div class="image-modal-content image-animate-zoom">
            <img id="img01" style="width:100%">
         </div>
      </div>
         <script>
            function onClick(element) {
               document.getElementById("img01").src = element.src;
               document.getElementById("modal01").style.display = "block";
            }
         </script>

"""

# ======  FOOTER
htmlfooter = "<br><br><div class='cssNewMonth' id='endoffile'> end of file &nbsp;&nbsp;<span style='float:right; font-size:16px; margin-right:15px; padding-top:24px;'><a href='#top'>back to top</a></span></div><br><br>"

# ======  PUT EVERYTHING TOGETHER
print("\n #7 ----- Finalizing HTML")
htmldata = htmlheader + newtocList + htmldata + htmlfooter + imagepopuphtml + "</body></html>"


# ======  WRITE HTML to FILE
with open(outputFileName + ".html", 'w', encoding='utf-8') as f:
    print(htmldata, file=f)
print(" #8 ------------------------- ready -------------------------\n\n")

if len(myErrorList) > 0:
    print("    -------------------- Error Messages ---------------------")
    for myerrors in myErrorList:
        print(" > " + myerrors)
# ------------------------ the end ------------------------
