*MAJOR UPDATE v19 - MAJOR UPDATE v19 - MAJOR UPDATE v19*

[Features](#features)

[Start](#start)

[Configure](#configuration)

[Release notes](#releasenotes)

[Troubleshooting](#troubleshooting)

[Roadmap](#roadmap)

[Feedback & Support](#feedback)


# Webex Teams Space Archive NEW
Archive Cisco Webex Teams Space messages to a single HTML file. It is based on the older [Webex Teams Space archiver](https://github.com/DJF3/Webex-Teams-Space-Archive). Because of the major updates I published it in *this* repository. You can use one or the other.
NOTE: This code is written for a customer as an example. I specifically wanted 1 (one) .py file that did everything. It's not beautiful code but it works :-)
Feedback? Please go [here](#feedback) and let me know what you think!

How-to & Demo: https://youtu.be/gula_Hxh2ms

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/DJF3/Webex-Teams-Space-Archive-v2/master/webexteams-archive-screenshot.jpg" width="400px">

# REQUIREMENTS
* A (free) [Webex Teams](https://www.webex.com/team-collaboration.html) account
* Python 3.6 or higher
* Python '[requests](http://docs.python-requests.org/en/master/user/install/#install)' library
* Be a member of the Webex Teams Space you want to archive
* Mac: SSL fix (see [troubleshooting](#troubleshooting) section at the end)


<a name="start"/>

# Features

### DOES:
* Archive all messages in a space
* Find space ID with built in search function
* Download space images, files or both
* All files are organized: \spacenamefolder with subfolders for \files, \images, \avatars
* Export space data to JSON or TXT file
* Restrict messages by number of messages or number of days
* Display: messages grouped per month
* Display: show full user names
* Display: show (linked or downloaded) user avatars
* Display: attached file-names + size
* Display: "@mentions" in a different color
* Display: quoted or formatted text
* Display: external users in different color (users with other domain)
* Display: images in popup when clicked


### DOESN'T:
* Clean your dishes
* ~~*Download* user avatar files~~


### NOTE:

* The message TIME **displayed** is in the UTC timezone. The timezone on your device defines how this UTC time/date is displayed. A message send at 12:43 CEST is stored as 10:43 UTC. When you change your timezone to PDT (UTC-7) it will be displayed as 03:43.



<a name="start"/>

# Start

1. Run the script to create the configuration file "webexteamsarchive-config.ini" (if it does not exist)

2. Update your developer token in the webexteamsarchive-config.ini file. Save the file.

3. Now you can:
* Run the script to archive a space.
* Run the script with your search argument as a parameter to find the right space ID. Example: python webex-teams-space-archive.py customername



<a name="configuration"/>

# Configuration
Edit the following variables in the python file:

---

**Personal Token**: you can find this on [developer.webex.com](https://developer.webex.com/docs/api/getting-started), login (top right of the page) and then scroll down to "Your Personal Access Token".
> **mytoken = "YOUR_TOKEN_HERE"**

***NOTE***: This token is valid for 12 hours! Then you have to get a new Personal Access Token.

---

**Space ID**: To find this, first save your developer token in the .ini file. Then run the script with a search arguments as a parameter. It will list all spaces+spaceId that match you search argument.
Alternatively: go to [Webex Teams Developer List rooms](https://developer.webex.com/endpoint-rooms-get.html), make sure you're logged in, set the 'max' parameter to '900' and click Run.
If you don't see the RUN button, make sure 'test mode' is turned on (top of page, under "Documentation")
> **myspaceid = "YOUR_SPACE_ID_HERE"**


---

**Downloadfiles**: do you want to download images or images & files? Think about it. Downloading images *and* files can significantly increase the archive time and consume disk space.  Downloaded images or files are stored in the subfolder. Options:
> **downloadfiles = no**

- "no"         : (default) no downloads, only show the text "file attachment"
- "images"  : download images only
- "files"       : download files *and* images

---

**UserAvatar**: Do you want to show the user avatar or an icon? Avatars are not downloaded but *linked*. That means the script will get the user Avatar URL and use that in the HTML file. So the images are not downloaded to your hard-drive. Needs an internet connection in order to display the Avatar images.
> **useravatar = link**

- "no"        : (default) show user initials
- "link"      : link to avatar images (needs internet connection!)
- "download"  : download avatar images

---

**Max Messages**: Restrict the number of messages that are archived.  Some spaces contain 100,000 messages and you may not want to archive all of them. When configured it will archive the *last* 5000 (example) messages.
> **maxtotalmessages = 5000**

- (empty)     : (default) 1,000 messages
- 4000        : (example) download the last 4,000 messages
- 60d         : (example) download messages from the last 60 days. 120d = 120 days

---

**OutputFilename**: Enter the file name of the output HTML file. If EMPTY the filename will be the same as the Archived Space name (recommended).
> **outputfilename = yourfilename.html**

---

**Sorting**: of archived messages.
> **sortoldnew = yes**

- "yes"   : (default) last message at the bottom (like in the Teams client)
- "no"     : latest message at the top

---

**OutputJSON**: Besides the .html file, how would you like to store your messages?
> **outputjson = no**

- "no"        :(default) only generate .html file
- "yes/both"  :output message data as .json and .txt file
- "json"      :output message data as .json file
- "txt"       :output message data as .txt file



<a name="troubleshooting"/>

# Troubleshooting
Most of the errors should be handles by the script.
* **SSL Issue**: On a Mac: the default SSL is outdated & unsupported. Check out the *readme.rtf* in your Python Application folder. That folder also contains a "Install certificates.command" which should do the work for you.


<a name="releasenotes"/>

# Release Notes

## Enhancements in release v17h-v19

- TIME: Messages are stored in UTC. Your timezone is detected and time/dates are converted  (v18b9)
- FILES: HTML files are always stored in a folder.       (v18b)
- FILES: images/files/avatars are stored in their own folder (/images, /files, /avatars)    (v18b)
- OUTPUT: export message data as .txt (besides .html & .json)   (v18b8)
- OUTPUT: export message data as a .json file (default: no)   (v18b2)
- OUTPUT: ability to restrict number of messages by nr. of days: '60d' = 60 days  (v18b7)
- AVATAR: Config item 'useravatar' now has the option 'download' to download avatar images  (v18)
- AVATAR: download: Only downloads Avatars of the people who actually wrote a message    (v18b7)
- AVATAR: empty? Show circle with first 2 initials    (v17h)
- FIND SPACE ID: Find space ID by running the script with a search argument as parameter. (v17h)


## Minor enhancements in release v17h-v19

- TIME: add time-zone detection in script    (v18b9)
- TIME: add 'generation' time-zone to header    (v18b9)
- REQUIREMENT: for Python 3.6 or higher is checked (because of print(f"{blah}"))   (v18b8)
- FONT: easier to read: removed: HelveticaNeue-Light/Helvetica Neue Light from CSS    (v18b9)
- ERROR: print certain errors when the script finishes (toggle: by setting in the script)   (v18b8)
- PRIVACY: change filename for avatars to userId   (v18b8)
- PERFORMANCE: report displayed based on variable printPerformanceReport=False in script  (v18b7)
- NAVIGATE: add floating "back to top" button   (v18b3)
- STATS: When not downloading files, it will provide stats for files AND images. (v18b3)
- NOTIFY: spaceId not set: explain what they can do: run with search parameter!   (v19)
- NOTIFY: When the script is ready, it beeps once    (v18b3)
- FOLDERS: will be created AFTER messages/members have been retrieved. ERROR? No folders created.   (v18b8)
- FOLDER: If a folder exists, it will add a number '-01', '-02' instead of '-1', '-2'    (v18b3)
- INI: .txt and/or .json file: configurable in .ini    (v18b8)
- INI: Renamed config key 'myroom' to 'myspaceid' - but you can use both     (v18b4)
- INI: Updated the .ini file lay-out to make it more compact and easier to read.    (v18b3)
- INI: change downloadfiles key to 'download'      (v18a2)
- MESSAGE: Removed gray bubble (v18a2)
- ATTACHMENTS: added base64 encoded paperclip icon (v18a2)
- ATTACHMENTS: show file size and filename underneath image   (v18a1)
- ATTACHMENTS: when not downloading files or images, still display the filename & size.     (v18a1)
- IMAGES: Simplified CSS in code for images    (v18b3)
- IMAGES: Decreased space between multiple images in the same message    (v18b3)
- IMAGES: Image popup: added "escape" key to close the image    (v17h)



## Bugs Fixed in release v17h-v19

- CODE: steps appeared twice: #7, #7, #8. NOW have #7, #8, #9   (v19)
- SEARCH: if you haven't set your space ID, the search function doesn't work!    (v19)
- DOWNLOAD: could cause a KeyError: 'content-disposition'. Code now deals with this situation.   (v18b9)
- HTML: header height wrong (66px) - changed to 76px because of 2nd line with space info    (v19)
- HTML: code still contained: <spark-mention> tags - they do nothing - removed.   (v18b9)
- AVATAR: step 4 had a wrong reference to members.personId that should have been members['personId']   (v18b5)
- AVATAR: Display user avatar+msg when the same user writes a msg >60 seconds after the prev message   (v18b4)
- AVATAR: download: store failed downloads in a list and re-process these items! (try max 3x)   (v18b7)
- ATTACHMENTS: more than 1 attachment in a single messsage? They are processed twice. Fixed   (v18b9)
- ATTACHMENTS: 0 byte file: don't download the file, only show the filename/size    (v18b3)
- EXPORT: set outputjson to "json"-> the outputToText variable is not set.     (v18b9)
- EXPORT: to .txt file: full of HTML tags for mentions + divs: strip!  (v18b8)
- HTML: Unnessecary spaces after filename in img link      (v18b)
- HYPERLINKS: Markdown ('embedded') hyperlinks are not working (no link)    (v18b8)
- HYPERLINKS: Markdown hyperlinks did not open in a new window:    (v18b8)
- INI: Outputfilename (when configured in the .ini) is not being used!     (v18b)
- INI: If maxmessages is not set it will use the default: 1000    (v18b3)
- IMAGES: If a filename/image contains a colon (':'), the image linking doesn't work     (v18a2)
- IMAGES: Depending on the size (very wide, very high) images are not resized correctly.      (v18a2)
- MAX MSG when limiting max messages by days, it would not show at the top of the screen.    (v18b7)
- MAX MSG maxMessages not displayed in HTML header (setting)   (v18b7)
- MAX MSG: if you set the max age to 10 days and no messages are <10 days old: error.   (v18b8)
- NOTIFY: Beep function printed 3 empty lines. fixed with end/flush in print      (v18a2)


## Limitations in v19
* If _HTML code_ is written as TEXT (without marking it as code using  ```), the message may not be displayed or it could mess up the lay-out for remaining messages
* PRINTing the HTML page to PDF (for example) will mess up lay-out (fixed in v0.19a)


<a name="roadmap"/>

# Roadmap
* PRINT: update lay-out so printing works great (version 0.19a)
* WEB: make this script web-based
   * Login using Webex Teams (oAuth)
   * Select space to archive
   * Space messages are exported to an HTML file
   * User receives 1:1 message from a Bot with the HTML file attached


<a name="feedback"/>

# Feedback & Support
Please click this link and [enter your feedback](https://tools.sparkintegration.club/forms/joinspace/jv4kauin9bm7cs01va5vhosi3jro6a/) in the text field. If you want me to respond let me know in your message and enter your real email address.
