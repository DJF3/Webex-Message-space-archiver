# -*- coding: utf-8 -*-
"""Webex Message Space Archive Script.
Creates a single HTML file with the messages of a Webex Message space
Info/Requirements/release-notes: https://github.com/DJF3/Webex-Message-space-archiver
Copyright (c) 2021 Cisco and/or its affiliates.
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
import datetime
import calendar  # for DST support
import re
import time
import sys
import os
import shutil  # for file-download with requests
import math    # for converting bytes to KB/MB/GB
import string
from pathlib import Path
import configparser
try:
    assert sys.version_info[0:2] >= (3, 9)
except:
    print("\n\n **ERROR** Minimum Python version is 3.9. Please visit this site to\n           install a newer Python version: https://www.python.org/downloads/\n           Or in the code, remove line 33 'exit()' to continue with an untested Python version.\n\n")
    exit()
try:
    import requests
except ImportError:
    print("\n\n **ERROR** Missing library 'requests'. Please visit the following site to\n           install 'requests': http://docs.python-requests.org/en/master/user/install/ \n\n")
    exit()


#--------- DO NOT CHANGE ANYTHING BELOW ---------
__author__ = "Dirk-Jan Uittenbogaard"
__email__ = "duittenb@cisco.com"
__version__ = "0.30"
__copyright__ = "Copyright (c) 2022 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
sleepTime = 3
version = __version__
printPerformanceReport = False
printErrorList = True
max_messages = 500
currentDate = datetime.datetime.now().strftime("%x %X")
configFile = "webexspacearchive-config.ini"
myMemberList = dict()
myErrorList = list()
downloadAvatarCount = 1
originalConfigFile = configFile
myRoom = ""
mySearch = ""
# below --> ini maxtotalmessages dateformat. Use %d,%m, %y and %Y, change the order / add slashes
#           DON'T use dashes in the date format, only between 2 dates: WRONG: %d-%m-%Y
#              correct examples: %Y/%m/%d, %y%m%d, %d%m%Y
maxmsg_format = "%d%m%Y"


def beep(count):  # PLAY SOUND (for errors)
    for x in range(0, count):
        print(chr(7), end="", flush=True)
    return


print(f"\n\n\n========================= START ========================={version}")
# First check command line arguments
cl_args = ' '.join(sys.argv[1:]).strip()
cl_count = len(sys.argv) - 1
#___ parameter: nothing - default config file
#  = 0 ___
if cl_count == 0:
    print(f"    Using default config file: {configFile}")
#  = 1 ___
#___ parameter: space ID
if cl_count == 1 and "Y2lzY" in cl_args:
    myRoom = cl_args
    print(f"    Alternate Space ID   : {myRoom}")
#___ parameter: config_file.ini
elif cl_count == 1 and ".ini" in cl_args:
    configFile = cl_args
    print(f"    Alternate config file: {configFile}")
#___ parameter: space name search argument
elif cl_count == 1:
    mySearch = cl_args
    print(f"    Searching for space containing '{mySearch}'")
#  > 1 ___
#___ parameter: Space ID and INI (in no particular order)
if cl_count > 1 and ".ini" in cl_args:
    if ".ini" in sys.argv[1]:
        configFile = sys.argv[1].strip()
        myRoom = sys.argv[2].strip()
    elif ".ini" in sys.argv[2]:
        configFile = sys.argv[2].strip()
        myRoom = sys.argv[1].strip()
    print(f"    Alternate config file: {configFile}")
    print(f"    Alternate Space ID   : {myRoom}")
elif cl_count > 1:
    mySearch = cl_args
    print(f"    Searching for space containing '{cl_args}'")


config = configparser.ConfigParser(allow_no_value=True)
# ----------- CONFIG FILE: check if config file exists and if the mandatory settings entries are present.
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
        # Webex token in environment variable 'WEBEX_ARCHIVE_TOKEN' or in the .ini file.
        if "WEBEX_ARCHIVE_TOKEN" in os.environ:
            myToken = os.environ['WEBEX_ARCHIVE_TOKEN']
        else:
            myToken = config['Archive Settings']['mytoken']
        if myRoom == "":  # No space id provided as command line parameter
            if config.has_option('Archive Settings', 'myroom'):  # Added to deal with old naming in .ini files
                myRoom = config['Archive Settings']['myroom']
            if config.has_option('Archive Settings', 'myspaceid'):  # Replacing the old 'myroom' setting
                myRoom = config['Archive Settings']['myspaceid']
        outputFileName = config['Archive Settings']['outputfilename']
        maxTotalMessages = config['Archive Settings']['maxtotalmessages']
        if maxTotalMessages:
            if 'd' in maxTotalMessages:  # Example: maxTotalMessages = 60d = 60 days.
                msgMaxAge = int(maxTotalMessages.replace("d", ""))
                maxTotalMessages = 9999999
                msgMinAge = 0
                # Archive msgs between 2 dates.
            elif '-' in maxTotalMessages:  # Example: maxTotalMessages = 18042021-30102021 (ddmmyyyy-ddmmyyyy)
                msgMaxAge = maxTotalMessages.split('-')[0]
                msgMinAge = maxTotalMessages.split('-')[1]
                if len(msgMinAge) == 0:
                    msgMinAge = datetime.datetime.today().strftime(maxmsg_format)
                for my_date in [msgMaxAge, msgMinAge]:  # check the provided date format
                    try:
                        test_date = my_date[7]  # dummy variable: if the date has less than 8 characters it will generate an error
                        datetime.datetime.strptime(my_date, maxmsg_format).date()
                    except:
                        date_fmt = maxmsg_format.replace("%d", "dd").replace("%b", "mmm").replace("%m", "mm").replace("%y", "yy").replace("%Y", "yyyy")
                        print(f" ** ERROR reading the from or to date: '{my_date}'")
                        print(f"          use this exact format: {date_fmt}-{date_fmt} or {date_fmt}- \n\n")
                        exit()
                msgMaxAge = (datetime.datetime.today() - datetime.datetime.strptime(msgMaxAge, maxmsg_format)).days
                msgMinAge = (datetime.datetime.today() - datetime.datetime.strptime(msgMinAge, maxmsg_format)).days
                if msgMaxAge <= msgMinAge:
                    print(f" ** ERROR end date must be after the start date")
                    print(f"          use this exact format: ddmmyyyy-ddmmyyyy or ddmmyyyy- \n\n")
                    exit()
                maxTotalMessages = 999999
            else:
                maxTotalMessages = int(maxTotalMessages)
                msgMaxAge = 0
                msgMinAge = 0
        else:
            maxTotalMessages = 1000
            msgMaxAge = 0
            msgMinAge = 0
        userAvatar = config['Archive Settings']['useravatar']
        outputToJson = config['Archive Settings']['outputjson']
        if config.has_option('Archive Settings', 'dst_start') and config.has_option('Archive Settings', 'dst_stop'):
            dst_start = config['Archive Settings']['dst_start']
            dst_stop = config['Archive Settings']['dst_stop']
        else:
            print(f" ** config entries 'dst_start' and 'dst_stop' not in config file, please rename config.ini and run script to generate a new ini with the latest enhancements. Then update the new .ini file with your settings")
            dst_stop = ""
            dst_start = ""
        if config.has_option('Archive Settings', 'blurring'):
            blurring = config['Archive Settings']['blurring']
        else:
            print(f" ** config entries 'blurring' not in config file, please rename config.ini and run script to generate a new ini with the latest enhancements. Then update the new .ini file with your settings.\nFor now I will turn off blurring.")
            blurring = ""
    except Exception as e:  # Error: keys missing from .ini file
        print(f" **ERROR** reading webexspacearchive-config.ini file settings.\n    ERROR: {e}")
        print("    Check if your .ini file contains the following keys: \n        download, sortoldnew, mytoken, myspaceid, outputfilename, useravatar, maxtotalmessages, outputjson")
        print("    Rename your .ini file, re-run this script (generating correct file)\n    and put your settings in the new .ini file")
        print(" ---------------------------------------\n\n")
        beep(3)
        exit()
elif os.path.isfile("./" + configFile.replace("webexspacearchive-config", "webexteamsarchive-config")):
    print(f" **ERROR** OLD config filename found!\n   RENAME 'webexteamsarchive-config.ini' to 'webexspacearchive-config.ini' and retry \n\n")
    beep(3)
    exit()

else:
    # ----------- CONFIG FILE: CREATE new config file because it does not exist
    try:
        config = configparser.ConfigParser(allow_no_value=True)
        config.optionxform = str
        config.add_section('Archive Settings')
        config.set('Archive Settings', '; Your Cisco Webex developer token (NOTE: tokens are valid for 12 hours!)')
        config.set('Archive Settings', ';      if empty, create an environment variable "WEBEX_ARCHIVE_TOKEN" with your token.')
        config.set('Archive Settings', 'mytoken', '__YOUR_TOKEN_HERE__')
        config.set('Archive Settings', ';')
        config.set('Archive Settings', '; Space ID: Enter your token above and run this script followed by a search argument')
        config.set('Archive Settings', ';     "archivescript.py searchstring" - returns lists of spaces matching "searchstring"')
        config.set('Archive Settings', ';     OR: go to https://developer.webex.com/docs/api/v1/rooms/list-rooms')
        config.set('Archive Settings', ';         "login, API reference, rooms, list all rooms", set "max" to 900 and run ')
        config.set('Archive Settings', 'myspaceid', '__YOUR_SPACE_ID_HERE__')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; ')
        config.set('Archive Settings', '; Download:  "no"      : (default) only show text "attached_file"')
        config.set('Archive Settings', ';            "info"    : file details (name & size = slower)')
        config.set('Archive Settings', ';            "images"  : download images only')
        config.set('Archive Settings', ';            "files"   : download files & images')
        config.set('Archive Settings', ';     First try the script with downloadFiles set to "no".')
        config.set('Archive Settings', ';     Downloading many files can take more time')
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
        config.set('Archive Settings', ';               -    01052021-11062021 = msgs between 1 May and 11 June (ddmmyyyy-ddmmyyyy)')
        config.set('Archive Settings', ';                 or 01052021-         = msg after May 1st -> keep the "-"!')
        config.set('Archive Settings', ';               - empty (default): last 1000 messages')
        config.set('Archive Settings', 'maxTotalMessages', '1000')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', ';    ')
        config.set('Archive Settings', '; Output filename: Name of the generated HTML file. EMPTY: use the spacename')
        config.set('Archive Settings', ';      (downloadFiles enabled? Attachment foldername: same as spacename)')
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
        config.set('Archive Settings', '; Manually configure Daylight Savings Time (summertime) start/stop dates')
        config.set('Archive Settings', '; __EMPTY:   (default) will use system information')
        config.set('Archive Settings', '; __usa:     dst_start: second week (2) sunday (7) of march (3)   --> 2,7,3')
        config.set('Archive Settings', ';            dst_stop: first week (1) sunday (7) of november (11) --> 1,7,11')
        config.set('Archive Settings', '; __EUROPE:  dst_start: last week (L) sunday (7) of March (3)     --> L,7,3')
        config.set('Archive Settings', ';            dst_stop: last week (L) sunday (7) of October (10)   --> L,7,10')
        config.set('Archive Settings', ';      WEEK_NR:1-4 or L (last), DAY_NR:1-7, MONTH:1-12')
        config.set('Archive Settings', ';   or empty  = only wintertime (of your current timezone)')
        config.set('Archive Settings', ';dst_start = L, 7, 3')
        config.set('Archive Settings', ';dst_stop  = L, 7, 10')
        config.set('Archive Settings', 'dst_start', '')
        config.set('Archive Settings', 'dst_stop', '')
        config.set('Archive Settings', ';       ')
        config.set('Archive Settings', ';       ')
        config.set('Archive Settings', '; Configure if you want the generated HTML file to have names blurred. You can still copy them but they appear blurred.')
        config.set('Archive Settings', ';   no / empty  = (default) no blurring')
        config.set('Archive Settings', ';   yes = blurring enabled')
        config.set('Archive Settings', 'blurring', '')
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
if downloadFiles not in ['no', 'info', 'images', 'files', 'image', 'file']:
    goExitError += "\n   **ERROR** the 'download' setting must be: 'no', 'images' or 'files'"
if not myToken or len(myToken) < 55:
    goExitError += "\n   **ERROR** your token is not set or not long enough. You can also\n     create an environment variable \"WEBEX_ARCHIVE_TOKEN\" with your token."
if len(myRoom) < 70 and mySearch == "":
    goExitError += "\n   **ERROR** your space ID is not set or not long enough\n    RUN this script with a search parameter (space name) to find your space ID"
if not outputFileName or len(outputFileName) < 2:
    outputFileName = ""
if ("\\" in r"%r" % outputFileName) or ("/" in r"%r" % outputFileName):
    goExitError += f"\n   **ERROR** the 'outputFileName' should not contain folders (slashes)\n     outputfilename : {outputFileName}\n    Change the 'outputFileName' to ONLY contain a filename."
if userAvatar not in ['no', 'link', 'download']:
    goExitError += "\n   **ERROR** the 'useravatar' setting must be: 'no', 'link' or 'download'"
if outputToJson not in ['yes', 'no', 'both', 'txt', 'json']:
    outputToJson = "no"
if outputToJson in ['txt', 'yes', 'both']:
    outputToText = True
else:
    outputToText = False
if blurring == "yes":
    blurring = "_blur"
else:
    blurring = ""
if dst_start != "":  # converting dst_start/stop string to list
    try:
        dst_start = dst_start.split(",")
        dst_stop = dst_stop.split(",")
    except Exception as e:
        goExitError += "\n   **ERROR** the 'dst_start' or 'dst_stop' format is incorrect."
if mySearch == "":  # NOT searching for space name
    if msgMaxAge == 0:
        maxMessageString = str(maxTotalMessages)
    elif msgMaxAge > 0 and msgMinAge == 0:
        maxMessageString = f"{msgMaxAge} days"
    else:
        maxMessageString = f"between {msgMinAge}-{msgMaxAge} days "
    dst_string = "no"  # Only for script GUI, to show that DST is configured or not
    if dst_start != "":
        dst_string = "yes"
    blur_msg = ""
    if blurring != "":
        blur_msg = "Blur: yes"
    print(f"    download:{downloadFiles}  Max-msg:{maxMessageString}  Avatars:{userAvatar}  DST:{dst_string} {blur_msg}")
if len(goExitError) > 76:   # length goExitError = 66. If error: it is > 76 characters --> print errors + exit
    print(f"{goExitError}\n ------------------------------------------------------------------\n\n")
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
    if (document.getElementById(myElement).style.display == 'none') {
        document.getElementById(myElement).style.display = 'block';
        document.getElementById('yeararrow' + yearnr).innerHTML = '▼';
    } else {
        document.getElementById(myElement).style.display = 'none';
        document.getElementById('yeararrow' + yearnr).innerHTML = '▶';
    }
}
function show_showall() {
    for (let step = 2010; step < 2040; step++) {
        let element = 'expand year-' + step;
        if(document.body.contains(document.getElementById(element))){
            document.getElementById(element).style.display = 'block';
            document.getElementById('yeararrow' + step).innerHTML = '▼';
        }
    }
}
function show_hideall() {
    for (let step = 2010; step < 2040; step++) {
        let element = 'expand year-' + step;
        if(document.body.contains(document.getElementById(element))){
            document.getElementById(element).style.display = 'none';
            document.getElementById('yeararrow' + step).innerHTML = '▶';
        }
    }
}
</script>
<style type='text/css'>
body { font-family: 'HelveticaNeue-Light', 'Helvetica Neue Light', 'Helvetica', 'Arial', 'Lucida Grande', 'sans-serif';}
div[class^="expand"], div[class*=" year-"] {
    display:block;
}
.cssRoomName {
    height: 100%;
    background-color: #029EDB;
    font-size: 34px;
    color: #fff;
    padding-left: 30px;
    align-items: center;
    padding-top: 8px;
    min-width: 1000px;
    display: inline-block;
    width: 100%;
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
.css_email_blur {  /* BLURRING */
    font-size: 14px;
    color: rgb(133, 134, 136);
    padding-left: 6px;
    padding-top: 6px;
    filter: blur(3px);
    -webkit-filter: blur(3px);
}
/*  ------ NAME  ------ */
.css_email_external {
    font-size: 14px;
    color: #F0A30B;
    padding-left: 6px;
    padding-top: 6px;
}
.css_email_external_blur {   /* BLURRING */
    font-size: 14px;
    color: #F0A30B;
    padding-left: 6px;
    padding-top: 6px;
    filter: blur(3px);
    -webkit-filter: blur(3px);
}
.myblur {                   /* BLURRING */
    filter: blur(3px);
    -webkit-filter: blur(3px);
}
/*  ------ @Mentions  ------ */
.atmention {
    color: red;
    display: inline;
}
.atmention_blur {               /* BLURRING */
    color: red;
    display: inline;
    filter: blur(3px);
    -webkit-filter: blur(3px);
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
  /* wrap shared code so it can be printed */
  pre, code {
    white-space: pre-wrap !important;
    word-break: break-word;
  }
}
#myBtn:hover {
  background-color: #555;
}
.card_class {
    background-color: lightgrey;
    font-size: 11px;
    color: black;
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
# FUNCTION convert date to format displayed with each message. Used in HTML generation.
#          This function checks the timezone difference between you and UTC and updates the
#          message date/time so the actual times for your timezone are displayed.
#          It also checks for DST
def convertDate(inputdate, returnFormat):
    FMT = "%Y-%m-%dT%H:%M:%S.%fZ"  # UTC format stored in Webex cloud
    inputdate = datetime.datetime.strptime(inputdate, FMT)
    dstinfo = time.localtime(int(inputdate.timestamp()))
    date_is_dst = bool(dstinfo.tm_isdst)
    if date_is_dst:
        offset = utc_offset['summer']
    else:
        offset = utc_offset['winter']
    # ---------- NO DST CONFIGURED --------------------
    if dst_start == "":
        dateMSGnew = inputdate + datetime.timedelta(hours=offset, minutes=0)
    else:  # ---------- DST CONFIGURED --------------------
        if inputdate > dst_table[inputdate.year][0] and inputdate < dst_table[inputdate.year][1]:  # = SUMMER
            dateMSGnew = inputdate + datetime.timedelta(hours=utc_offset['summer'], minutes=0)
        else:
            dateMSGnew = inputdate + datetime.timedelta(hours=utc_offset['winter'], minutes=0)  # = WINTER
    return datetime.datetime.strftime(dateMSGnew, returnFormat)


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
    tdelta = datetime.datetime.today() - datetime.datetime.strptime(msgdate, FMT)
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
            matchDict[matchNum] = [match.start(), match.end()]
        for i in sorted(matchDict.keys(), reverse=True):
            msgtext = msgtext[0:matchDict[i][0]] + " target='_blank'" + msgtext[matchDict[i][1]:]
    except Exception as e:
        test = msgtext
        print(f" **ERROR** replacing markdown URL's in text: {msgtext}")
    return msgtext


# ----------------------------------------------------------------------------------------
# FUNCTION that retrieves a list of Space members (displayName + email address)
def get_memberships(mytoken, myroom, maxmembers):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'roomId': myroom, 'max': 400}
    resultjson = list()
    while True:
        try:
            result = requests.get('https://webexapis.com/v1/memberships', headers=headers, params=payload)
            if "Link" in result.headers:  # there's MORE members
                headerLink = result.headers["Link"]
                myCursor = headerLink[headerLink.find("cursor=") + len("cursor="):headerLink.rfind(">")]
                payload = {'roomId': myroom, 'max': maxmembers, 'cursor': myCursor}
                resultjson += result.json()["items"]
                continue
            else:
                resultjson += result.json()["items"]
                print(f"          Number of space members: {len(resultjson)}")
                break
        except requests.exceptions.RequestException as e:  # For problems like SSLError/InvalidURL
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True)  # Progress indicator
            else:
                print(f" *** ERROR *** getting space members. Error message: {result.status_code}\n {e}")
                break
        except Exception as e:
            print(f" *** ERROR *** getting space members. Error message: {e}")
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
                print(f" ** ERROR ** Problem retrieving specific messages. Try to lower\n                the max_messages variable in the .py and .ini file until it works\nERROR msg: {result.text}\nERROR code: {result.status_code}")
                beep(3)
                exit()
            messageCount += len(result.json()["items"])
            progress_counter += 1
            sys.stdout.write('\r')
            sys.stdout.write("          %d %s " % (messageCount, '*' * progress_counter))
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
                        maxTotalMessages = next((index for (index, d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                        break
                myBeforeMessage = result.headers.get('Link').split("beforeMessage=")[1].split(">")[0]
                payload = {'roomId': myroom, 'max': myMaxMessages, 'beforeMessage': myBeforeMessage}
                continue
            else:
                resultjsonmessages = resultjsonmessages + result.json()["items"]
                if msgMaxAge != 0:
                    msgAge = timedifferencedays(result.json()["items"][-1]["created"])
                    lastMsgLocation = next((index for (index, d) in enumerate(resultjsonmessages) if timedifferencedays(d["created"]) > msgMaxAge), 99999)
                    maxTotalMessages = lastMsgLocation
                print(f" FINISHED total messages: {messageCount}")
                if "Link" in result.headers:   # There ARE more messages but the maxTotalMessages has been reached
                    print(f"          Reached configured maximum # messages ({maxTotalMessages})")
                break
        except requests.exceptions.RequestException as e:  # A serious problem, like an SSLError or InvalidURL
            print(f"          EXCEPT status_code: {e.status_code}")
            print(f"          EXCEPT text: {e.text}")
            print(f"          EXCEPT headers: {e.headers}")
            if e.status_code == 429:
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True)  # Progress indicator
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
    return filename.strip()


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
        elif result.status_code == 404:  # and "resource could not be found" in str(result.text) --> WRONG SPACE ID
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
    try:
        header = {'Authorization': "Bearer " + mytoken, 'content-type': 'application/json; charset=utf-8'}
        result = requests.get(url='https://webexapis.com/v1/people/me', headers=header)
    except Exception as e:
        print(f"       **ERROR** get_me API call status_code: {result.status_code}\n status_text: {result.text}\n Exception {e}\n\n")
        beep(3)
        exit()
    return result.json()


# ----------------------------------------------------------------------------------------
# FUNCTION to convert file-size "bytes" to readable format (KB,MB,GB)
def convert_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(int(size_bytes), 1024)))
    p = math.pow(1024, i)
    # Below: if B/KB/MB --> don't show decimals. Otherwise show 2 decimals
    if i > 2:
        s = round(int(size_bytes) / p, 2)
        s = f"{s:.2f}"
    else:
        s = round(int(size_bytes) / p, 0)
        s = f"{s:.0f}"
    return f"{s} {size_name[i]}"


# ----------------------------------------------------------------------------------------
# FUNCTION to download message images & files (if enabled)
def process_Files(fileData, fileDate):
    global myErrorList
    filelist = list()
    for url in fileData:
        headers = {"Authorization": f"Bearer {myToken}", "Accept-Encoding": ""}
        r = requests.head(url, headers=headers)
        if r.status_code == 404:  # Item must have been deleted since url was retrieved
            continue
        try:
            filename = str(r.headers['Content-Disposition']).split("\"")[1]
            # Files with no name or just spaces: fix so they can still be downloaded:
            if len(filename) < 1 or filename.isspace():
                filename = "unknown-filename"
            if filename == ('+' * (int(len(filename) / len('+')) + 1))[:len(filename)]:
                filename = "unknown-filename"
                beep(1)
                print(f"**process_files** {str(r.headers)}")
        except Exception as e:
            filename = "error-getting-filename"
            myErrorList.append("def process_Files Header 'content-disposition' error for url: " + url)
        filename = format_filename(filename)
        filesize = int(r.headers['Content-Length'])
        fileextension = os.path.splitext(filename)[1][1:].replace("\"", "")
        filenamepart = os.path.splitext(filename)[0]
        if int(r.headers['Content-Length']) <= 0:
            # Not downloading 0 Byte files, only show the filename
            filelist.append(filename + "###" + str(filesize))
            continue
        if downloadFiles not in ['images', 'files', 'image', 'file']:
            # No file downloading --> just get the filename + size
            filelist.append(filename + "###" + str(filesize))
            continue
        if "image" in downloadFiles and fileextension.lower() not in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif']:
            # File is not an image --> just get the filename + size
            filelist.append(filename + "###" + str(filesize))
            continue
        if fileextension.lower() in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif']:
            # File is an image
            subfolder = "/images/"
        else:
            # File is a non-image file
            subfolder = "/files/"
        # CHECK if filename exists, if yes, add "-x" where x is a counter
        if downloadFiles in ['images', 'files', 'image', 'file']:
            if os.path.isfile(myOutputFolder + subfolder + filename):  # File exist? add '-<number>' to the filename.
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
                filelist.append(filename + "###" + str(filesize))
        except Exception as e:
            print(f"----- ERROR:  {e}")
            myErrorList.append("def process_Files download failed for file: " + filename)
        print(".", end='', flush=True)  # Progress indicator
    return filelist


# ----------------------------------------------------------------------------------------
# FUNCTION download member avatars (user images). Will retry failed downloads max. 3 times.
def download_avatars(avatardictionary):  # dictionary:  userId, avatarUrl
    global downloadAvatarCount
    global myErrorList
    # Remove previous avatar error messages
    myErrorList = [elem for elem in myErrorList if "def download_avatars download failed" not in elem]
    retryDictionary = dict()
    for key, value in avatardictionary.items():
        filename = "".join(re.findall(r'[A-Za-z0-9]+', key)) + ".jpg"
        try:
            r = requests.get(value, stream=True)
        except Exception as e:
            myErrorList.append("def download_avatars download failed (attempt #" + str(downloadAvatarCount) + ") for user: " + key + " with URL: " + value + " Error: " + str(e))
            retryDictionary[key] = value  # Create temp dictionary for failed avatar downloads - retry later
            print("X", end='', flush=True)  # Progress indicator
            continue
        if r.status_code == 200:
            r.raw.decode_content = True
            with open(myOutputFolder + "/avatars/" + filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            print(f"\n**ERROR** download_avatars RESULT: {r.status_code}\n")
    if len(retryDictionary) > 0 and downloadAvatarCount < 4:  # Try failed avatar downloads max 3 times
        myErrorList.append("             Avatar download attempt nr. " + str(downloadAvatarCount))
        time.sleep(1)
        downloadAvatarCount += 1
        download_avatars(retryDictionary)


# ----------------------------------------------------------------------------------------
# FUNCTION download member details (that include the member avatar URL)
#          only called when userAvatar = 'download' or 'link'
def get_persondetails(mytoken, personlist):
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    personlist = str(personlist)[2:-2].replace("', '", ",")
    payload = {'id': personlist}
    resultjsonmessages = list()
    while True:
        try:
            result = requests.get('https://webexapis.com/v1/people', headers=headers, params=payload)
            if result.status_code != 200 and result.status_code != 429:
                print(f"     ** ERROR ** def get_persondetails. result.status_code: {result.status_code}\n        headers: {headers}\n        personlist: >>{personlist.strip()}<<\n        result.text: {result.text}")
            else:
                resultjsonmessages = resultjsonmessages + result.json()["items"]
            break
        except requests.exceptions.RequestException as e:
            print(e)
            print(f"\n\n get_persondetails Exception e: {e}\n\n")
            if "e.status_code" == "429":
                print("          Code 429, waiting for : " + str(sleepTime) + " seconds: ", end='', flush=True)
                for x in range(0, sleepTime):
                    time.sleep(1)
                    print(".", end='', flush=True)  # Progress indicator
            else:
                break
    return resultjsonmessages


# ----------------------------------------------------------------------------------------
# FUNCTION download ALL SPACES - when you call this script with a parameter, it will
#          search all of your spaces and return spaces that match your search string
def get_searchspaces(mytoken, searchstring):
    max_spaces_to_retrieve = 500  # PER API call
    headers = {'Authorization': 'Bearer ' + mytoken, 'content-type': 'application/json; charset=utf-8'}
    payload = {'max': max_spaces_to_retrieve}
    search_result_group = dict()
    search_result_direct = dict()
    resultjson = list()
    print(" ", end='', flush=True)  # Progress indicator
    while True:
        try:
            print(".", end='', flush=True)  # Progress indicator
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
                myCursor = headerLink[headerLink.find("cursor=") + len("cursor="):headerLink.rfind(">")]
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
        except requests.exceptions.RequestException as e:  # A serious problem, like an SSLError or InvalidURL
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
    return search_result_group, search_result_direct


# ----------------------------------------------------------------------------------------
# FUNCTION that creates a table with the message order (needed for threaded messages)
#
def create_threading_order_table(WebexMessages):
    msgOrderTable = dict()
    msgOrderIndex = 1.000
    missing_parent_msg = {}
    missing_parent_msglist = list()
    count_hasparent = 0
    count_hasnoparent = 0
    for msg in WebexMessages:
        if 'parentId' not in msg:
            # NOT a threaded message
            count_hasnoparent += 1
            msgAge = timedifferencedays(msg["created"])
            if (msgAge < msgMinAge or msgAge > msgMaxAge) and msgMaxAge != 0:  # check if msg is between min/max msg date
                continue
            else:
                msgOrderTable[(str(float("%.3f" % msgOrderIndex)))] = msg['id']
                msgOrderIndex = msgOrderIndex + 1.000
        else:
            count_hasparent += 1
            # THREADED MESSAGE!
            # If parentId does not exist in msgOrderTable: CREATE PARENT!
            #    note: this also happens when you retrieve 500 msg and the parent happens to be the 501th msg.
            if msg['parentId'] not in msgOrderTable.values():
                missing_parent_msg = {}
                FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
                missing_parent_msg["id"]          = msg['parentId']
                missing_parent_msg["roomId"]      = msg['roomId']
                missing_parent_msg["roomType"]    = msg["roomType"]
                missing_parent_msg["html"]        = "<span style='color: gray;'>User deleted their own message, or msg outside maxtotalmessages scope.</span>"
                missing_parent_msg["personId"]    = "Y2lzY29xxXXxxXXxx00xxXXxx11xxXXxx22xxXXxx33xxXXxx44xxXXxx55xxXXxx66xxXXxx77xxX"
                missing_parent_msg["personEmail"] = "placeholder@user_removed_their_msg.com"
                missing_parent_msg["created"]     = (datetime.datetime.strptime(msg["created"], FMT) - datetime.timedelta(hours=0, minutes=20)).strftime(FMT)
                missing_parent_msglist.append(missing_parent_msg)
                # because the parent is NOT a threaded message, do the same as for a non threaded message (like a parent)
                msgAge = timedifferencedays(missing_parent_msg["created"])
                if (msgAge < msgMinAge or msgAge > msgMaxAge) and msgMaxAge != 0:  # check if msg is between min/max msg date
                    continue
                else:
                    msgOrderTable[(str(float("%.3f" % msgOrderIndex)))] = missing_parent_msg['id']
                    msgOrderIndex = msgOrderIndex + 1.000
                # DJ: NOW the ordertables are available and ready for the "threaded message" (there is a parent for the message)
            # 1 get msgOrderIndex for parent ID in msgOrderTable.
            try:
                newOrderIndex = float(list(msgOrderTable.keys())[list(msgOrderTable.values()).index(msg['parentId'])])
            except Exception as e:
                print(f"\n **ERROR** create_threading_order_table - newOrderIndex. Error message:\n{e}")
                continue  # message belongs to thread outside of the current message scope
            # 2 check if nr from parentid + 0.001 exists
            while True:
                if str(float(("%.3f" % newOrderIndex))) in msgOrderTable:
                    # the above str(float(etc)) fixes issue where max 9 msgs per thread were shown in html and txt 0.22 ojchase!
                    newOrderIndex = float("%.3f" % (newOrderIndex + 0.001))
                    continue
                else:
                    msgOrderTable[str(newOrderIndex)] = msg['id']
                    break
    return msgOrderTable, missing_parent_msglist


# ----------------------------------------------------------------------------------------
# FUNCTION that writes data to a file - not used right now
def write_to_file(data, filename):
    if os.path.exists(filename):
        fileCounter = 1
        f_name = filename.split(".")[0]
        f_extension = filename.split(".")[1]
        filename = f_name + "-" + "{:02d}".format(fileCounter) + "." + f_extension
        while os.path.exists(filename):
            fileCounter += 1
            filename = f_name + "-" + "{:02d}".format(fileCounter) + "." + f_extension
    with open("./" + filename, 'w', encoding='utf-8') as f:
        if filename.split(".")[1] == "json":
            json.dump(data, f)
        else:
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
# FUNCTION ... Based on dst_start/stop config, this returns the exact start/stop dates for a specific year
def find_dayofmonth(myyear, dst_info):
    c = calendar.Calendar(firstweekday=calendar.SUNDAY)
    mymonth = int(dst_info[2])
    monthcal = c.monthdatescalendar(myyear, mymonth)
    myday = int(dst_info[1]) - 1  # position in list = -1 because list starts at 0
    myposition = dst_info[0]
    if myposition == "L":
        try:
            resultday = [day for week in monthcal for day in week if day.weekday() == myday and day.month == mymonth]
            if len(resultday) == 5:
                resultday = resultday[4]
            else:
                resultday = resultday[3]
        except:
            resultday = [day for week in monthcal for day in week if day.weekday() == myday and day.month == mymonth][4]
            print(f">> result day TRY 4th: {resultday}")
    else:
        resultday = [day for week in monthcal for day in week if day.weekday() == myday and day.month == mymonth][int(myposition) - 1]
    my_time = datetime.time(0, 0)
    my_date = resultday
    returndata = datetime.datetime.combine(my_date, my_time)
    return returndata


# ----------------------------------------------------------------------------------------
# FUNCTION get_utc_offset: returns the UTC offset for a given date (in hours)
def get_utc_offset(my_date):
    local_now = my_date.astimezone()
    my_offset_h = local_now.tzinfo.utcoffset(local_now).seconds / 3600  # hours
    if local_now.tzinfo.utcoffset(local_now).days:  # if "days" parameter is present
        my_offset_h = (24 - my_offset_h) * -1
    return my_offset_h


# ----------------------------------------------------------------------------------------
# FUNCTIONs to analyze what takes the most time. Enable by setting printPerformanceReport (top) to true
performanceReport = " ______________________________________________________\n"
performanceReport += "   Performance Report - space archive script \n"
performanceReport += " ______________________________________________________"
start_time = time.time()
def startTimer():
    global start_time
    start_time = time.time()
def stopTimer(description, dl_timer):
    t_sec = round(time.time() - start_time, 2)
    if dl_timer > 0:
        t_sec = t_sec - dl_timer
    global performanceReport
    performanceReport += f"\n {t_sec:7.1f} " + description
# Performance counters for downloading files
dl_timer = time.time()
dl_duration_total = 0
def startTimerFiledownload():
    global dl_timer
    dl_timer = time.time()
def stopTimerFiledownload():
    t_sec = round(time.time() - dl_timer, 2)
    global dl_duration_total
    dl_duration_total += t_sec


# ------------------------------------------------------------------------
#    Start of non-function code !  #lastfunction
#
# ------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# ===== SEARCH SPACES: If parameter provided, use it to search in your spaces, display result and exit
if mySearch != "":
    spaceSearchResult_group, spaceSearchResult_direct = get_searchspaces(myToken, mySearch)
    if len(spaceSearchResult_group.items()) > 0:
        print("___________________________ group _______________________\n")
        for key, value in spaceSearchResult_group.items():
            print(f"  {value}\n    id:      {key}")
    if len(spaceSearchResult_direct.items()) > 0:
        print("__________________________ direct _______________________\n")
        for key, value in spaceSearchResult_direct.items():
            print(f"  {value}\n    id:      {key}")
    if len(spaceSearchResult_group.items()) + len(spaceSearchResult_direct.items()) > 0:
        print("_________________________________________________________\n\n")
    exit()


# =====  CREATE TABLE with DST dates for my LOCAL TIME ==========================
# ___ dst_start empty? don't create dst_table
if dst_start != "":
    dst_table = dict()
    for year in range(2016, datetime.datetime.now().year + 1):
        dst_table[year] = (find_dayofmonth(year, dst_start), find_dayofmonth(year, dst_stop))
#___ DEFINE UTC OFFSET summer AND winter
# No dst_start/stop config? Messages use your current winter and summer time offset to UTC
utc_offset = dict()
utc_offset['winter'] = get_utc_offset(datetime.datetime(2021, 1, 1, 1, 1, 1, 1))  # just a date in the winter
utc_offset['summer'] = get_utc_offset(datetime.datetime(2021, 7, 7, 7, 7, 7, 7))  # just a date in the summer
# Below: dst START date AFTER dst STOP date (Australia): swap summer winter offsets
if dst_start != "":
    if dst_table[2021][0] > dst_table[2021][1]:
        utc_offset['summer'], utc_offset['winter'] = utc_offset['winter'], utc_offset['summer']


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
stopTimer("get space name", 0)
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
if len(WebexMessages) == 0:  # for spaces that have no messages (anymore)
    print(" **ERROR** STEP #2: getting Messages")
    print(f"             No messages found\n\n")
    beep(3)
    exit()
stopTimer("get messages", 0)


# ===== CREATE USERLIST ========================================================
#   Collect only userId's of users who wrote a message. For those users we will
#   retrieve details & download/link avatars
startTimer()
uniqueUserIds = list()
for myUser in WebexMessages:
    if myUser['personId'] not in uniqueUserIds and "xxXXxx" not in myUser['personId']:
        uniqueUserIds.append(myUser['personId'])
stopTimer("get unique user ids", 0)


# =====  GET MEMBER NAMES ======================================================
# myMembers used # of space members (stats).
# myMemberList is used to get the displayName of users (msg only show email address - personEmail)
startTimer()
print(" #3 --- Get MEMBER List")  # Put ALL members in a dictionary that contains: "email + fullname"
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
stopTimer("get memberlist", 0)


# =====  CREATE FOLDERS FOR ATTACHMENTS & AVATARS ==============================
startTimer()
print(f" #4a--- Create FOLDER for HTML. Download files? {downloadFiles}")
if not os.path.exists(myOutputFolder):
    print(f"          folder does NOT exist: {myOutputFolder}")
else:   # check if folder-01 exists, if yes, check if folder-02 exists, etc.
    folderCounter = 1
    print(f"          folder EXISTS  : {myOutputFolder}")
    while os.path.exists(myOutputFolder + "-" + "{:02d}".format(folderCounter)):
        folderCounter += 1
    myOutputFolder += "-" + "{:02d}".format(folderCounter)
print(f"          Output folder  : {myOutputFolder}")
os.makedirs(myOutputFolder)
if userAvatar == "download":
    os.makedirs(myOutputFolder + "/avatars/")
if "file" in downloadFiles:
    os.makedirs(myOutputFolder + "/files/")
    os.makedirs(myOutputFolder + "/images/")
if "image" in downloadFiles:
    os.makedirs(myOutputFolder + "/images/")
stopTimer("create folders", 0)


# =====  GET MEMBER AVATARS ====================================================
startTimer()
if userAvatar == "link" or userAvatar == "download":
    print(" #4b--- MEMBER Avatars: collect avatar Data (" + str(len(uniqueUserIds)) + ")  ", end='', flush=True)
    userAvatarDict = dict()  # --> userAvatarDict[your@email.com] = "https://webex_message_avatarurl"
    x = 0
    y = len(uniqueUserIds)
    if 50 > y:
        chunksize = y
    else:
        chunksize = 50
    if y < 50:
        chunksize = y
    for i in range(x, y, chunksize):  # - LOOPING OVER MemberDataList in chunks of xx
        x = i
        person_list = get_persondetails(myToken, uniqueUserIds[x:x + chunksize])
        print(".", end='', flush=True)  # Progress indicator
        for persondetails in person_list:
            try:
                userAvatarDict[persondetails['id']] = persondetails['avatar'].replace("~1600", "~80")
            except:
                print('', end='')
    print(".", flush=False)
stopTimer("get avatars", 0)

startTimer()
if userAvatar == "link" or userAvatar == "download":
    print(" #4c--- MEMBER Avatars: downloading avatar files for " + str(len(userAvatarDict)) + " members  ")  #, end='', flush=True)
    if userAvatar == "download":
        download_avatars(userAvatarDict)
    # print("")
stopTimer("download avatars", 0)


# =====  GET MY DETAILS ========================================================
startTimer()
try:
    myOwnDetails = get_me(myToken)
    myEmail = "".join(myOwnDetails['emails'])
    myName = myOwnDetails['displayName']
    myDomain = myEmail.split("@")[1]
    print(f" #5 --- Get my details: {myEmail}")
except Exception as e:
    print(f"\n #5 --- Get my details: **ERROR** : {e}\n\n myOwnDetails data retrieved: \n{myOwnDetails}")
stopTimer("get my details", 0)


# =====  SET/CREATE VARIABLES ==================================================
tocList = ""
statTotalFiles = 0
statTotalImages = 0
statTotalFilesSize = 0
statTotalImagesSize = 0
statTotalMessages = len(WebexMessages)
statTotalMentions = 0
myDomainStats = dict()
statMessageMonth = dict()
previousEmail = ""
previousMonth = ""
previousMsgCreated = ""
TimezoneName = str(time.tzname[time.localtime().tm_isdst])


# ======  GENERATE HTML HEADER =================================================
#
print(f" #6 --- Generate HTML header")
configFileInfo = ""
if configFile != originalConfigFile:
    configFileInfo = f"Config file: <span style='color:yellow'>{configFile}</span>"
dst_msg = "NO"
if dst_start != "":
    # below: changing dst_start/stop to string
    dst_msg = (str(dst_start) + "/" + str(dst_stop)).replace(" ", "").replace("[", "").replace("]", "").replace("'", "")
blur_msg = "YES"
if blurring == "":
    blur_msg = "NO"
outputjson_msg = outputToJson.replace("yes", "json/txt").replace("both", "json/txt")
htmlheader += f"<div class='cssRoomName'>   {roomName}&nbsp;&nbsp;&nbsp;<br><span style='float:left;margin-top:8px;padding-bottom:11px;"
htmlheader += f"font-size:10px;color:#fff'> CREATED: <span style='color:yellow'>{currentDate}</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  Generated by: <span "
htmlheader += f"style='color:yellow'>{myName}</span> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;  {configFileInfo}"
htmlheader += f"&nbsp;&nbsp;&nbsp; version:  {version}&nbsp;&nbsp;&nbsp;<br>Sort old-new: <span style='color:yellow'>"
htmlheader += str(sortOldNew).replace("True", "yes (default)").replace("False", "no") + f"</span> &nbsp;&nbsp; Max messages:"
htmlheader += f"<span style='color:yellow'> {maxMessageString} </span>&nbsp;&nbsp; File Download: <span style='color:yellow'>{downloadFiles.upper()}</span>"
htmlheader += f"&nbsp;&nbsp; Avatar: <span style='color:yellow'>{userAvatar.upper()}</span>&nbsp;&nbsp; Message timezone: <span style='color:yellow'>{TimezoneName}</span>"
htmlheader += f"&nbsp;&nbsp; DST configured: <span style='color:yellow'>{dst_msg}</span>"
htmlheader += f"&nbsp;&nbsp; Output: <span style='color:yellow'>{outputjson_msg}</span>"
htmlheader += f"&nbsp;&nbsp; Blurring: <span style='color:yellow'>{blur_msg}</span></span></div><br>"


# ====== GENERATE FINAL HTML ===================================================
#  for all messages (and optionally a .txt file with all messages)
#
startTimer()  # for generating the full HTML file

# ___ first create msg order table
startTimer()
sortedMessages = sorted(WebexMessages, key=lambda i: i['created'], reverse=False)
stopTimer("sort WebexMessages", 0)

startTimer()
# --- Message order table: create
msgOrderTable, missing_parent_msglist = create_threading_order_table(sortedMessages)
if len(missing_parent_msglist) > 0:
    WebexMessages += missing_parent_msglist
    sortedMessages = sorted(WebexMessages, key=lambda i: i['created'], reverse=False)

# --- Sort Messages: process all msgs defined by the "threading index"-table order
if sortOldNew:
    sortedMsgOrderTable = sorted(msgOrderTable, key=lambda x: (float(x), -int(float(x))))
else:
    sortedMsgOrderTable = sorted(msgOrderTable, key=lambda x: (-int(float(x)), float(x)))
stopTimer("create threading order table", 0)

print(f" #7 --- Generate HTML code for {len(sortedMsgOrderTable)} messages" + (" AND downloading all " + downloadFiles if downloadFiles in ['images', 'files', 'image', 'file'] else ""))
htmldata = ""
textOutput = ""
if outputToText:
    textOutput += f"------------------------------------------------------------\n {roomName}\n------------------------------------------------------------\n"
    textOutput += f"CREATED:        {currentDate}\nFile Download:  {downloadFiles.upper()}\nGenerated by:   {myName}\nSort old-new:   "
    textOutput += str(sortOldNew).replace("True", "yes (default)").replace("False", "no") + f"\nMax messages:   {maxMessageString}\nAvatar:"
    textOutput += f"         {userAvatar} \nversion:        {version} \nTimezone:       {TimezoneName}\nDST configured:     "
    if dst_start == "":
        textOutput += "No\n"
    else:
        textOutput += "Yes\n"


# ====== WRITE JSON data to a FILE =============================================
#   (optional) Write JSON to a FILE to be used as input (not using the Webex Message APIs)
startTimer()
if outputToJson == "yes" or outputToJson == "both" or outputToJson == "json":
    with open(myOutputFolder + "/" + outputFileName + ".json", 'w', encoding='utf-8') as f:
        json.dump(WebexMessages, f)
stopTimer("output to json", 0)


# Progress bar:
mycounter = 0
download_stats = ""
progress_steps = int(len(sortedMsgOrderTable) / 20)  # 0.26d don't show total msg downloaded but the actual number of msg
if progress_steps < 1:
    progress_steps = 1  # Fix issue with low number of maxtotalmessages v0.22
# --- PROCESS EVERY MESSAGE ----------------------------------------------------
for index, key in enumerate(sortedMsgOrderTable):
    mycounter += 1
    current_step = mycounter / progress_steps
    if (current_step - int(current_step)) == 0:
        current_step = int(current_step)
        sys.stdout.write('\r')
        # the exact output you're looking for:
        sys.stdout.write("          [%-20s] %d%%" % ('=' * current_step, 5 * current_step))
        sys.stdout.flush()
    # find matching message ID in message list
    msg = next(item for item in WebexMessages if item["id"] == msgOrderTable[key])
    try:
        previousitem = float(sortedMsgOrderTable[index - 1])
        currentitem = float(sortedMsgOrderTable[index])
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
        print("_EMPTYmessage_")
        beep(1)  # troubleshooting thing (to see, eh, hear how many "empty messages" are found)
        continue        # message empty

    data_text = ""
    # --- if msg was updated: add 'Edited' in date
    if "updated" in msg:
        data_msg_was_edited = True
        data_created = convertDate(str(msg['created']), "%A %H:%M      (%b %d, %Y)") + "   -  edited at " + convertDate(str(msg['updated']), "%H:%M  %b %d")
    else:
        data_msg_was_edited = False
        data_created = convertDate(str(msg['created']), "%A %H:%M      (%b %d, %Y)")
    # --- HTML in message? Deal with markdown
    if "html" in msg:
        # --- Check if there are Markdown hyperlinks [linktext](www.cisco.com) as these look very different
        if "sparkBase.clickEventHandler(event)" in str(msg['html']):
            data_text = convertMarkdownURL(str(msg['html']), 1)
            data_text = convertMarkdownURL(data_text, 2)
        else:
            data_text = convertURL(str(msg['html']))
    elif "text" in msg:
        data_text = convertURL(msg['text'])
        data_text = data_text.replace("<script", "<pre>&lt;")  # --- Replace script in 'text' msg (stopping HTML generation) - 0.20b
        if "<code>" in data_text:
            if "</code>" not in data_text:
                data_text += "</code>"
        data_text = data_text.replace("<", "&lt;").replace(">", "&gt;")  # make sure html in 'text' is not interpreted (v25) except for hyperlinks
        data_text = data_text.replace("&lt;a href", "<a href").replace("&lt;/a&gt;", "</a>").replace("blank'&gt;", "blank'>")
        data_text = str(data_text).replace("\n", "<br>")  # replace \n with <br> - 0.22d3
    if data_text == "" and 'files' not in msg and 'mentionedPeople' not in msg:
        # empty text without mentions or attached images/files: SKIP
        print("_EMPTYmessage_")
        beep(1)  # troubleshooting thing (to see, eh, hear how many "empty messages" are found)
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
    #  IF message is THREADED _AND_ the key doesn't exist: skip
    # >>> below: if/print/else statement are added
    if threaded_message and statMessageMonthKey not in statMessageMonth:
        pass
    else:
        statMessageMonth[statMessageMonthKey] = statMessageMonth.get(statMessageMonthKey, 0) + 1
    if messageMonth != previousMonth and not threaded_message:
        htmldata += f"<div class='cssNewMonth' id='{statMessageMonthKey}'>   {messageYear}    <span style='color:#C3C4C7'>" + messageMonth + "</span><span style='float:right; font-size:56px; color:lightgrey;margin-right:15px; padding-top:0px;'><a href='#top' style='text-decoration:none;color:inherit;'>▲</a></span></div>"
        if outputToText:  # for .txt output
            textOutput += f"\n\n---------- {messageYear}    {messageMonth} ------------------------------\n\n"
    # ====== if PREVIOUS email equals current email, then skip header
    if threaded_message:  # ___________________________________ start thread ______________________________
        htmldata += "<div class='css_message_thread'>"
    else:
        htmldata += "<div class='css_message'>"

    # ====== AVATAR: + msg header: display or not
    if (data_email != previousEmail) or (data_email == previousEmail and timedifference(msg["created"], previousMsgCreated) > 60) or (data_msg_was_edited):
        if userAvatar == "link" and data_userid in userAvatarDict:
            htmldata += f"<img src='{userAvatarDict[data_userid]}' class='avatarCircle'  width='36px' height='36px'/>"
        elif userAvatar == "download" and data_userid in userAvatarDict:
            htmldata += f"<img src='avatars/" + data_userid + ".jpg' class='avatarCircle'  width='36px' height='36px'/>"
        else:  # User that may not exist anymore --> use email as name
            if data_name == data_email:
                htmldata += f"<div id='avatarCircle'>{data_name[0:2].upper()}</div>"
            else:
                # show circle with initials instead of avatar
                try:
                    htmldata += "<div id='avatarCircle'>" + data_name.split(" ")[0][0].upper() + data_name.split(" ")[1][0].upper() + "</div><div class='css_message'>"
                except:  # Sometimes there's no "first/last" name. If one word, take the first 2 characters.
                    htmldata += "<div id='avatarCircle'>" + data_name[0:2].upper() + "</div>"

        msgDomain = data_email.split("@")[1]    # Get message sender domain
        if myDomain == msgDomain:               # If domain <> own domain, use different color
            htmldata += f"<span class='css_email{blurring}' title='{data_email}'>{data_name}</span>"
        else:
            htmldata += "<span class='css_email" + blurring + "' title='" + data_email + "'>" + data_name + "</span>   <span class='css_email_external" + blurring + "'>(@" + data_email.split("@")[1] + ")</span>"
        htmldata += f"<span class='css_created'>{data_created}</span>"
    else:
        htmldata += "<div class='css_message'>"

    if outputToText:  # for .txt output
        if blurring != "":  # For blurring
            data_email = "_____@_____.__"
        if threaded_message:  # add ">>" to text output to indicate a thread v0.23
            textOutput += convertDate(str(msg['created']), "%A %H:%M      (%b %d, %Y)") + "  >> " + data_email + ": "
        else:
            textOutput += convertDate(str(msg['created']), "%A %H:%M      (%b %d, %Y)") + "  " + data_email + ": "

    # ====== DEAL WITH MENTIONS IN A MESSAGE
    if 'mentionedPeople' in msg:
        try:
            statTotalMentions += 1
            for item in msg['mentionedPeople']:
                texttoreplace = "<spark-mention data-object-type=\"person\" data-object-id=\"" + item + "\">"
                data_text = data_text.replace(texttoreplace, "<span class='atmention" + blurring + "'>@")
            data_text = data_text.replace("</spark-mention>", "</span>")
        except:
            print(" **ERROR** processing mentions, don't worry, I will continue")
    if 'mentionedGroups' in msg:
        try:
            statTotalMentions += 1
            for item in msg['mentionedGroups']:
                texttoreplace = "<spark-mention data-object-type=\"groupMention\" data-group-type=\"" + item + "\">"
                data_text = data_text.replace(texttoreplace, "<span style='color:red;display:inline;'>@")
            data_text = data_text.replace("</spark-mention>", "</span>")
        except:
            print(" **ERROR** processing mentions, don't worry, I will continue")
    # check if msg is a card. If yes: add "cannot display" message
    try:
        if "contentType" in msg["attachments"][0]:
            is_card = True
    except:
        is_card = False
    if is_card:
        data_text = "<span class='card_class'>&nbsp;<span style='color:red'>Card</span>&nbsp; content cannot be displayed in this archive&nbsp;</span>&nbsp;  " + data_text
    htmldata += "<div class='css_messagetext'>" + data_text
    if outputToText and 'text' in msg:  # for .txt output
        if msg['text'] == "":
            myErrorList.append("processing msgs: msg WITH html WITHOUT text? html: " + msg['html'] + " -- msg id: " + msg['id'])
        p = re.compile(r'<.*?>')
        textOutput += p.sub('', msg['text']).replace("\"", "'").replace("\n", " ").replace("\r", " ")
        textOutput += "\n\r"
    if outputToText and 'text' not in msg and 'files' not in msg:
        textOutput += "\n\r"

    # ====== DEAL WITH FILE ATTACHMENTS IN A MESSAGE
    if 'files' in msg:
        startTimerFiledownload()
        if data_text != "":
            htmldata += "<br>"
        if downloadFiles == "no":   # download=no  - only show "file attachment", no details whatsoever
            for i in range(len(msg['files'])):
                htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'> attached_file</span>"
                statTotalFiles += 1
            if outputToText:
                textOutput += f" <File Attachment> \n\n"  # v26
        else:  # download=info/images/files
            myFiles = process_Files(msg['files'], msg['created'])
            # SORT attached files by <files> _then_ <images>
            myFiles.sort(key=lambda x: x.split("###")[0].split(".")[-1] in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif'])
            splitFilesImages = ""
            for filename in myFiles:
                # IMAGE POPUP
                filename, filesize = filename.split("###")
                if int(filesize) == 0:
                    filesize_fancy = "0 B"
                else:
                    filesize_fancy = convert_size(filesize)
                fileextension = os.path.splitext(filename)[1][1:].lower()
                if fileextension in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif'] and (downloadFiles in ["images", "files", "image", "file"]):
                    if splitFilesImages == "":
                        # extra return after all attached files are listed
                        htmldata += "<br>"
                        splitFilesImages = "done"
                    htmldata += f"<div class='css_created'><img src='images/{filename} ' title='click to zoom' onclick='onClick(this)' class='image-hover-opacity' /><br>{filename}<br><div class='filesize'>{filesize_fancy}</div> </div>"
                elif "file" in downloadFiles:
                    htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'><a href='files/{filename}'>{filename}</a>  ({filesize_fancy})</span>"
                else:
                    htmldata += f"<br><div id='fileicon'></div><span style='line-height:32px;'> {filename}   ({filesize_fancy})</span>"
                if fileextension in ['jpg', 'png', 'jpeg', 'gif', 'bmp', 'tif']:
                    statTotalImages += 1
                    statTotalImagesSize += int(filesize)
                else:
                    statTotalFiles += 1
                    statTotalFilesSize += int(filesize)
                if outputToText:  # for .txt output
                    textOutput += f"                           Attachment: {filename} ({filesize_fancy})\n"
        stopTimerFiledownload()
    htmldata += "</div>"    # css_messagetext
    htmldata += "</div>"    # css_message or css_message_thread
    htmldata += "</div>"    # other div - needed!
    previousEmail = data_email
    if not threaded_message:
        previousMonth = messageMonth
    previousMsgCreated = msg['created']
    if downloadFiles in ['images', 'files', 'image', 'file'] and (statTotalFiles + statTotalImages) > 0 and dl_duration_total > 0:
        download_stats = f"\n {dl_duration_total:7.1f} download of {downloadFiles.replace('files', 'images and files')} ({statTotalFiles + statTotalImages} files,  {round((statTotalFiles + statTotalImages) / dl_duration_total, 2)} files/sec)"
    elif downloadFiles == "info" and dl_duration_total > 0:
        download_stats = f"\n {dl_duration_total:7.1f} process filenames ({statTotalFiles + statTotalImages} files, {round((statTotalFiles + statTotalImages) / dl_duration_total, 1)} files/sec)"
    else:
        download_stats = ""
stopTimer("generate HTML messages (" + str(round(len(sortedMsgOrderTable), 1)) + ")" + download_stats, dl_duration_total)


# ======  *SORT* DOMAIN USER STATISTICS
startTimer()
myDomainStatsSorted = sorted(
    [(v, k) for k, v in myDomainStats.items()], reverse=True)
myDomainStatsSorted = myDomainStatsSorted[0:10]  # only want the top 10
returntextDomain = ""
returntextMsgMonth = ""
stopTimer("sorting messages", 0)


# ======  TABLE OF CONTENTS
startTimer()
# If message sorting is old-to-new, also sort the TOC
if sortOldNew:  # Default
    mytest = sorted(statMessageMonth.items(), reverse=False)
else:
    mytest = sorted(statMessageMonth.items(), reverse=True)
my_yearcounter = 0
prev_year = 0
tocList = "<table style='width: 290px;'>"
for k, v in mytest:
    pr_year = int(k.split("-")[0])
    pr_monthname = k.split("-")[2]
    if prev_year != pr_year:
        tocList += f"</table><a href='javascript:;' onclick=show('{pr_year}') style='text-decoration: none;font-weight:bolder;font-size'> <div id='yeararrow{pr_year}' style='display:inline;'>▼</div>  {pr_year}</span></a><br>"
        tocList += f"<table id='expand year-{pr_year}' style='width: 290px;'>"
        tocList += "<tr><td>"
        my_yearcounter += 1
    else:
        tocList += "<tr><td>"
    tocList += f"<a href='#{k}' style='text-decoration:none;'>&nbsp;&nbsp;{pr_year} - {pr_monthname}</a></td>"
    tocList += f"<td><span class='month_msg_count'>{v:,}</span></td></tr>"
    prev_year = pr_year

messageType = "newest"
if not sortOldNew:
    messageType = "oldest"
tocList += "</table>"
tocList += "<table><tr><td colspan='2'>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'><a href='#endoffile' style='text-decoration:none;'>" + messageType + " message</a></span></td></tr></table>"


# ======  DOMAIN MESSAGE STATISTICS
total_stat_users = 0
returntextDomain += "<table id='mytoc' style='width: 220px;'>"
for domain in myDomainStatsSorted:
    if domain[1] == "user_removed_their_msg.com":
        continue
    if blurring != "":
        blurring = "class='myblur'"
    returntextDomain += f"<tr><td {blurring}>{domain[1]}</td><td style='text-align:right;'>{domain[0]:,}</td>"
    total_stat_users += int(domain[0])
if (statTotalMessages - total_stat_users) > 0 and len(myDomainStatsSorted) > 9:
    returntextDomain += f"<tr><td>...other domains</td><td style='text-align:right;'>{(statTotalMessages-total_stat_users):,}</td>"
returntextDomain += "</table>"


# ======  MESSAGE & FILE STATISTICS
tocStats = "<table id='mytoc' style='width: 250px;'>"
tocStats += f"<tr><td># of messages: </td><td style='text-align:right;'> {len(sortedMsgOrderTable):,} </td></tr>"
#  ^^^^ 0.26d don't show total msg downloaded but the actual number of msg
if statTotalImages > 0:
    tocStats += f"<tr><td> # images: "
    if downloadFiles in ['no', 'info']:
        tocStats += f"<span style='color:grey;font-size:10px;'>not downloaded</span> "
    tocStats += f"</td><td style='text-align:right;'> {statTotalImages:,} </td></tr>"
if statTotalImages > 0 and statTotalImagesSize > 0:
    tocStats += f"<tr><td>&nbsp;&nbsp;&nbsp;size: </td><td style='text-align:right;'> {convert_size(statTotalImagesSize)} </td></tr>"
    tocStats += f"<tr><td>&nbsp;&nbsp;&nbsp;average size: </td><td style='text-align:right;'> {convert_size(statTotalImagesSize / statTotalImages)} </td></tr>"
tocStats += f"<tr><td> # files: "
if downloadFiles in ['no', 'info', 'images', 'image']:
    tocStats += f"<span style='color:grey;font-size:10px;'>not downloaded</span> "
tocStats += f"</td><td style='text-align:right;'> {statTotalFiles:,} </td></tr>"
if statTotalFiles > 0 and statTotalFilesSize > 0:
    tocStats += f"<tr><td>&nbsp;&nbsp;&nbsp;size: </td><td style='text-align:right;'> {convert_size(statTotalFilesSize)} </td></tr>"
    tocStats += f"<tr><td>&nbsp;&nbsp;&nbsp;average size: </td><td style='text-align:right;'> {convert_size(statTotalFilesSize / statTotalFiles)} </td></tr>"
tocStats += f"<tr><td># @mentions: </td><td style='text-align:right;'> {statTotalMentions:,} </td></tr>"
tocStats += f"<tr><td># total members: </td><td style='text-align:right;'> {len(myMembers):,} </td></tr>"
tocStats += f"<tr><td># active members: <br>&nbsp;&nbsp;&nbsp;<span style='font-size:11px;'>(in this archive)</span> </td><td style='text-align:right;'> {len(uniqueUserIds):,} </td></tr>"
if statTotalMessages > maxTotalMessages - 10:
    tocStats += f"<tr><td colspan='2'><br><span style='color:grey;font-size:10px;'>space contains more than  {statTotalMessages:,} messages</span></td></tr>"
tocStats += "</table>"
if outputToText:  # for .txt output
    textOutput += f"\n\n\n STATISTICS \n--------------------------\n # of messages : {len(sortedMsgOrderTable):,}\n # of images   : {statTotalImages:,}\n # of files    : {statTotalFiles:,}\n # of mentions : {statTotalMentions:,}\n\n\n"
    #  ^^^^ 0.26d don't show total msg downloaded but the actual number of msg


# ======  HEADER
newtocList = "<table class='myheader' id='myheader'> <tr>"
newtocList += "<td style='width:300px;'> <strong>Index </strong>"
newtocList += "<span style='text-decoration:none; font-size:10px;'><a href='javascript:;' onclick='show_showall()'>expand</a> / <a href='javascript:;' onclick='show_hideall()'>collapse</a></span>"
newtocList += "<br>" + tocList + " </td>"
newtocList += "<td> <strong>Numbers</strong><br>" + tocStats + " </td>"
newtocList += "<td> <table id='mytoc' style='width: 220px;'><tr><td style='text-align:left;font-weight:bold;'>Top-10 domains</td><td style='text-align:right;font-weight:bold;'># messages</td></tr></tbody></table>" + returntextDomain + " </td>"
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
htmlfooter = "<br><br><div class='cssNewMonth' id='endoffile'> end of file &nbsp;&nbsp;<span style='float:right; font-size:16px; margin-right:15px; padding-top:24px;'><a href='#top' style='text-decoration:none;'>back to top</a></span></div><br><br>"

# ======  PUT EVERYTHING TOGETHER
print("\n #8 --- Finalizing HTML")
htmldata = htmlheader + newtocList + htmldata + htmlfooter + imagepopuphtml + "</body></html>"
stopTimer("generate ToC, statistics, header and footer", 0)


# ======  WRITE to HTML FILE
startTimer()
with open(myOutputFolder + "/" + outputFileName + ".html", 'w', encoding='utf-8') as f:
    print(htmldata, file=f)
stopTimer("write html to file", 0)

# ======  WRITE to TEXT FILE
if outputToText:
    with open(myOutputFolder + "/" + outputFileName + ".txt", 'w', encoding='utf-8') as f:
        print(textOutput, file=f)


if printPerformanceReport:
    msg_time = int(performanceReport.split("order table")[1].split(" generate HTML")[0].lstrip().split(".")[0])
    if msg_time == 0:
        msg_time = 1
    msg_nr = int(performanceReport.split(" (")[1].split(")")[0])
    msg_statsline = performanceReport.split("order table")[1].split(")")[0].lstrip() + ")"
    msg_per_sec = msg_nr / msg_time
    msg_statsline_new = msg_statsline.replace(")", f" msg, {msg_per_sec:.0f} msg/sec)")
    performanceReport = performanceReport.replace(msg_statsline, msg_statsline_new)
    print(f"{performanceReport}\n\n")  # ______________________________________________________\n")


# ======  PRINT ERROR LIST
if len(myErrorList) > 0 and printErrorList:
    print("\n    -------------------- Error Messages ---------------------")
    for myerrors in myErrorList:
        print(f" > {myerrors}")

print(" _______________________ ready ________________________\n\n")
beep(1)

# ------------------------------- end of code -------------------------------
