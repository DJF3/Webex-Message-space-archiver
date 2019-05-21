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
import codecs
import datetime
import urllib.request
import re
import time
import traceback
import sys
import os
import shutil
import math
import string
from pathlib import Path
import configparser
try:
    assert sys.version_info >= (3, 6)
except:
    print("\n\n **ERROR** Minimum Python version is 3.6. Please visit this site to\n           install a newer Python version: https://www.python.org/downloads/ \n\n")
    exit()
try:
    import requests
except ImportError:
    print("\n\n **ERROR** Missing library 'requests'. Please visit the following site to\n           install 'requests': http://docs.python-requests.org/en/master/user/install/ \n\n")
    exit()

#--------- DO NOT CHANGE ANYTHING BELOW ---------
__author__ = "Dirk-Jan Uittenbogaard"
__email__ = "duittenb@cisco.com"
__version__ = "0.19"
__copyright__ = "Copyright (c) 2019 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
sleepTime = 3
version = __version__
printPerformanceReport = False
printErrorList = True
currentDate = datetime.datetime.now().strftime("%x %X")
configFile = "webexteamsarchive-config.ini"
myMemberList = dict()
myErrorList = list()
downloadAvatarCount = 1

def beep(count): # PLAY SOUND (for errors)
    for x in range(0,count):
        print(chr(7), end="", flush=True)
    return

print("\n\n\n #0 ========================= START =========================")
config = configparser.ConfigParser(allow_no_value=True)
# --- CHECK if config file exists and if the mandatory settings entries are present.
if os.path.isfile("./" + configFile):
    try:
        config.read('./' + configFile)
        if config.has_option('Archive Settings', 'downloadfiles'):
            print(" *** NOTE!\n     Please change the key 'downloadfiles' in your .ini file to 'download'\n     or rename your .ini file and run this script to generate a new .ini file\n ***")
            beep(3)
            downloadFiles = config['Archive Settings']['downloadfiles'].lower().strip()
        else:
            downloadFiles = config['Archive Settings']['download'].lower().strip()
        sortOldNew = config['Archive Settings']['sortoldnew']
        myToken = config['Archive Settings']['mytoken']
        if config.has_option('Archive Settings', 'myroom'): # Added to deal with old naming in .ini files
            myRoom = config['Archive Settings']['myroom']
        if config.has_option('Archive Settings', 'myspaceid'): # Replacing the old 'myroom' setting
            myRoom = config['Archive Settings']['myspaceid']
        outputFileName = config['Archive Settings']['outputfilename']
        maxTotalMessages = config['Archive Settings']['maxtotalmessages']
        if maxTotalMessages:
            if 'd' in maxTotalMessages: # Example: maxTotalMessages = 60d = 60 days.
                msgMaxAge = int(maxTotalMessages.replace("d",""))
                maxTotalMessages = 999999
            else:
                maxTotalMessages = int(maxTotalMessages)
                msgMaxAge = 0
        else:
            maxTotalMessages = 1000
            msgMaxAge = 0
        userAvatar = config['Archive Settings']['useravatar']
        outputToJson = config['Archive Settings']['outputjson']
    except Exception as e:  # Error: keys missing from .ini file
        print(" **ERROR** reading webexteamsarchive-config.ini file settings.\n    ERROR: " + str(e))
        print("    Check if your .ini file contains the following keys: \n        download, sortoldnew, mytoken, myspaceid, outputfilename, useravatar, maxtotalmessages, outputjson")
        print("    Rename your .ini file, re-run this script (generating correct file)\n    and put your settings in the new .ini file")
        print(" ---------------------------------------\n\n")
        beep(3)
        exit()
else:  # CREATE config file (when it does not exist)
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.add_section('Archive Settings')
        config.set('Archive Settings', '; Your Cisco Webex Teams developer token (NOTE: tokens are valid for 12 hours!)')
        config.set('Archive Settings', 'mytoken', '__YOUR_TOKEN_HERE__')
        config.set('Archive Settings', ';')
        config.set('Archive Settings', '; Space ID: Enter your token above and run this script followed by a search argument')
        config.set('Archive Settings', ';     "archivescript.py searchstring" - returns lists of spaces containing "searchstring" + space ID')
        config.set('Archive Settings', ';     OR: go to https://developer.webex.com/endpoint-rooms-get.html')
        config.set('Archive Settings', ';         "login, API reference, rooms, list all rooms", set "max" to 900 and run ')
        config.set('Archive Settings', 'myspaceid', '__YOUR_SPACE_ID_HERE__')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; Download:  "no"      : (default) only show text "file attachment"')
        config.set('Archive Settings', ';            "images"  : download images only')
        config.set('Archive Settings', ';            "files"   : download files & images')
        config.set('Archive Settings', ';     First try the script with downloadFiles set to "no".')
        config.set('Archive Settings', ';     Downloading Large spaces with many files will take a LOT of time')
        config.set('Archive Settings', 'download', 'no')
        config.set('Archive Settings', ';  ')
        config.set('Archive Settings', ';  ')
        config.set('Archive Settings', '; Download/show user avatar')
        config.set('Archive Settings', ';     no       - (default) show user initials (fast)')
        config.set('Archive Settings', ';     link     - link to avatar image - does need internet connection')
        config.set('Archive Settings', ';     download - download avatar images')
        config.set('Archive Settings', 'useravatar', 'no')
        config.set('Archive Settings', ';   ')
        config.set('Archive Settings', ';   ')
        config.set('Archive Settings', '; Max Messages: - Maximum number of messages you want to download.')
        config.set('Archive Settings', ';                 important if you want to limit archiving HUGE spaces')
        config.set('Archive Settings', ';               - 30d = 30 days, 365d = all msg from the last year')
        config.set('Archive Settings', ';               - empty (default): 1000 messages')
        config.set('Archive Settings', 'maxTotalMessages', '1000')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', '; Output filename: Name of the generated HTML file. EMPTY: use the spacename')
        config.set('Archive Settings', ';      (downloadFiles enabled? Attachment foldername: same as spacename')
        config.set('Archive Settings', 'outputfilename', '')
        config.set('Archive Settings', ';     ')
        config.set('Archive Settings', ';     ')
        config.set('Archive Settings', '; Sorting of messages. "yes" (default) means: last message at the bottom,')
        config.set('Archive Settings', ';      just like in the Webex Teams client. "no" = latest message at the top')
        config.set('Archive Settings', 'sortoldnew', 'yes')
        config.set('Archive Settings', ';      ')
        config.set('Archive Settings', ';      ')
        config.set('Archive Settings', '; Output message data to html _PLUS_ a .json and/or .txt file')
        config.set('Archive Settings', ';      no       (default) only generate .html file')
        config.set('Archive Settings', ';      yes/both output message data as .json and .txt file')
        config.set('Archive Settings', ';      json     output message data as .json file')
        config.set('Archive Settings', ';      txt      output message data as .txt file')
        config.set('Archive Settings', 'outputjson', 'no')
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
    goExitError += "\n   **ERROR** the 'download' setting must be: 'no', 'images' or 'files'"
if not sortOldNew in ['yes', 'no']:
    sortOldNew = "yes"
if not myToken or len(myToken) < 55:
    goExitError += "\n   **ERROR** your token is not set or not long enough"
if not myRoom or len(myRoom) < 70:
    goExitError += "\n   **ERROR** your space ID is not set or not long enough"
if not outputFileName or len(outputFileName) < 2:
    outputFileName = ""
if not userAvatar in ['no', 'link', 'download']:
    goExitError += "\n   **ERROR** the 'useravatar' setting must be: 'no', 'link' or 'download'"
if not outputToJson in ['yes', 'no', 'both', 'txt', 'json']:
    outputToJson = "no"
if outputToJson in ['txt', 'yes', 'both']:
    outputToText = True
else:
    outputToText = False
if len(sys.argv) > 1:  # Command line parameter provided? Then SEARCH for spaces
    print(" searching spaces for: " + ' '.join(sys.argv[1:]))
else:
    if msgMaxAge == 0:
        maxMessageString = str(maxTotalMessages)
    else:
        maxMessageString = str(msgMaxAge) + " days"
    print("    download:" + downloadFiles + " - Max messages:" + maxMessageString + " - Avatars: " + userAvatar)
if len(goExitError) > 76:   # length goExitError = 66. If error: it is > 76 characters --> print errors + exit
    print(goExitError + "\n ------------------------------------------------------------------\n\n")
    beep(3)
    exit()


# --- HTML header code containing images, styling info (CSS)
htmlheader = """<!DOCTYPE html><html><head><meta charset="utf-8"/><style media='screen' type='text/css'>
body { font-family: 'HelveticaNeue', 'Helvetica Neue', 'Helvetica', 'Arial', 'Lucida Grande', 'sans-serif';
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

#avatarCircle {
    border-radius: 50%;
    width: 31px;
    height: 31px;
    padding: 0px;
    background: #fff;
    border: 1px solid #DDD;
    color: #888;
    text-align: center;
    font-size: 20px;
    line-height: 30px;
    float: left;
    margin-left: 15px;
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
/* paperclip icon for file attachments */
#fileicon { background-image: url('data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiA/PjwhRE9DVFlQRSBzdmcgIFBVQkxJQyAnLS8vVzNDLy9EVEQgU1ZHIDEuMS8vRU4nICAnaHR0cDovL3d3dy53My5vcmcvR3JhcGhpY3MvU1ZHLzEuMS9EVEQvc3ZnMTEuZHRkJz48c3ZnIGlkPSJMYXllcl8xIiBzdHlsZT0iZW5hYmxlLWJhY2tncm91bmQ6bmV3IDAgMCA2NCA2NDsiIHZlcnNpb249IjEuMSIgdmlld0JveD0iMCAwIDY0IDY0IiB4bWw6c3BhY2U9InByZXNlcnZlIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIj48c3R5bGUgdHlwZT0idGV4dC9jc3MiPgoJLnN0MHtmaWxsOiMxMzQ1NjM7fQo8L3N0eWxlPjxnPjxnIGlkPSJJY29uLVBhcGVyY2xpcCIgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTI3LjAwMDAwMCwgMzgwLjAwMDAwMCkiPjxwYXRoIGNsYXNzPSJzdDAiIGQ9Ik0tMTEwLjMtMzI2Yy0yLjQsMC00LjYtMC45LTYuMy0yLjZjLTEuNy0xLjctMi42LTMuOS0yLjYtNi4zYzAtMi40LDAuOS00LjYsMi42LTYuM2wyNS40LTI1LjQgICAgIGM0LjYtNC42LDEyLjItNC42LDE2LjgsMGMyLjIsMi4yLDMuNSw1LjIsMy41LDguNGMwLDMuMi0xLjIsNi4xLTMuNSw4LjRsLTE5LDE5bC0yLTJsMTktMTljMy41LTMuNSwzLjUtOS4zLDAtMTIuOCAgICAgYy0zLjUtMy41LTkuMy0zLjUtMTIuOCwwbC0yNS40LDI1LjRjLTEuMiwxLjEtMS44LDIuNy0xLjgsNC4zYzAsMS42LDAuNiwzLjIsMS44LDQuM2MyLjQsMi40LDYuMiwyLjQsOC42LDBsMTktMTkgICAgIGMxLjItMS4yLDEuMi0zLjIsMC00LjRjLTEuMi0xLjItMy4yLTEuMi00LjQsMGwtMTIuNywxMi43bC0yLTJsMTIuNy0xMi43YzIuMy0yLjMsNi0yLjMsOC4zLDBjMi4zLDIuMywyLjMsNiwwLDguM2wtMTksMTkgICAgIEMtMTA1LjctMzI2LjktMTA3LjktMzI2LTExMC4zLTMyNiIgaWQ9IkZpbGwtNjAiLz48L2c+PC9nPjwvc3ZnPg==');
    display: block;
    width: 32px;
    height: 32px;
    background-repeat: no-repeat;
    float:left;
}

.cssNewMonth {
    height: 65px;
    background-color: #DFE7F1;
    font-size: 50px;
    color: #C3C4C7;
    padding-left: 50px;
    margin-bottom: 10px;
}
/*  ---- NAME  ----- */
.css_email {
    font-size: 14px;
    color: rgb(133, 134, 136);
    padding-left: 6px;
    padding-top: 6px;
}
/*  ---- NAME  ----- */
.css_email_external {
    font-size: 14px;
    color: #F0A30B;
    padding-left: 6px;
    padding-top: 6px;
}
/*  ---- DATE  ----- */
.css_created {
    color: #C0C0C1;
    font-size: 13px;
    padding-left: 50px;
    line-height: 14px;
}
/*  ---- MESSAGE TEXT  ----- */
.css_messagetext {
    color: rgb(51, 51, 51);
    font-size: 16px;
    font-weight: 400;
    margin-bottom: 20px;
    margin-top: 6px;
    margin-left: 20px;
    padding-bottom: 8px;
}
/*  ---- MESSAGE TEXT IMAGES ----- */
.css_messagetext img {
    margin-top: 10px;
    padding-left: 50px;
    max-width: 700px;
    max-height: 100px;
    cursor: pointer;
    color: #686868;
    font-size: 14px;
    display: inline;
    line-height: 14px;
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
/* to fix HTML code used in text messages */
#myheader tr {
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
         max-width: 90vh;
         max-height: 100vh;
         overflow: auto;
      }

      .image-modal {
         /* For image popups */
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
         background-color: rgba(0, 0, 0, 0.4);
      }
      /* TOOLTIP CSS (email address at member name) */
      .tooltip {
  position: relative;
  display: inline-block;
}
.imagepopup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    max-width: 90%;
    max-height: 90%;
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
/* For quotes */
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
/* SCROLL TO TOP button */
#myBtn {
  display: none;
  position: fixed;
  bottom: 20px;
  right: 30px;
  z-index: 99;
  font-size: 18px;
  border: none;
  outline: none;
  background-color: red;
  color: white;
  cursor: pointer;
  padding: 8px;
  border-radius: 2px;
}
#myBtn:hover {
  background-color: #555;
}
</style>
</head><body><div id='top'></div><button onclick="topFunction()" id="myBtn" title="Go to top">&uarr;</button>
"""

# FUNCTION calculates the difference between your local timezone and UTC.
#          Webex teams messages are stored with a UTC date. With this information
#          we can update the UTC dates from messages to your local timezone dates.
def timeDeltaWithUTC():
    dateNOW = datetime.datetime.now()       # your current time
    dateUTC = datetime.datetime.utcnow()    # the  current UTC time (used for Teams messages)
    if dateNOW > dateUTC:   # On a map you're RIGHT of UTC
       UTChourDelta = round((dateNOW-dateUTC).seconds / 3600, 1)       #print("   A>B")
    else:                   # On a map you're LEFT of UTC
       UTChourDelta = round((dateUTC-dateNOW).seconds / 3600, 1) * -1
    return UTChourDelta

# FUNCTION convert date to format displayed with each message. Used in HTML generation.
#          this function checks the timezone difference between you and UTC and updates the
#          message date/time so the actual times for your timezone are displayed.
def convertDate(inputdate, hourdelta): # msg['created']
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    dateMSG = datetime.datetime.strptime(inputdate, FMT)
    dateMSGnew = dateMSG + datetime.timedelta(hours=hourdelta)
    return datetime.datetime.strftime(dateMSGnew, "%b %d, %H:%M     (%A  -  %Y)")


# FUNCTION convert date to format displayed with each message. Used in HTML generation.
def convertDateOLD(inputdate):
    return datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b %d, %H:%M  %A  (%Y)")


# FUNCTION used in the lay-out and statistics. Used in HTML generation.
#          takes a date and outputs "2018" (year), "Feb" (short month), "2" (month number)
def get_monthday(inputdate):
    myyear = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y")
    mymonth = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b")
    mymonthnr = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%m")
    return myyear, mymonth, mymonthnr


# FUNCTION that returns the time difference between 2 dates in seconds
#           (to check if msg from the same author were send within 60 seconds)
def timedifference(newdate, previousdate):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    tdelta = datetime.datetime.strptime(newdate, FMT) - datetime.datetime.strptime(previousdate, FMT)
    return tdelta.seconds


# FUNCTION that returns the time difference between the msg-date and today (# of days)
#           (used when setting max messages to XX days instead of number of msgs)
def timedifferencedays(msgdate):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    tdelta = datetime.datetime.today() - datetime.datetime.strptime(msgdate,FMT)
    return tdelta.days


# FUNCTION finds URLs in message text + convert to a hyperlink. Used in HTML generation.
def convertURL(inputtext):
    outputtext = inputtext
    urls = re.findall('(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&!:/~+#-]*[\w@?^=%&/~+#-])?', inputtext)
    if len(urls) > 0:
        for replaceThisURL in urls:
            replaceNewURL = replaceThisURL[0] + "://" + replaceThisURL[1] + replaceThisURL[2]
            outputtext = outputtext.replace(replaceNewURL, "<a href='" + str(replaceNewURL) + "' target='_blank'>" + str(replaceNewURL) + "</a>")
    return outputtext


# FUNCTION to convert Markdown URL's [linktext](http://link.com)  to a clickable link
def convertMarkdownURL(msgtext):
    try:
        regex = r"alt(.*?)event\);\""
        matches = re.finditer(regex, msgtext, re.MULTILINE)
        matchDict = dict()  # create dictionary with match details so I can _reverse_ replace
        for matchNum, match in enumerate(matches, start=1):
            matchDict[matchNum] = [match.start(),match.end()]
        for i in sorted(matchDict.keys(), reverse=True):
            msgtext = msgtext.replace(msgtext[matchDict[i][0]:matchDict[i][1]],"target='_blank'")
    except:
        test = msgtext
        print(" **ERROR** replacing markdown URL's in text: " + msgtext)
    return msgtext



# FUNCTION that retrieves a list of Space members (name + email address)
def get_memberships(mytoken, myroom, maxmembers):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': maxmembers}
    resultjson = list()
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/memberships', headers=headers, params=payload)
            # **DJ** does it make sense to check for status_code here?
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=")+len("cursor="):headerLink.rfind("==>")]
                payload = {'roomId': myroom, 'max': maxmembers, 'cursor': myCursor}
                resultjson += result.json()["items"]
                continue
            else:
                resultjson += result.json()["items"]
                print("          Number of space members: " + str(len(resultjson)))
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


# FUNCTION that retrieves all Space messages - testing error 429 catching
def get_messages(mytoken, myroom, myMaxMessages):
    global maxTotalMessages
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': myMaxMessages}
    resultjsonmessages = list()
    messageCount = 0
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/messages', headers=headers, params=payload)
            messageCount += len(result.json()["items"])
            if "Link" in result.headers and messageCount < maxTotalMessages:  # there's MORE messages
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                # When retrieving multiple batches _check_ if the last message retrieved is _OLDER_. If yes, trim results to the max age.
                if msgMaxAge != 0:
                    msgAge = timedifferencedays(result.json()["items"][-1]["created"])
                    if msgAge > msgMaxAge:
                        print("          max messages reached (>" + str(msgMaxAge) + " days old)")
                        # NOW I set maxTotalMessages to the last msg index that should be included, based on msg age in days.
                        maxTotalMessages = next((index for (index,d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                        break
                print("          messages retrieved: " + str(messageCount)) # + "      (status: " + str(result.status_code) + ")")
                myBeforeMessage = result.headers.get('Link').split("beforeMessage=")[1].split(">")[0]
                payload = {'roomId': myroom, 'max': myMaxMessages, 'beforeMessage': myBeforeMessage}
                continue
            else:
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                if msgMaxAge != 0:
                    msgAge = timedifferencedays(result.json()["items"][-1]["created"])
                    lastMsgLocation = next((index for (index,d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                    maxTotalMessages = lastMsgLocation
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
    if maxTotalMessages == 0:
        print(" **ERROR** there are no messages. Please check your maxMessages setting and try again.")
        exit()
    return resultjsonmessages[0:maxTotalMessages]

# FUNCTION to turn Teams Space name into a valid filename string
def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

# FUNCTION get the Space-name (Used in the header + possibly for the filename)
def get_roomname(mytoken, myroom):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    returndata = "webexteams-space-archive"
    try:
        result = requests.get('https://api.ciscospark.com/v1/rooms/' + myroom, headers=headers)
        if result.status_code == 401:   # WRONG ACCESS TOKEN
            print("    -------------------------- ERROR ------------------------")
            print("       Please check your Access Token in the .ini file.")
            print("           Note that your Access Token is only valid for 12 hours.")
            print("           Go here to get a new token:")
            print("           https://developer.webex.com/docs/api/getting-started")
            print("    ------------------------- STOPPED ----------------------- \n\n\n")
            exit()
        elif result.status_code == 404: #and "resource could not be found" in str(result.text) --> WRONG SPACE ID
            print("       **ERROR** 404 - Please check if the Space ID in your .ini file is correct.")
            print("    ------------------------- STOPPED ----------------------- \n\n\n")
            exit()
        elif result.status_code != 200:
            print("       **ERROR** <>200 Unknown Error occurred. status code: " + str(result.status_code) + "\n       Info: \n " + result.text)
            exit()
        elif result.status_code == 200:
            returndata = result.json()['title']
    except Exception as e:  # **DJ** Really: do we need 429 error testing here?
        print(" ********* EXCEPTION *********" + str(e))
        if result.status_code == 429:
            print("       **ERROR** #1 get_roomname API call 429 - too many requests!! : " + str(result.status_code))
        else:
            print("       **ERROR** #1 get_roomname API call status_code: " + str(result.status_code))
            print("       **ERROR** #1 get_roomname API call status text: " + str(result.text))
        beep(3)
        exit()
    return str(returndata)


# FUNCTION get your details. Name: displayed in the header.
#          Also used to get your email domain: mark _other_ domains as 'external' messages
def get_me(mytoken):
    header = {'Authorization': "Bearer " + mytoken,'content-type': 'application/json; charset=utf-8'}
    result = requests.get(url='https://api.ciscospark.com/v1/people/me', headers=header)
    return result.json()


# FUNCTION to convert file-size "bytes" to readable format (KB,MB,GB)
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


# FUNCTION download the images & files if enabled
def process_Files(fileData):
    global myErrorList
    filelist = list()
    # REQUEST File headers
    for url in fileData:
        headers = {"Authorization": f"Bearer {myToken}","Accept-Encoding": ""}
        r = requests.head(url, headers=headers)
        if r.status_code == 404:  # Item must have been deleted since url was retrieved
            continue
        try:
            filename = str(r.headers['Content-Disposition']).split("\"")[1]
        except e as Exception:
            filename = "error-getting-filename"
            myErrorList.append("def process_Files Header 'content-disposition' error for url: " + url)
        filename = format_filename(filename)
        filesize = convert_size(int(r.headers['Content-Length']))
        fileextension = os.path.splitext(filename)[1][1:].replace("\"","")
        filenamepart = os.path.splitext(filename)[0]
        if int(r.headers['Content-Length']) <= 0:
            # Not downloading 0 Byte files, only show the filename
            filelist.append(filename + "###" + filesize)
            continue
        if downloadFiles not in ['images', 'files']:
            # No file downloading --> just get the filename + size
            filelist.append(filename + "###" + filesize)
            continue
        if "image" in downloadFiles and fileextension not in ['png', 'jpg','bmp', 'gif', 'tif']:
            # File is not an image --> just get the filename + size
            filelist.append(filename + "###" + filesize)
            continue
        if fileextension.lower() in ['png', 'jpg','bmp', 'gif', 'tif']:
            # File is an image
            subfolder = "/images/"
        else:
            # File is a non-image file
            subfolder = "/files/"
        # CHECK if filename exists, if yes, add "-x" where x is a counter
        if downloadFiles in ['images', 'files']:
            if os.path.isfile(myAttachmentFolder + subfolder + filename): # File exist? add '-<number>' to the filename.
                filepartName = filenamepart
                filepartExtension = "." + fileextension
                filepartCounter = 1
                while os.path.isfile(myAttachmentFolder + subfolder + filepartName + "-" + str(filepartCounter) + filepartExtension):
                    filepartCounter += 1
                filename = filepartName + "-" + str(filepartCounter) + filepartExtension
        # DOWNLOAD file
        try:
            with requests.get(url, headers=headers, stream=True) as r:
                with open(myAttachmentFolder + subfolder + filename, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                filelist.append(filename + "###" + filesize)
        except Exception as e:
            print(f"----- ERROR:  {e}")
            myErrorList.append("def process_Files download failed for file: " + filename)
        print(".", end='', flush=True) # Progress indicator
    return filelist


# FUNCTION download member avatar. Will retry failed downloads max. 3 times.
def download_avatars(avatardictionary):
    global downloadAvatarCount
    retryDictionary = dict()
    for key, value in avatardictionary.items():
        filename = "".join(re.findall(r'[A-Za-z0-9]+', key))
        try:
            response = urllib.request.urlretrieve(value, myAttachmentFolder + "/avatars/" + filename)
        except Exception as e:
            global myErrorList
            myErrorList.append("def download_avatars download failed (attempt #" + str(downloadAvatarCount) + ") for user: " + key + " with URL: " + value)
            retryDictionary[key] = value # Create temp dictionary for failed avatar downloads - retry later
            print("X", end='', flush=True)  # Progress indicator
            continue
    if len(retryDictionary) > 0 and downloadAvatarCount < 4: # Try failed avatar downloads max 3 times
        myErrorList.append("             Avatar download attempt nr. " + str(downloadAvatarCount))
        time.sleep(1)
        downloadAvatarCount += 1
        download_avatars(retryDictionary)


# FUNCTION download member avatar URLs
def get_persondetails(mytoken, personlist):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    personlist = str(personlist)[2:-2].replace("', '",",")
    payload = {'id': personlist}
    resultjsonmessages = list()
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

# FUNCTION download ALL SPACES
def get_searchspaces(mytoken, searchstring):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'sortBy': 'lastactivity', 'max': 900}
    resultjsonspaces = dict()
    resultjson = list()
    while True:
        try:
            result = requests.get('https://api.ciscospark.com/v1/rooms', headers=headers, params=payload)
            if result.status_code == 401:  # Wrong access token # **DJ** does it make sense to check for status_code here?
                print("    -------------------------- ERROR ------------------------")
                print("       Please check your Access Token in the .ini file.")
                print("           Note that your Access Token is only valid for 12 hours.")
                print("           Go here to get a new token:")
                print("           https://developer.webex.com/docs/api/getting-started")
                print("    ------------------------- STOPPED ----------------------- \n\n\n")
                exit()
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=")+len("cursor="):headerLink.rfind(">")]
                payload = {'sortBy': 'lastactivity', 'max': 900, 'cursor': myCursor}
                resultjson += resultjson + result.json()["items"]
                continue
            else:
                resultjson += resultjson + result.json()["items"]
                print(" Number of spaces retrieved: " + str(len(resultjson)))
                break
        except requests.exceptions.RequestException as e: # A serious problem, like an SSLError or InvalidURL
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                break
    for spaces in resultjson:
        try:
            if searchstring.lower() in spaces['title'].lower():
                resultjsonspaces[spaces['id']] = spaces['title']
        except:
            continue
    return resultjsonspaces

performanceReport = "Performance Report - Space Archive Script \n ----------------------------------------------------"
_start_time = time.time()
def startTimer():
    global _start_time
    _start_time = time.time()
def stopTimer(description):
    t_sec = round(time.time() - _start_time,2)
    global performanceReport
    performanceReport += f"\n {t_sec:5.2f} " + description

# ------------------------------------------------------------------------
#    Start of non-function code !  #lastfunction
#
# ------------------------------------------------------------------------

# ===== SEARCH SPACES: If parameter provided, use it to search in your spaces, display result and exit
if len(sys.argv) > 1:
    spaceSearchResults = get_searchspaces(myToken, ' '.join(sys.argv[1:]))
    for key, value in spaceSearchResults.items():
        print(" -- NAME: " + value)
        print("      id:      " + key)
    print("    ------------------------- ready -------------------------\n\n")
    exit()



# =====  GET SPACE NAME
startTimer()
try:
    roomName = get_roomname(myToken, myRoom)
    print(" #1 ----- Get SPACE NAME: '" + roomName + "'")
except Exception as e:
    print(" #1 ----- get SPACE NAME: **ERROR** getting space name")
    print("             Error message: " + str(e))
    beep(3)
    exit()
stopTimer("Get Space Name")
# If no outputFileName has been configured: use the space name
if outputFileName == "":
    outputFileName = format_filename(roomName)
myAttachmentFolder = outputFileName



startTimer()
# =====  GET MESSAGES
print(" #2 ----- Get MESSAGES")
try:
    WebexTeamsMessages = get_messages(myToken, myRoom, 900)
except Exception as e:
    print(" **ERROR** STEP #2: getting Messages")
    print("             Error message: " + str(e))
    traceback.print_exc()
    beep(3)
    exit()
stopTimer("get messages")



# ===== CREATE USERLIST
# Collect only userId's of users who wrote a message. For those users we will
#   retrieve details & download/link avatars
startTimer()
uniqueUserIds = list()
for myUser in WebexTeamsMessages:
    if myUser['personId'] not in uniqueUserIds:
        uniqueUserIds.append(myUser['personId'])
stopTimer("get unique user ids")



# =====  GET MEMBER NAMES
startTimer()
print(" #3 ----- Get MEMBER List") # Put ALL members in a dictionary that contains: "email + fullname"
try:
    myMembers = get_memberships(myToken, myRoom, 500)
    for members in myMembers:
        try:
            myMemberList[str(members['personEmail'])] = str(members['personDisplayName'])
        except Exception as e:  # IF there's no personDisplayName, use email
            myMemberList[str(members['personEmail'])] = str(members['personEmail'])
except Exception as e:
    print(" **ERROR** STEP #3: getting Memberlist (email address)")
    print("             Error message: " + str(e))
    beep(1)
stopTimer("get memberlist")



startTimer()
# =====  CREATE FOLDERS FOR ATTACHMENTS & AVATARS
print(" #4a ----- Create folder for HTML. Download files? " + downloadFiles)
if not os.path.exists(myAttachmentFolder):
    print("             folder does NOT exist: " + myAttachmentFolder)
else:   # check if folder-01 exists, if yes, check if folder-02 exists, etc.
    folderCounter = 1
    print("             folder EXISTS. Checking if " + myAttachmentFolder + "-" + "{:02d}".format(folderCounter) + " exists!")
    while os.path.exists(myAttachmentFolder + "-" + "{:02d}".format(folderCounter)):
        folderCounter += 1
    myAttachmentFolder += "-" + "{:02d}".format(folderCounter)
print("             Attachment Folder: " + myAttachmentFolder)
os.makedirs(myAttachmentFolder)
if userAvatar == "download":
    os.makedirs(myAttachmentFolder + "/avatars/")
if downloadFiles == "files":
    os.makedirs(myAttachmentFolder + "/files/")
    os.makedirs(myAttachmentFolder + "/images/")
if downloadFiles == "images":
    os.makedirs(myAttachmentFolder + "/images/")
stopTimer("create folders")



# =====  GET MEMBER AVATARS
startTimer()
print(" #4b----- MEMBER Avatars: collect avatar Data (" + str(len(uniqueUserIds)) + ")  ", end='', flush=True)
if userAvatar == "link" or userAvatar == "download":
    userAvatarDict = dict()    # userAvatarDict[your@email.com] = "https://webexteamsavatarurl"
    x=0
    y=len(uniqueUserIds)
    if 80 > y:
        chunksize = y
    else:
        chunksize = 80
    if y < 80:
        chunksize = y
    for i in range(x,y,chunksize): # - LOOPING OVER MemberDataList
        x=i
        abc = get_persondetails(myToken, uniqueUserIds[x:x+chunksize])
        print(".", end='', flush=True)  # Progress indicator
        for persondetails in abc:
            try:
                userAvatarDict[persondetails['id']] = persondetails['avatar'].replace("~1600","~80")
            except:
                pass
stopTimer("get avatars")
print("")
startTimer()
if userAvatar == "link" or userAvatar == "download":
    print(" #4c----- MEMBER Avatars: downloading avatar files for " + str(len(userAvatarDict)) + ")  ", end='', flush=True)
    if userAvatar == "download":
        download_avatars(userAvatarDict)
        if downloadAvatarCount > 0:
            print("")
stopTimer("download avatars")



# =====  GET MY DETAILS
startTimer()
try:
    myOwnDetails = get_me(myToken)
    myEmail = "".join(myOwnDetails['emails'])
    myName = myOwnDetails['displayName']
    myDomain = myEmail.split("@")[1]
    print(" #5 ----- Get MY details: " + myEmail)
except Exception as e:
    print(" #5 ----- Get MY details: **ERROR** : " + str(e))
stopTimer("get my details")



# =====  SET/CREATE VARIABLES
tocList = "<div class=''>"
statTotalFiles = 0
statTotalImages = 0
statTotalMessages = len(WebexTeamsMessages)
myDomainStats = dict()
statMessageMonth = dict()
previousEmail = ""
previousMonth = ""
previousMsgCreated = ""
UTChourDelta = timeDeltaWithUTC()
TimezoneName = str(time.tzname)

# Write ALL JSON to a FILE to be used as input (not putting load on Webex Teams APIs)
startTimer()
if outputToJson == "yes" or outputToJson == "both" or outputToJson == "json":
    if inputFileName == "":
        with open(myAttachmentFolder + "/" + outputFileName + ".json", 'w', encoding='utf-8') as f:
            json.dump(WebexTeamsMessages, f)
stopTimer("output to json")



# ======  GENERATE HTML HEADER
print(" #6 ----- Generate HTML header")
print("          Messages Processed:  " + str(statTotalMessages))
htmlheader += f"<div class='cssRoomName'>   {roomName}&nbsp;&nbsp;&nbsp;<br><span style='float:left;margin-top:8px;font-size:10px;color:#fff'> CREATED: <span style='color:yellow'>{currentDate}</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Generated by: <span style='color:yellow'>{myName}</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Message timezone: <span style='color:yellow'>{TimezoneName}</span>&nbsp;&nbsp;&nbsp; version: {version}&nbsp;&nbsp;&nbsp;<br>Sort old-new: <span style='color:yellow'>" + sortOldNew.replace("yes", "yes (default)") + f"</span> &nbsp;&nbsp; Max messages: <span style='color:yellow'> {maxMessageString} </span>&nbsp;&nbsp; File Download: <span style='color:yellow'>{downloadFiles.upper()}</span> </span> </div><br>"



htmldata = ""
textOutput = ""
if outputToText:
    textOutput += f"------------------------------------------------------------\n {roomName}\n------------------------------------------------------------\nCREATED:        {currentDate}\nFile Download:  {downloadFiles.upper()}\nGenerated by:   {myName}\nSort old-new:   " + sortOldNew.replace("yes", "yes (default)") + f"\nMax messages:   {maxMessageString} \nversion:        {version} \nTimezone:           {TimezoneName}"



# ====== GENERATE HTML FOR EACH MESSAGE
startTimer()
print(" #7 ----- Generate HTML code for each message")
if sortOldNew == "yes":  # Sorting messages 'old to new', unless configured otherwise
    WebexTeamsMessages = sorted(WebexTeamsMessages, key=lambda k: k['created'])
if downloadFiles in ['images', 'files']:
    print("          + download " + downloadFiles + " ", end='', flush=True)
statTotalMentions = 0
for msg in WebexTeamsMessages:
    if len(msg) < 5:
        continue        # message empty
    if 'text' not in msg:
        continue        # message without 'text' key
    data_created = convertDate(str(msg['created']),UTChourDelta)
    if "html" in msg:   # if html is there, use it to automatically deal with markdown
        # Check if there are Markdown hyperlinks [linktext](www.cisco.com) as these look very different
        if "sparkBase.clickEventHandler(event)" in str(msg['html']):
            data_text = convertMarkdownURL(str(msg['html']))
        else:
            data_text = convertURL(str(msg['html']))
    else:
        data_text = convertURL(str(msg['text']))
        if "<code>" in data_text:
            if "</code>" not in data_text:
                data_text += "</code>"
    if data_text == "" and 'files' not in msg and 'mentionedPeople' not in msg:
        continue
        # ^^^ empty text without mentions or attached images/files: SKIP
    try:  # Put email & name in variable
        data_email = str(msg['personEmail'])
        data_userid = str(msg['personId'])
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
        htmldata += f"<div class='cssNewMonth' id='{statMessageMonthKey}'>   {messageYear}    <span style='color:#C3C4C7'>" + \
            messageMonth + "</span><span style='float:right; font-size:16px; padding-top:24px;margin-right: 15px'><a href='#top'>back to top</a></span></div>"
        if outputToText:  # for .txt output
            textOutput += f"\n\n---------- {messageYear}    {messageMonth} ------------------------------\n\n"
    # ====== if PREVIOUS email equals current email, then skip header
    if (data_email != previousEmail) or (data_email == previousEmail and timedifference(msg["created"], previousMsgCreated) > 60):
        if userAvatar == "link" and data_userid in userAvatarDict:
            htmldata += f"<img src='{userAvatarDict[data_userid]}' class='message-avatar'  width='36px' height='36px'/><div class='css_message'>"
        elif userAvatar == "download" and data_userid in userAvatarDict:
            htmldata += f"<img src='avatars/" + data_userid + "' class='message-avatar'  width='36px' height='36px'/><div class='css_message'>"
        else: # User that may not exist anymore --> use email as name
            if data_name == data_email:
                htmldata += f"<div id='avatarCircle'>{data_name[0:2].upper()}</div><div class='css_message'>"
            else:
                try:
                    htmldata += "<div id='avatarCircle'>" + data_name.split(" ")[0][0].upper() + data_name.split(" ")[1][0].upper()+ "</div><div class='css_message'>"
                except:  # Sometimes there's no "first/last" name. If one word, take the first 2 characters.
                    htmldata += "<div id='avatarCircle'>" + data_name[0:2].upper() + "</div><div class='css_message'>"
            # ^^ show circle with initials instead of bubble.
        msgDomain = data_email.split("@")[1]    # Get message sender domain
        if myDomain == msgDomain:               # If domain <> own domain, use different color
            htmldata += f"<span class='css_email' title='{data_email}'>{data_name}</span>"
        else:
            htmldata += f"<span class='css_email_external' title='{data_email}'>{data_name}</span>"
        htmldata += f"<span class='css_created'>{data_created}</span>"
    else:
        htmldata += "<div class='css_message'>"

    if outputToText:  # for .txt output
        textOutput += f"{msg['created']}  {data_email} - "

    # ====== DEAL WITH MENTIONS IN A MESSAGE
    if 'mentionedPeople' in msg:
        try:
            statTotalMentions += 1
            for item in msg['mentionedPeople']:
                texttoreplace = "<spark-mention data-object-type=\"person\" data-object-id=\"" + item + "\">"
                data_text = data_text.replace(texttoreplace,"<span style='color:red;display:inline;'>@")
            data_text = data_text.replace("</spark-mention>","</span>")
        except:
            print(" **ERROR** processing mentions, don't worry, I will continue")
    htmldata += "<div class='css_messagetext'>" + data_text
    if outputToText and 'mentionedPeople' in msg:  # for .txt output
        p = re.compile(r'<.*?>')
        textOutput += p.sub('', data_text)
        textOutput += "\n\r"
    if outputToText and 'mentionedPeople' not in msg:  # for .txt output
        textOutput += f"{data_text}\n\r"

    # ====== DEAL WITH FILE ATTACHMENTS IN A MESSAGE
    if 'files' in msg:
        if data_text != "":
            htmldata += "<br>"
        myFiles = process_Files(msg['files'])
        for filename in myFiles:
            # IMAGE POPUP
            filename, filesize = filename.split("###")
            fileextension = filename[-3:].lower()
            if fileextension in ['png', 'jpg', 'bmp', 'gif', 'tif'] and (downloadFiles in ["images", "files"]):
                htmldata += f"<img src='images/{filename} ' title='click to zoom' onclick='onClick(this)' class='image-hover-opacity'/><br><div class='css_created'>{filesize} <strong>  -  </strong> {filename} </div>"
            elif downloadFiles == "files":
                htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'><a href='files/{filename}'>{filename}</a>  ({filesize})"
            else:
                htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'> {filename}   ({filesize})</span>"
            if fileextension in ['png', 'jpg', 'bmp', 'gif', 'tif']:
                statTotalImages += 1
            else:
                statTotalFiles += 1
            if outputToText:  # for .txt output
                textOutput += f"                           Attachment: {filename} ({filesize})\n"
        htmldata += "</span>"
    htmldata += "</div>"
    htmldata += "</div>"
    previousEmail = data_email
    previousMonth = messageMonth
    previousMsgCreated = msg['created']
stopTimer("generate HTML")



# ======  *SORT* DOMAIN USER STATISTICS
startTimer()
myDomainStatsSorted = sorted(
    [(v, k) for k, v in myDomainStats.items()], reverse=True)
myDomainStatsSorted = myDomainStatsSorted[0:10]  # only want the top 10
returntextDomain = ""
returntextMsgMonth = ""
stopTimer("sorting messages")



# ======  TABLE OF CONTENTSstartTimer()
startTimer()
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
messageType = "last"
if sortOldNew == "no": messageType = "last"
tocList += "<tr><td colspan='2'>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'><a href='#endoffile'>" + messageType + " message</a></span></td></tr>"
tocList += "</table>"



# ======  DOMAIN MESSAGE STATISTICS
returntextDomain += "<table id='mytoc'>"
for domain in myDomainStatsSorted:
    returntextDomain += f"<tr><td>{domain[1]}</td><td>{domain[0]}</td>"
returntextDomain += "</table>"



# ======  MESSAGE & FILE STATISTICS
tocStats = "<table id='mytoc'>"
tocStats += "<tr><td># of messages: </td><td>" + str(statTotalMessages) + "</td></tr>"
tocStats += "<tr><td> # images: </td><td>" + str(statTotalImages) + "</td></tr>"
tocStats += "<tr><td> # files: </td><td>" + str(statTotalFiles) + "</td></tr>"
tocStats += "<tr><td># mentions: </td><td>" + str(statTotalMentions) + "</td></tr>"
# if not ALL messages have been archived: show message
if statTotalMessages > maxTotalMessages -10:
    tocStats += "<tr><td colspan='2'><br><span style='color:grey;font-size:10px;'>space contains more than " + str(statTotalMessages) + " messages</span></td></tr>"
tocStats += "</table>"
if outputToText:  # for .txt output
    textOutput += f"\n\n\n STATISTICS \n--------------------------\n # of messages : {statTotalMessages}\n # of images   : {statTotalImages}\n # of files    : {statTotalFiles}\n # of mentions : {statTotalMentions}\n\n\n"
# ======  HEADER
newtocList = "<table id='myheader'> <tr>"
newtocList += "<td> <strong>Index</strong><br>" + tocList + " </td>"
newtocList += "<td> <strong>Numbers</strong><br>" + tocStats + " </td>"
newtocList += "<td> <strong>Messages top-10 domains</strong><br>" + returntextDomain + " </td>"
newtocList += "</tr> </table></div><br><br>"
# ====== IMAGE POPUP
imagepopuphtml = """      <div id="modal01" class="image-modal" onclick="this.style.display='none'">
         <div class="image-modal-content image-animate-zoom">
            <img id="img01" class="imagepopup">
         </div>
      </div>
         <script>
            function onClick(element) {
               document.getElementById("img01").src = element.src;
               document.getElementById("modal01").style.display = "block";
            }
            document.addEventListener('keydown', function(event) {
                const key = event.key;
                if (key === "Escape") {
                   document.getElementById("modal01").style.display = "none";
                }
            });
            // SCROLL TO TOP button
            window.onscroll = function() {scrollFunction()};
            function scrollFunction() {
              if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                document.getElementById("myBtn").style.display = "block";
              } else {
                document.getElementById("myBtn").style.display = "none";
              }
            }

            // When the user clicks on the button, scroll to the top of the document
            function topFunction() {
              document.body.scrollTop = 0;
              document.documentElement.scrollTop = 0;
            }
         </script>

"""
# ======  FOOTER
htmlfooter = "<br><br><div class='cssNewMonth' id='endoffile'> end of file &nbsp;&nbsp;<span style='float:right; font-size:16px; margin-right:15px; padding-top:24px;'><a href='#top'>back to top</a></span></div><br><br>"

# ======  PUT EVERYTHING TOGETHER
print("\n #7 ----- Finalizing HTML")
htmldata = htmlheader + newtocList + htmldata + htmlfooter + imagepopuphtml + "</body></html>"
stopTimer("toc,domainstats,header,footer + combining")



# ======  WRITE HTML to FILE
startTimer()
with open(myAttachmentFolder + "/" + outputFileName + ".html", 'w', encoding='utf-8') as f:
    print(htmldata, file=f)
print(" #8 ------------------------- ready -------------------------\n\n")
beep(1)
stopTimer("write html to file")

if len(myErrorList) > 0 and printErrorList:
    print("    -------------------- Error Messages ---------------------")
    for myerrors in myErrorList:
        print(" > " + myerrors)
# ------------------------ the end ------------------------

if printPerformanceReport:
    print("    -------------------- Performance ---------------------")
    print(performanceReport)

if outputToText:
    with open(myAttachmentFolder + "/" + outputFileName + ".txt", 'w', encoding='utf-8') as f:
        print(textOutput, file=f)
