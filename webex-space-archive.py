# -*- coding: utf-8 -*-
"""Webex Message Space Archive Script.
Creates a single HTML file with the messages of a Webex Message space
Info/Requirements/release-notes: https://github.com/DJF3/Webex-Message-space-archiver
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
import re
import time
import sys
import os
import shutil # for file-download with requests
import math   # for converting bytes to KB/MB/GB
import string
from pathlib import Path
import configparser
try:
    assert sys.version_info[0:2] >= (3, 6)
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
__version__ = "0.21"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
sleepTime = 3
version = __version__
printPerformanceReport = False
printErrorList = True
max_messages = 700
currentDate = datetime.datetime.now().strftime("%x %X")
configFile = "webexspacearchive-config.ini"
myMemberList = dict()
myErrorList = list()
downloadAvatarCount = 1

def beep(count): # PLAY SOUND (for errors)
    for x in range(0,count):
        print(chr(7), end="", flush=True)
    return

print("\n\n\n========================= START =========================")
config = configparser.ConfigParser(allow_no_value=True)
# ----------- CONFIG FILE: check if config file exists and if the mandatory settings entries are present.
# --
if os.path.isfile("./" + configFile):
    try:
        config.read('./' + configFile)
        if config.has_option('Archive Settings', 'downloadfiles'):
            print(" *** NOTE!\n     Please change the key 'downloadfiles' in your .ini file to 'download'\n     or rename your .ini file and run this script to generate a new .ini file\n\n")
            beep(3)
            downloadFiles = config['Archive Settings']['downloadfiles'].lower().strip()
        else:
            downloadFiles = config['Archive Settings']['download'].lower().strip()
        if config['Archive Settings']['sortoldnew'] == "yes":
            sortOldNew = True
        else:
            sortOldNew = False
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
        print(f" **ERROR** reading webexspacearchive-config.ini file settings.\n    ERROR: {e}")
        print("    Check if your .ini file contains the following keys: \n        download, sortoldnew, mytoken, myspaceid, outputfilename, useravatar, maxtotalmessages, outputjson")
        print("    Rename your .ini file, re-run this script (generating correct file)\n    and put your settings in the new .ini file")
        print(" ---------------------------------------\n\n")
        beep(3)
        exit()
elif os.path.isfile("./" + configFile.replace("webexspacearchive-config","webexteamsarchive-config")):
        print(f" **ERROR** OLD config filename found!\n   RENAME 'webexteamsarchive-config.ini' to 'webexspacearchive-config.ini' and retry \n\n")
        beep(3)
        exit()

else:
    # ----------- CONFIG FILE: CREATE new config file because it does not exist
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.add_section('Archive Settings')
        config.set('Archive Settings', '; Your Cisco Webex developer token (NOTE: tokens are valid for 12 hours!)')
        config.set('Archive Settings', 'mytoken', '__YOUR_TOKEN_HERE__')
        config.set('Archive Settings', ';')
        config.set('Archive Settings', '; Space ID: Enter your token above and run this script followed by a search argument')
        config.set('Archive Settings', ';     "archivescript.py searchstring" - returns lists of spaces matching "searchstring"')
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
        config.set('Archive Settings', '; Sorting of messages. "yes" (default) means: newest message at the bottom,')
        config.set('Archive Settings', ';      just like in the Webex Message client. "no" = newest message at the top')
        config.set('Archive Settings', 'sortoldnew', 'yes')
        config.set('Archive Settings', ';      ')
        config.set('Archive Settings', ';      ')
        config.set('Archive Settings', '; Output message data to html _PLUS_ a .json and/or .txt file')
        config.set('Archive Settings', ';      no       (default) only generate .html file')
        config.set('Archive Settings', ';      yes/both output message data as .json and .txt file')
        config.set('Archive Settings', ';      json     output message data as .json file')
        config.set('Archive Settings', ';      txt      output message data as .txt file')
        config.set('Archive Settings', 'outputjson', 'no')
        config.set('Archive Settings', ';       ')
        config.set('Archive Settings', ';       ')
        with open('./' + configFile, 'w') as configfile:
            config.write(configfile)
    except Exception as e:  # Error creating config file
        print(" ** ERROR ** creating config file")
        print(f"             Error message: {e}")
        beep(3)
    print(f"\n\n ------------------------------------------------------------------ \n ** WARNING ** Config file '{configFile}' does not exist.  \n               Creating empty configuration file. \n --> EDIT the configuration in this file and re-run this script.\n ------------------------------------------------------------------\n\n")
    # STOP - the script because you need a valid configuration file first
    exit()

# ----------------------------------------------------------------------------------------
#   CHECK if the configuration VALUES are valid. If not, print error messsage and exit
# ----------------------------------------------------------------------------------------
goExitError = "\n\n ------------------------------------------------------------------"
if not downloadFiles in ['no', 'images', 'files']:
    goExitError += "\n   **ERROR** the 'download' setting must be: 'no', 'images' or 'files'"
if not myToken or len(myToken) < 55:
    goExitError += "\n   **ERROR** your token is not set or not long enough"
if not myRoom and len(sys.argv) < 1 or len(myRoom) < 70 and len(sys.argv) < 1:
    goExitError += "\n   **ERROR** your space ID is not set or not long enough\n    RUN this script with a search parameter (space name) to find your space ID"
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
    print(" searching spaces for: \"" + ' '.join(sys.argv[1:]) + "\"")
else:
    if msgMaxAge == 0:
        maxMessageString = str(maxTotalMessages)
    else:
        maxMessageString = str(msgMaxAge) + " days"
    print(f"    download: {downloadFiles} - Max messages: {maxMessageString} - Avatars: {userAvatar} ")
if len(goExitError) > 76:   # length goExitError = 66. If error: it is > 76 characters --> print errors + exit
    print(goExitError + "\n ------------------------------------------------------------------\n\n")
    beep(3)
    exit()


# ----------------------------------------------------------------------------------------
#   HTML header code containing images, styling info (CSS)
# ----------------------------------------------------------------------------------------
htmlheader = """<!DOCTYPE html><html><head><meta charset="utf-8"/>
<script>
function show(yearnr)
{
	var myElement = 'expand year-' + yearnr;
	if(document.getElementById(myElement).style.display == 'none')
		document.getElementById(myElement).style.display = 'block';
        document.getElementById('yeararrow' + yearnr).innerHTML = '⇊';
	else
		document.getElementById(myElement).style.display = 'none';
        document.getElementById('yeararrow' + yearnr).innerHTML = '⇉';
}
</script>
<style type='text/css'>
body { font-family: 'HelveticaNeue-Light', 'Helvetica Neue Light', 'Helvetica', 'Arial', 'Lucida Grande', 'sans-serif';}
div[class^="expand"], div[class*=" year-"] {
    display:block;
}
.cssRoomName {
    height: 76px;
    background-color: #029EDB;
    font-size: 34px;
    color: #fff;
    padding-left: 30px;
    align-items: center;
    padding-top: 8px;
    min-width: 1000px;
}

#avatarCircle,
.avatarCircle {
    border-radius: 50%;
    width: 31px;
    height: 31px;
    padding: 0px;
    background: #fff;
    /* border: 1px solid #D2D5D6; */
    color: #000;
    text-align: center;
    font-size: 14px;
    line-height: 30px;
    float: left;
    margin-left: 15px;
    background-color: #D2D5D6;
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
/*  ------ NAME  ------ */
.css_email {
    font-size: 14px;
    color: rgb(133, 134, 136);
    padding-left: 6px;
    padding-top: 6px;
}
/*  ------ NAME  ------ */
.css_email_external {
    font-size: 14px;
    color: #F0A30B;
    padding-left: 6px;
    padding-top: 6px;
}
/*  ------ DATE  ------ */
.css_created {
    color: #C0C0C1;
    font-size: 13px;
    padding-left: 50px;
    line-height: 14px;
    display: inline-block;
}
/*  ------ MESSAGE TEXT  ------ */
.css_messagetext {
    color: rgb(51, 51, 51);
    font-size: 16px;
    font-weight: 400;
    margin-bottom: 20px;
    margin-top: 6px;
    margin-left: 55px;
    padding-bottom: 10px;
}

/*  ------ MESSAGE TEXT IMAGES ------ */
.css_messagetext img {
    margin-top: 10px;
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
    margin-left: 10px;
}
.css_message_thread {
    border-left: 4px solid #dadada;
    margin-left: 80px;
    padding-left: 00px;
    margin-top: -20px;
}

#myheader
#myheader table,
#myheader td,
#myheader tbody {
    width: 900px;
    vertical-align: top;
    padding-left: 10px;
    min-width: 120px;
}
#myheader td {
    vertical-align: top;
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
    min-width: 150px;
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
.filesize {
    display: inline-block;
    color: #b3afaf;
}
.css_imagetext {
    display: inline-block;
    color: #8e8e8e;
    font-size: 12px;
    padding-left: 20px;
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
    /* display: inline-block; */
    text-align: left;
    color: #000;
    word-wrap: break-word;
    white-space: pre-wrap;
    width: 95%;
    border-left: 4px solid #dadada;
    margin: 1em 0 1em .5em;
    padding-left: 30px
}
/* SCROLL TO TOP button */
@media screen {
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
}
/* Hiding 'back to top' button from printed page */
@media print {
   #myBtn {
     display: none !important;
     position: fixed;
  }
}
#myBtn:hover {
  background-color: #555;
}
.card_class {
    background-color: #2f9033;
    font-size: 11px;
    color: white;
}
.month_msg_count {
    color:grey;
    display:inline-block;
    font-size:12px;
}
</style>
</head><body><div id='top'></div><button onclick="topFunction()" id="myBtn" title="Go to top">&uarr;</button>
"""

# ----------------------------------------------------------------------------------------
#   FUNCTIONS
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# FUNCTION calculates the difference between your local timezone and UTC.
#          Webex messages are stored with a UTC date. With this information
#          we can update the UTC dates from messages to your local timezone dates.
def timeDeltaWithUTC():
    dateNOW = datetime.datetime.now()       # your current time
    dateUTC = datetime.datetime.utcnow()    # the  current UTC time (used for messages)
    if dateNOW > dateUTC:   # On a map you're RIGHT of UTC
       UTChourDelta = round((dateNOW-dateUTC).seconds / 3600, 1)       #print("   A>B")
    else:                   # On a map you're LEFT of UTC
       UTChourDelta = round((dateUTC-dateNOW).seconds / 3600, 1) * -1
    return UTChourDelta

# ----------------------------------------------------------------------------------------
# FUNCTION convert date to format displayed with each message. Used in HTML generation.
#          This function checks the timezone difference between you and UTC and updates the
#          message date/time so the actual times for your timezone are displayed.
def convertDate(inputdate, hourdelta):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    dateMSG = datetime.datetime.strptime(inputdate, FMT)
    dateMSGnew = dateMSG + datetime.timedelta(hours=hourdelta)
    return datetime.datetime.strftime(dateMSGnew, "%A, %H:%M      (%b %d, %Y)")


# ----------------------------------------------------------------------------------------
# FUNCTION used in the lay-out and statistics HTML generation.
#          takes a date and outputs "2018" (year), "Feb" (short month), "2" (month number)
def get_monthday(inputdate):
    myyear = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y")
    mymonth = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%b")
    mymonthnr = datetime.datetime.strptime(inputdate, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%m")
    return myyear, mymonth, mymonthnr


# ----------------------------------------------------------------------------------------
# FUNCTION that returns the time difference between 2 dates in seconds
#           (to check if msgs from 1 author were send within 60 seconds: no new msg header)
def timedifference(newdate, previousdate):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    tdelta = datetime.datetime.strptime(newdate, FMT) - datetime.datetime.strptime(previousdate, FMT)
    return tdelta.seconds


# ----------------------------------------------------------------------------------------
# FUNCTION that returns the time difference between the msg-date and today (# of days)
#           (used when setting max messages to XX days instead of number of msgs)
def timedifferencedays(msgdate):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
    tdelta = datetime.datetime.today() - datetime.datetime.strptime(msgdate,FMT)
    return tdelta.days


# ----------------------------------------------------------------------------------------
# FUNCTION finds URLs in message text + convert to a hyperlink. Used in HTML generation.
def convertURL(inputtext):
    outputtext = inputtext
    urls = re.findall('(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&!:/~+#-]*[\w@?^=%&/~+#-])?', inputtext)
    urls = set(urls)
    if len(urls) > 0:
        for replaceThisURL in urls:
            replaceNewURL = replaceThisURL[0] + "://" + replaceThisURL[1] + replaceThisURL[2]
            outputtext = outputtext.replace(replaceNewURL, "<a href='" + str(replaceNewURL) + "' target='_blank'>" + str(replaceNewURL) + "</a>")
    return outputtext


# ----------------------------------------------------------------------------------------
# FUNCTION to convert all Markdown URL's [linktext](http://link.com) to clickable links
def convertMarkdownURL(msgtext, whichreplace):
    try:
        if whichreplace == 1:
            regex = r"alt=(.*?)event\);\""
        if whichreplace == 2:
            regex = r"\ onClick=(.*?)event\)\;\""
        matches = re.finditer(regex, msgtext, re.MULTILINE)
        matchDict = dict()  # create dictionary with match details so I can _reverse_ replace
        for matchNum, match in enumerate(matches, start=1):
            matchDict[matchNum] = [match.start(),match.end()]
        for i in sorted(matchDict.keys(), reverse=True):
            msgtext = msgtext[0:matchDict[i][0]] + " target='_blank'" + msgtext[matchDict[i][1]:]
    except:
        test = msgtext
        print(f" **ERROR** replacing markdown URL's in text: {msgtext}")
    return msgtext


# ----------------------------------------------------------------------------------------
# FUNCTION that retrieves a list of Space members (displayName + email address)
def get_memberships(mytoken, myroom, maxmembers):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': maxmembers}
    resultjson = list()
    while True:
        try:
            result = requests.get('https://webexapis.com/v1/memberships', headers=headers, params=payload)
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=")+len("cursor="):headerLink.rfind("==>")]
                payload = {'roomId': myroom, 'max': maxmembers, 'cursor': myCursor}
                resultjson += result.json()["items"]
                continue
            else:
                resultjson += result.json()["items"]
                print(f"          Number of space members: {len(resultjson)}")
                break
        except requests.exceptions.RequestException as e: # For problems like SSLError/InvalidURL
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                print(" *** ERROR *** getting space members. Error message: {result.status_code}\n {e}")
                break
    return resultjson


# ----------------------------------------------------------------------------------------
# FUNCTION that retrieves all space messages - testing error 429 catching
def get_messages(mytoken, myroom, myMaxMessages):
    global maxTotalMessages
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': myMaxMessages}
    resultjsonmessages = list()
    messageCount = 0
    progress_counter = 0
    while True:
        try:
            result = requests.get('https://webexapis.com/v1/messages', headers=headers, params=payload)
            if result.status_code != 200 and result.status_code != 429:
                print(" *** ERROR *** There is a problem retrieving specific messages. You could try to lower the max_messages variable in the .py file until it works\n\n")
                beep(3)
                exit()
            messageCount += len(result.json()["items"])
            progress_counter += 1
            sys.stdout.write('\r')
            sys.stdout.write("          %d %s " % (messageCount, '*'*progress_counter))
            sys.stdout.flush()
            if "Link" in result.headers and messageCount < maxTotalMessages:  # there's MORE messages
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                # When retrieving multiple batches _check_ if the last message retrieved
                #      is _OLDER_ than the configured max msg age (in the .ini). If yes: trim results to the max age.
                if msgMaxAge != 0:
                    msgAge = timedifferencedays(result.json()["items"][-1]["created"])
                    if msgAge > msgMaxAge:
                        print("          max messages reached (>" + str(msgMaxAge) + " days old)")
                        # NOW I set maxTotalMessages to the last msg index that should be included, based on msg age in days.
                        maxTotalMessages = next((index for (index,d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                        break
                myBeforeMessage = result.headers.get('Link').split("beforeMessage=")[1].split(">")[0]
                payload = {'roomId': myroom, 'max': myMaxMessages, 'beforeMessage': myBeforeMessage}
                continue
            else:
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                if msgMaxAge != 0:
                    msgAge = timedifferencedays(result.json()["items"][-1]["created"])
                    lastMsgLocation = next((index for (index,d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                    maxTotalMessages = lastMsgLocation
                print(f" FINISHED total messages: {messageCount}")
                if "Link" in result.headers:   # There ARE more messages but the maxTotalMessages has been reached
                    print(f"          Reached configured maximum # messages ({maxTotalMessages})")
                break
        except requests.exceptions.RequestException as e: # A serious problem, like an SSLError or InvalidURL
            print(f"          EXCEPT status_code: {e.status_code}")
            print(f"          EXCEPT text: {e.text}")
            print(f"          EXCEPT headers: {e.headers}")
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                print(f"          EXCEPT ELSE e: {e}     e.code: {e.code}")
                break
    if maxTotalMessages == 0:
        print(" **ERROR** there are no messages. Please check your maxMessages setting and try again.\n\n")
        beep(3)
        exit()
    return resultjsonmessages[0:maxTotalMessages]

# ----------------------------------------------------------------------------------------
# FUNCTION to turn Space name into a valid filename string
def format_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    return filename

# ----------------------------------------------------------------------------------------
# FUNCTION get the Space-name (Used in the header + optionally for the filename)
def get_roomname(mytoken, myroom):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    returndata = "webex-space-archive"
    try:
        result = requests.get('https://webexapis.com/v1/rooms/' + myroom, headers=headers)
        if result.status_code == 401:   # WRONG ACCESS TOKEN
            print("__________________________ ERROR ________________________")
            print("   Please check your Access Token in the .ini file.")
            print("       Note that your Access Token is only valid for 12 hours.")
            print("       Go here to get a new token:")
            print("       https://developer.webex.com/docs/api/getting-started")
            print("_________________________ STOPPED _______________________\n\n\n")
            beep(3)
            exit()
        elif result.status_code == 404:
            print("       **ERROR** Check if the Space ID in your .ini file is correct.\n         Find the Space ID? Run this script with the space name as parameter!")
            print("_________________________ STOPPED _______________________\n\n\n")
            beep(3)
            exit()
        elif result.status_code != 200:
            print(f"       **ERROR** Unknown Error occurred. status code: {result.status_code}\n       Info: \n {result.text}\n\n")
            beep(3)
            exit()
        elif result.status_code == 200:
            returndata = result.json()['title']
    except Exception as e:
        print(f"       **ERROR** #1 get_roomname API call status_code: {result.status_code}\n status_text: {result.text}\n Exception {e}\n\n")
        beep(3)
        exit()
    return str(returndata.strip())


# ----------------------------------------------------------------------------------------
# FUNCTION get your own details. Name: displayed in the header.
#          Also used to get your email domain: mark _other_ domains as 'external' messages
def get_me(mytoken):
    header = {'Authorization': "Bearer " + mytoken,'content-type': 'application/json; charset=utf-8'}
    result = requests.get(url='https://webexapis.com/v1/people/me', headers=header)
    return result.json()


# ----------------------------------------------------------------------------------------
# FUNCTION to convert file-size "bytes" to readable format (KB,MB,GB)
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


# ----------------------------------------------------------------------------------------
# FUNCTION to download message images & files (if enabled)
def process_Files(fileData, fileDate):
    global myErrorList
    filelist = list()
    for url in fileData:
        headers = {"Authorization": f"Bearer {myToken}","Accept-Encoding": ""}
        r = requests.head(url, headers=headers)
        if r.status_code == 404:  # Item must have been deleted since url was retrieved
            continue
        try:
            filename = str(r.headers['Content-Disposition']).split("\"")[1]
            # Files with no name or just spaces: fix so they can still be downloaded:
            if len(filename) < 1 or filename.isspace():
                filename = "unknown-filename"
            if filename == ('+' * (int(len(filename)/len('+'))+1))[:len(filename)]:
                filename = "unknown-filename"
                beep(1)
        except Exception as e:
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
        if "image" in downloadFiles and fileextension.lower() not in ['png', 'jpg','bmp', 'gif', 'tif', 'jpeg']:
            # File is not an image --> just get the filename + size
            filelist.append(filename + "###" + filesize)
            continue
        if fileextension.lower() in ['png', 'jpg','bmp', 'gif', 'tif', 'jpeg']:
            # File is an image
            subfolder = "/images/"
        else:
            # File is a non-image file
            subfolder = "/files/"
        # CHECK if filename exists, if yes, add "-x" where x is a counter
        if downloadFiles in ['images', 'files']:
            if os.path.isfile(myOutputFolder + subfolder + filename): # File exist? add '-<number>' to the filename.
                filepartName = filenamepart
                filepartExtension = "." + fileextension
                filepartCounter = 1
                while os.path.isfile(myOutputFolder + subfolder + filepartName + "-" + str(filepartCounter) + filepartExtension):
                    filepartCounter += 1
                filename = filepartName + "-" + str(filepartCounter) + filepartExtension
        # DOWNLOAD file
        try:
            with requests.get(url, headers=headers, stream=True) as r:
                with open(myOutputFolder + subfolder + filename, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                # Change file modified date
                try:
                    fileLocation = myOutputFolder + subfolder + filename
                    dateMSG = datetime.datetime.strptime(fileDate, "%Y-%m-%dT%H:%M:%S.%fZ")
                    modTime = time.mktime(dateMSG.timetuple())
                    os.utime(fileLocation, (modTime, modTime))
                except Exception as e:
                    myErrorList.append("def process_Files can't change date modified for file: " + filename)
                filelist.append(filename + "###" + filesize)
        except Exception as e:
            print(f"----- ERROR:  {e}")
            myErrorList.append("def process_Files download failed for file: " + filename)
        print(".", end='', flush=True) # Progress indicator
    return filelist


# ----------------------------------------------------------------------------------------
# FUNCTION download member avatars (user images). Will retry failed downloads max. 3 times.
def download_avatars(avatardictionary):  # dictionary:  userId,avatarUrl
    global downloadAvatarCount
    global myErrorList
    # Remove previous error messages (**DJ** does this work when the avatar download fails after 4 tries?)
    myErrorList = [ elem for elem in myErrorList if "def download_avatars download failed" not in elem]
    retryDictionary = dict()
    for key, value in avatardictionary.items():
        filename = "".join(re.findall(r'[A-Za-z0-9]+', key))+".jpg"
        try:
            r = requests.get(value, stream=True)
        except Exception as e:
            myErrorList.append("def download_avatars download failed (attempt #" + str(downloadAvatarCount) + ") for user: " + key + " with URL: " + value + " Error: " + str(e))
            retryDictionary[key] = value # Create temp dictionary for failed avatar downloads - retry later
            print("X", end='', flush=True)  # Progress indicator
            continue
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(myOutputFolder + "/avatars/" + filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print(f"\n**ERROR** download_avatars RESULT: {r.status_code}\n")
    if len(retryDictionary) > 0 and downloadAvatarCount < 4: # Try failed avatar downloads max 3 times
        myErrorList.append("             Avatar download attempt nr. " + str(downloadAvatarCount))
        time.sleep(1)
        downloadAvatarCount += 1
        download_avatars(retryDictionary)


# ----------------------------------------------------------------------------------------
# FUNCTION download member details (that include the member avatar URL)
#          only called when userAvatar = 'download' or 'link'
def get_persondetails(mytoken, personlist):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    personlist = str(personlist)[2:-2].replace("', '",",")
    payload = {'id': personlist}
    resultjsonmessages = list()
    while True:
        try:
            result = requests.get('https://webexapis.com/v1/people', headers=headers, params=payload)
            if result.status_code != 200 and result.status_code != 429:
                print(f"     ** ERROR ** def get_persondetails. result.status_code: {result.status_code}\n        headers: {headers}\n        personlist: >>{personlist.strip()}<<\n        result.text: {result.text}")
            resultjsonmessages = resultjsonmessages + result.json()["items"]
            break
        except requests.exceptions.RequestException as e:
            print(e)
            print(f"\n\n get_persondetails Exception e: {e}\n\n")
            if "e.status_code" == "429":
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True) # Progress indicator
            else:
                break
    return resultjsonmessages


# ----------------------------------------------------------------------------------------
# FUNCTION download ALL SPACES - when you call this script with a parameter, it will
#          search all of your spaces and return spaces that match your search string
def get_searchspaces(mytoken, searchstring):
    max_spaces_to_retrieve = 500 # _per_ API call
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'max': max_spaces_to_retrieve}
    search_result_group = dict()
    search_result_direct = dict()
    resultjson = list()
    print(" ", end='', flush=True) # Progress indicator
    while True:
        try:
            print(".", end='', flush=True) # Progress indicator
            result = requests.get('https://webexapis.com/v1/rooms', headers=headers, params=payload)
            if result.status_code == 401:  # WRONG ACCESS TOKEN
                print("    -------------------------- ERROR ------------------------")
                print("       Please check your Access Token in the .ini file.")
                print("           Note that your Access Token is only valid for 12 hours.")
                print("           Go here to get a new token:")
                print("           https://developer.webex.com/docs/api/getting-started")
                print("    ------------------------- STOPPED ----------------------- \n\n\n")
                beep(3)
                exit()
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=")+len("cursor="):headerLink.rfind(">")]
                payload = {'max': max_spaces_to_retrieve, 'cursor': myCursor}
                if "items" in result.json():
                    try:
                        resultjson += result.json()["items"]
                    except Exception as e:
                        beep(1)
                        print(" **ERROR** get_searchspaces Link: " + str(e))
                continue
            else:
                try:
                    resultjson += result.json()["items"]
                except Exception as e:
                    beep(1)
                    print(f" **ERROR** get_searchspaces no Link: {e}")
                print(f" Total number of spaces: {len(resultjson)}")
                break
        except requests.exceptions.RequestException as e: # A serious problem, like an SSLError or InvalidURL
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
            else:
                break
    for spaces in resultjson:
        try:
            if searchstring.lower() in spaces['title'].lower():
                if spaces['type'] == "group":
                    search_result_group[spaces['id']] = spaces['title']
                elif spaces['type'] == "direct":
                    search_result_direct[spaces['id']] = spaces['title']
        except:
            continue
    return search_result_group,search_result_direct


# ----------------------------------------------------------------------------------------
# FUNCTION that creates a table with the message order (needed for threaded messages)
#
def create_threading_order_table(WebexMessages):
    msgOrderTable = dict()
    msgOrderIndex = 1.000
    for msg in WebexMessages:
        if 'parentId' not in msg:  # NOT a threaded message
            msgOrderTable[("%.3f" % msgOrderIndex)] = msg['id']
            msgOrderIndex = msgOrderIndex + 1.000
        else:   # THREADED MESSAGE!
            # 1 get msgOrderIndex for parent ID in msgOrderTable.
            try:
                newOrderIndex = float(list(msgOrderTable.keys())[list(msgOrderTable.values()).index(msg['parentId'])])
            except:
                continue  # message belongs to thread outside of the current message scope
            # 2 check if nr from parentid + 0.001 exists
            while True:
                if ("%.3f" % newOrderIndex) in msgOrderTable:
                    newOrderIndex = float("%.3f" % (newOrderIndex + 0.001))
                    continue
                else:
                    msgOrderTable[str(newOrderIndex)] = msg['id']
                    break
        # **DJ** thought: Should I NOW recreate the new WebexMessages instead of returning the order(table)?
    return msgOrderTable


# ----------------------------------------------------------------------------------------
# FUNCTION that writes data to a file - not used right now
def write_to_file(data,filename):
    with open("./" + filename, 'w', encoding='utf-8') as f:
        print(data, file=f)

# ----------------------------------------------------------------------------------------
# FUNCTION that tells you if a message is a card or not. Input: message json
def card_or_not(message_json):
    try:
        if "contentType" in message_json["attachments"][0]:
            return True
    except:
        return False


# ----------------------------------------------------------------------------------------
# FUNCTIONs that help me analyze what takes the most time
performanceReport  = " ______________________________________________________\n"
performanceReport += "   Performance Report - space archive script \n"
performanceReport += " ______________________________________________________"
_start_time = time.time()
def startTimer():
    global _start_time
    _start_time = time.time()
def stopTimer(description):
    t_sec = round(time.time() - _start_time,2)
    global performanceReport
    performanceReport += f"\n {t_sec:7.1f} " + description


# ------------------------------------------------------------------------
#    Start of non-function code !  #lastfunction
#
# ------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# ===== SEARCH SPACES: If parameter provided, use it to search in your spaces, display result and exit
if len(sys.argv) > 1:
    spaceSearchResult_group, spaceSearchResult_direct = get_searchspaces(myToken, ' '.join(sys.argv[1:]))
    print("___________________________ group _______________________\n")
    for key, value in spaceSearchResult_group.items():
        print(f"  {value}\n    id:      {key}")
    print("__________________________ direct _______________________\n")
    for key, value in spaceSearchResult_direct.items():
        print(f"  {value}\n    id:      {key}")
    print("_________________________________________________________\n\n")
    exit()


# =====  GET SPACE NAME ========================================================
#   used for the space name in the header and optionally the output foldername
startTimer()
try:
    roomName = get_roomname(myToken, myRoom)
    print(f" #1 --- Get SPACE NAME: '{roomName}'")
except Exception as e:
    print(" #1 --- get SPACE NAME: **ERROR** getting space name")
    print(f"             Error message: {e}\n\n")
    beep(3)
    exit()
stopTimer("get space name")
# If no outputFileName has been configured: use the space name
if outputFileName == "":
    outputFileName = format_filename(roomName)
myOutputFolder = outputFileName



# =====  GET MESSAGES ==========================================================
startTimer()
print(" #2 --- Get MESSAGES")
try:
    WebexMessages = get_messages(myToken, myRoom, max_messages)
except Exception as e:
    print(" **ERROR** STEP #2: getting Messages")
    print(f"             Error message: {e}\n\n")
    beep(3)
    exit()
stopTimer("get messages")


# ===== CREATE USERLIST ========================================================
#   Collect only userId's of users who wrote a message. For those users we will
#   retrieve details & download/link avatars
startTimer()
uniqueUserIds = list()
for myUser in WebexMessages:
    if myUser['personId'] not in uniqueUserIds:
        uniqueUserIds.append(myUser['personId'])
stopTimer("get unique user ids")



# =====  GET MEMBER NAMES ======================================================
# myMembers used # of space members (stats).
# myMemberList is used to get the displayName of users (msg only show email address - personEmail)
startTimer()
print(" #3 --- Get MEMBER List") # Put ALL members in a dictionary that contains: "email + fullname"
try:
    myMembers = get_memberships(myToken, myRoom, 800)
    for members in myMembers:
        try:
            myMemberList[str(members['personEmail'])] = str(members['personDisplayName'])
        except Exception as e:  # IF there's no personDisplayName, use email
            myMemberList[str(members['personEmail'])] = str(members['personEmail'])
except Exception as e:
    print(" **ERROR** STEP #3: getting Memberlist (email address)")
    print(f"             Error message: {e}")
    beep(1)
stopTimer("get memberlist")



# =====  CREATE FOLDERS FOR ATTACHMENTS & AVATARS ==============================
startTimer()
print(f" #4a--- Create FOLDER for HTML. Download files? {downloadFiles}")
if not os.path.exists(myOutputFolder):
    print(f"          folder does NOT exist: {myOutputFolder}")
else:   # check if folder-01 exists, if yes, check if folder-02 exists, etc.
    folderCounter = 1
    print(f"          folder EXISTS  : {myOutputFolder}")
    print(f"          checking folder: " + myOutputFolder + "-" + "{:02d}".format(folderCounter))
    while os.path.exists(myOutputFolder + "-" + "{:02d}".format(folderCounter)):
        folderCounter += 1
    myOutputFolder += "-" + "{:02d}".format(folderCounter)
print(f"          Output folder  : {myOutputFolder}")
os.makedirs(myOutputFolder)
if userAvatar == "download":
    os.makedirs(myOutputFolder + "/avatars/")
if downloadFiles == "files":
    os.makedirs(myOutputFolder + "/files/")
    os.makedirs(myOutputFolder + "/images/")
if downloadFiles == "images":
    os.makedirs(myOutputFolder + "/images/")
stopTimer("create folders")



# =====  GET MEMBER AVATARS ====================================================
startTimer()
if userAvatar == "link" or userAvatar == "download":
    print(" #4b--- MEMBER Avatars: collect avatar Data (" + str(len(uniqueUserIds)) + ")  ", end='', flush=True)
    userAvatarDict = dict()  # --> userAvatarDict[your@email.com] = "https://webex_message_avatarurl"
    x=0
    y=len(uniqueUserIds)
    if 50 > y:
        chunksize = y
    else:
        chunksize = 50
    if y < 50:
        chunksize = y
    for i in range(x,y,chunksize): # - LOOPING OVER MemberDataList in chunks of xx
        x=i
        person_list = get_persondetails(myToken, uniqueUserIds[x:x+chunksize])
        print(".", end='', flush=True)  # Progress indicator
        for persondetails in person_list:
            try:
                userAvatarDict[persondetails['id']] = persondetails['avatar'].replace("~1600","~80")
            except:
                pass
    print(".", flush=False)
stopTimer("get avatars")

startTimer()
if userAvatar == "link" or userAvatar == "download":
    print(" #4c--- MEMBER Avatars: downloading avatar files for " + str(len(userAvatarDict)) + " members)  ", end='', flush=True)
    if userAvatar == "download":
        download_avatars(userAvatarDict)
stopTimer("download avatars")


# =====  GET MY DETAILS ========================================================
startTimer()
try:
    myOwnDetails = get_me(myToken)
    myEmail = "".join(myOwnDetails['emails'])
    myName = myOwnDetails['displayName']
    myDomain = myEmail.split("@")[1]
    print(f"\n #5 --- Get my details: {myEmail}")
except Exception as e:
    print(f"\n #5 --- Get my details: **ERROR** : {e}")
stopTimer("get my details")


# =====  SET/CREATE VARIABLES ==================================================
tocList = ""
statTotalFiles = 0
statTotalImages = 0
statTotalMessages = len(WebexMessages)
myDomainStats = dict()
statMessageMonth = dict()
previousEmail = ""
previousMonth = ""
previousMsgCreated = ""
UTChourDelta = timeDeltaWithUTC()
TimezoneName = str(time.tzname)



# ====== WRITE JSON data to a FILE =============================================
#   (optional) Write JSON to a FILE to be used as input (not using the Webex Message APIs)
startTimer()
if outputToJson == "yes" or outputToJson == "both" or outputToJson == "json":
    with open(myOutputFolder + "/" + outputFileName + ".json", 'w', encoding='utf-8') as f:
        json.dump(WebexMessages, f)
stopTimer("output to json")



# ======  GENERATE HTML HEADER =================================================
#
print(f" #6 --- Generate HTML header")
htmlheader += f"<div class='cssRoomName'>   {roomName}&nbsp;&nbsp;&nbsp;<br><span style='float:left;margin-top:8px;font-size:10px;color:#fff'> CREATED: <span style='color:yellow'>{currentDate}</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Generated by: <span style='color:yellow'>{myName}</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Message timezone: <span style='color:yellow'>{TimezoneName}</span>&nbsp;&nbsp;&nbsp; version:  {version}&nbsp;&nbsp;&nbsp;<br>Sort old-new: <span style='color:yellow'>" + str(sortOldNew).replace("True", "yes (default)").replace("False", "no") + f"</span> &nbsp;&nbsp; Max messages: <span style='color:yellow'> {maxMessageString} </span>&nbsp;&nbsp; File Download: <span style='color:yellow'>{downloadFiles.upper()}</span> &nbsp;&nbsp; Avatar: <span style='color:yellow'>{userAvatar.upper()}</span></span> </div><br>"



# ====== GENERATE FINAL HTML ===================================================
#  for all messages (and optionally a .txt file with all messages)
#
startTimer()
print(f" #7 --- Generate HTML code for {statTotalMessages} messages" + (" AND downloading all " + downloadFiles if downloadFiles in ['images', 'files'] else ""))
htmldata = ""
textOutput = ""
if outputToText:
    textOutput += f"------------------------------------------------------------\n {roomName}\n------------------------------------------------------------\nCREATED:        {currentDate}\nFile Download:  {downloadFiles.upper()}\nGenerated by:   {myName}\nSort old-new:   " + str(sortOldNew).replace("True", "yes (default)").replace("False", "no") + f"\nMax messages:   {maxMessageString}\nAvatar:         {userAvatar} \nversion:        {version} \nTimezone:           {TimezoneName}"
statTotalMentions = 0

startTimer()
sortedMessages = sorted(WebexMessages, key = lambda i: i['created'],reverse=False)
stopTimer("sort WebexMessages")

startTimer()
# --- Message order table: create
msgOrderTable = create_threading_order_table(sortedMessages)
stopTimer("create threading order table")

# --- Sort Messages: process all msgs defined by the "threading index"-table order
if sortOldNew:
    abc = sorted(msgOrderTable , key = lambda x : (float(x),-int(float(x))))
else:
    abc = sorted(msgOrderTable , key = lambda x : (-int(float(x)),float(x)))

# progress bar:
mycounter = 0
progress_steps = int(statTotalMessages / 21)

# --- PROCESS EVERY MESSAGE ----------------------------------------------------
for index, key in enumerate(abc):
    mycounter +=1
    current_step = mycounter/progress_steps
    if (current_step - int(current_step)) == 0:
        current_step = int(current_step)
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("          [%-20s] %d%%" % ('='*current_step, 5*current_step))
        sys.stdout.flush()
    # find matching message ID in message list
    msg = next(item for item in WebexMessages if item["id"] == msgOrderTable[key])
    try:
        nextitem = float(abc[index+1])
        previousitem = float(abc[index-1])
        currentitem = float(abc[index])
        if previousitem - round(previousitem) == 0 and currentitem - round(currentitem) > 0:
            # START of threaded message!
            threadstart = True
        else:
            threadstart = False
        if currentitem - round(currentitem) > 0:
            threaded_message = True
        else:
            threaded_message = False
    except:
        threadstart = False
        threaded_message = False

    # --- continue processing messages
    if len(msg) < 5:
        continue        # message empty
    data_text = ""
    # --- if msg was updated: add 'Edited' in date
    if "updated" in msg:
        data_msg_was_edited = True
        data_created = convertDate(str(msg['created']),UTChourDelta) + "  Edited"
    else:
        data_msg_was_edited = False
        data_created = convertDate(str(msg['created']),UTChourDelta)
    # --- HTML in message? Deal with markdown
    if "html" in msg:
        msg['text'] = ""
        # --- Check if there are Markdown hyperlinks [linktext](www.cisco.com) as these look very different
        if "sparkBase.clickEventHandler(event)" in str(msg['html']):
            data_text = convertMarkdownURL(str(msg['html']),1)
            data_text = convertMarkdownURL(data_text,2)
        else:
            data_text = convertURL(str(msg['html']))
            if "onClick" in msg['html']:
                print(data_text)
    elif 'text' in msg:
        data_text = convertURL(str(msg['text']))
        # --- Replace script in 'text' message (it stops HTML generation) - 0.21
        data_text = data_text.replace("<script","<pre>&lt;")
        if "<code>" in data_text:
            if "</code>" not in data_text:
                data_text += "</code>"
    if data_text == "" and 'files' not in msg and 'mentionedPeople' not in msg:
        # empty text without mentions or attached images/files: SKIP
        continue
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
    if messageMonth != previousMonth and not threaded_message:
        htmldata += f"<div class='cssNewMonth' id='{statMessageMonthKey}'>   {messageYear}    <span style='color:#C3C4C7'>" + \
            messageMonth + "</span></div>"
        if outputToText:  # for .txt output
            textOutput += f"\n\n---------- {messageYear}    {messageMonth} ------------------------------\n\n"
    # ====== if PREVIOUS email equals current email, then skip header
    if threaded_message: # ___________________________________ start thread ______________________________
        htmldata += "<div class='css_message_thread'>"
    else:
        htmldata += "<div class='css_message'>"

    # ====== AVATAR: + msg header: display or not
    if (data_email != previousEmail) or (data_email == previousEmail and timedifference(msg["created"], previousMsgCreated) > 60) or (data_msg_was_edited):
        if userAvatar == "link" and data_userid in userAvatarDict:
            htmldata += f"<img src='{userAvatarDict[data_userid]}' class='avatarCircle'  width='36px' height='36px'/>"
        elif userAvatar == "download" and data_userid in userAvatarDict:
            htmldata += f"<img src='avatars/" + data_userid + ".jpg' class='avatarCircle'  width='36px' height='36px'/>"
        else: # User that may not exist anymore --> use email as name
            if data_name == data_email:
                htmldata += f"<div id='avatarCircle'>{data_name[0:2].upper()}</div>"
            else:
                # show circle with initials instead of avatar
                try:
                    htmldata += "<div id='avatarCircle'>" + data_name.split(" ")[0][0].upper() + data_name.split(" ")[1][0].upper()+ "</div><div class='css_message'>"
                except:  # Sometimes there's no "first/last" name. If one word, take the first 2 characters.
                    htmldata += "<div id='avatarCircle'>" + data_name[0:2].upper() + "</div>"

        msgDomain = data_email.split("@")[1]    # Get message sender domain
        if myDomain == msgDomain:               # If domain <> own domain, use different color
            htmldata += f"<span class='css_email' title='{data_email}'>{data_name}</span>"
        else:
            htmldata += "<span class='css_email' title='" + data_email + "'>" + data_name + "</span>   <span class='css_email_external'>(@" + data_email.split("@")[1] + ")</span>"
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
    if 'mentionedGroups' in msg:
        try:
            statTotalMentions += 1
            for item in msg['mentionedGroups']:
                texttoreplace = "<spark-mention data-object-type=\"groupMention\" data-group-type=\"" + item + "\">"
                data_text = data_text.replace(texttoreplace,"<span style='color:red;display:inline;'>@")
            data_text = data_text.replace("</spark-mention>","</span>")
        except:
            print(" **ERROR** processing mentions, don't worry, I will continue")
    # check if msg is a card. If yes: prefix
    try:
        if "contentType" in msg["attachments"][0]:
            is_card = True
    except:
        is_card = False
    if is_card:
        data_text = "<span class='card_class'>&nbsp;Card&nbsp;</span>&nbsp; " + data_text
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
        myFiles = process_Files(msg['files'],msg['created'])
        # SORT attached files by <files> _then_ <images>
        myFiles.sort(key = lambda x: x.split("###")[0].split(".")[-1] in ['jpg','png','jpeg','bmp','gif','tif'])
        splitFilesImages = ""
        for filename in myFiles:
            # IMAGE POPUP
            filename, filesize = filename.split("###")
            fileextension = os.path.splitext(filename)[1][1:].lower()
            if fileextension in ['png', 'jpg', 'bmp', 'gif', 'tif', 'jpeg'] and (downloadFiles in ["images", "files"]):
                if splitFilesImages == "":
                    # extra return after all attached files are listed
                    htmldata += "<br>"
                    splitFilesImages = "done"
                htmldata += f"<div class='css_created'><img src='images/{filename} ' title='click to zoom' onclick='onClick(this)' class='image-hover-opacity' /><br>{filename}<br><div class='filesize'>{filesize}</div> </div>"
            elif downloadFiles == "files":
                htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'><a href='files/{filename}'>{filename}</a>  ({filesize})"
            else:
                htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'> {filename}   ({filesize})</span>"
            if fileextension in ['png', 'jpg', 'bmp', 'gif', 'tif', 'jpeg']:
                statTotalImages += 1
            else:
                statTotalFiles += 1
            if outputToText:  # for .txt output
                textOutput += f"                           Attachment: {filename} ({filesize})\n"
        htmldata += "</span>"    # filesize or mention /span?
    htmldata += "</div>"    # css_messagetext ?
    htmldata += "</div>"    # css_message or css_message_thread?
    htmldata += "</div>"    #
    previousEmail = data_email
    if not threaded_message:
        previousMonth = messageMonth
    previousMsgCreated = msg['created']
stopTimer("generate HTML messages (" + str(statTotalMessages) + ")" + (" & downloading all " + downloadFiles if downloadFiles in ['images', 'files'] else ""))

# ======  *SORT* DOMAIN USER STATISTICS
startTimer()
myDomainStatsSorted = sorted(
    [(v, k) for k, v in myDomainStats.items()], reverse=True)
myDomainStatsSorted = myDomainStatsSorted[0:10]  # only want the top 10
returntextDomain = ""
returntextMsgMonth = ""
stopTimer("sorting messages")


# ======  TABLE OF CONTENTS
startTimer()
if sortOldNew:
    mytest = sorted(statMessageMonth.items(), reverse=False)
else:
    mytest = sorted(statMessageMonth.items(), reverse=True)
my_yearcounter = 0
tocList = "<table>"
for k, v in mytest:
    # **DJ** below: testing expandable years in TOC <<<<<<<<<<<<<<<
    # indents for all months except January (easy to see new years)
    if "Jan" not in k[10:]:
        tocList += "<tr><td>"
    else:
        tocList += "</table><br><a href='javascript:;' onclick=show('" + k[0:4] + "') style='text-decoration: none;font-weight:bolder;font-size'> <div id='yeararrow" + k[0:4] + "'>⇊</div>  " + k[0:4] + "</span></a><br><br>"
        tocList += "<table id='expand year-" + k[0:4] + "' style='width: 220px;'>"
        tocList += "<tr><td>"
    tocList += "<a href='#" + k + "'>" + k[0:6] + " " + k[10:] + "</a></td>"
    tocList += f"<td><span class='month_msg_count'>{v:,}</span></td></tr>"

# If message sorting is old-to-new, also sort the TOC
messageType = "last"
if not sortOldNew: messageType = "last"
tocList += "<tr><td colspan='2'>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'><a href='#endoffile'>" + messageType + " message</a></span></td></tr>"
tocList += "</table>"


# ======  DOMAIN MESSAGE STATISTICS
returntextDomain += "<table id='mytoc' style='width: 220px;'>"
for domain in myDomainStatsSorted:
    returntextDomain += f"<tr><td>{domain[1]}</td><td style='text-align:right;'>{domain[0]:,}</td>"
returntextDomain += "</table>"


# ======  MESSAGE & FILE STATISTICS
tocStats = "<table id='mytoc' style='width: 250px;'>"
tocStats += f"<tr><td># of messages: </td><td style='text-align:right;'> {statTotalMessages:,} </td></tr>"
tocStats += f"<tr><td> # images: </td><td style='text-align:right;'> {statTotalImages:,} </td></tr>"
tocStats += f"<tr><td> # files: </td><td style='text-align:right;'> {statTotalFiles:,} </td></tr>"
tocStats += f"<tr><td># mentions: </td><td style='text-align:right;'> {statTotalMentions:,} </td></tr>"
tocStats += f"<tr><td># total members: </td><td style='text-align:right;'> {len(myMembers):,} </td></tr>"
tocStats += f"<tr><td># active members: <br>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'>(in this archive)</span> </td><td style='text-align:right;'> {len(uniqueUserIds):,} </td></tr>"
if statTotalMessages > maxTotalMessages -10:
    tocStats += f"<tr><td colspan='2'><br><span style='color:grey;font-size:10px;'>space contains more than  {statTotalMessages:,} messages</span></td></tr>"
tocStats += "</table>"
if outputToText:  # for .txt output
    textOutput += f"\n\n\n STATISTICS \n--------------------------\n # of messages : {statTotalMessages:,}\n # of images   : {statTotalImages:,}\n # of files    : {statTotalFiles:,}\n # of mentions : {statTotalMentions:,}\n\n\n"

# ======  HEADER
newtocList = "<table class='myheader' id='myheader'> <tr>"
newtocList += "<td> <strong>Index</strong><br>" + tocList + " </td>"
newtocList += "<td> <strong>Numbers</strong><br>" + tocStats + " </td>"
newtocList += "<td> <strong>Top-10 user domains</strong><br>" + returntextDomain + " </td>"
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
print("\n #8 --- Finalizing HTML")
htmldata = htmlheader + newtocList + htmldata + htmlfooter + imagepopuphtml + "</body></html>"
stopTimer("generate ToC, statistics, header and footer")


# ======  WRITE to HTML FILE
startTimer()
with open(myOutputFolder + "/" + outputFileName + ".html", 'w', encoding='utf-8') as f:
    print(htmldata, file=f)
stopTimer("write html to file")

# ======  WRITE to TEXT FILE
if outputToText:
    with open(myOutputFolder + "/" + outputFileName + ".txt", 'w', encoding='utf-8') as f:
        print(textOutput, file=f)


if printPerformanceReport:
    msg_time = int(performanceReport.split("order table")[1].split(" generate HTML")[0].lstrip().split(".")[0])
    if msg_time == 0:
        msg_time = 1
    msg_nr   = int(performanceReport.split(" (")[1].split(")")[0])
    msg_statsline = performanceReport.split("order table")[1].split(")")[0].lstrip() + ")"
    msg_per_sec = msg_nr/msg_time
    msg_statsline_new = msg_statsline.replace(")",f" msg, {msg_per_sec:.0f} msg/sec)")
    performanceReport = performanceReport.replace(msg_statsline,msg_statsline_new)
    print(f"{performanceReport}\n\n")


# ======  PRINT ERROR LIST
if len(myErrorList) > 0 and printErrorList:
    print("\n    -------------------- Error Messages ---------------------")
    for myerrors in myErrorList:
        print(f" > {myerrors}")

print(" _______________________ ready ________________________\n\n")
beep(1)

# ------------------------------- end of code -------------------------------
