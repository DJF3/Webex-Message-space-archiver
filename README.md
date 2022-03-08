# Webex Space Archiver 

**NEW: Important Release! v25** (check out new features in the [release notes](#releasenotes))

[Features](#features)

[Start](#start)

[Configure](#configuration)

[Release notes](#releasenotes)

[Troubleshooting](#troubleshooting)

[Feedback & Support](#feedback)

[<img src="https://camo.githubusercontent.com/7a785e6fab9f9040fb3739fdc2df1284b3ef199c7450b3d379716b365a37156f/68747470733a2f2f7374617469632e70726f64756374696f6e2e6465766e6574636c6f75642e636f6d2f636f646565786368616e67652f6173736574732f696d616765732f6465766e65742d7075626c69736865642e737667" alt="published" data-canonical-src="https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg" style="max-width: 100%;">](https://developer.cisco.com/codeexchange/github/repo/DJF3/Webex-Teams-Space-Archive-v2/) 

Archive Cisco Webex space messages to a single HTML file. NOTE: This code is written for a customer as an example. I specifically wanted 1 (_one_) .py file that did everything. It's not beautiful code but it works :-)
Feedback? Please go [here](#feedback) and let me know what you think!

# VIDEO 
[**_How to use & Demo_**](https://youtu.be/gula_Hxh2ms)

# SCREENSHOT
Example HTML file of an archived Webex space: 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<img src="https://raw.githubusercontent.com/DJF3/Webex-Message-space-archiver/master/webexteams-archive-screenshot.jpg" width="600px">


# REQUIREMENTS
* A (free) [Webex](https://www.webex.com/team-collaboration.html) account
* Python 3.9 or higher (not tested with 3.6)
* Python '[requests](http://docs.python-requests.org/en/master/user/install/#install)' library
* Be a member of the Webex message space you want to archive
* Mac: SSL fix (see [troubleshooting](#troubleshooting) section at the end)  


<a name="features"/>
        
# Features

* Archive all messages in a space
* Find space ID with built in search function
* Batch archiving with multiple config files
* Deal with threaded messages
* Download space images, files or both (with msg file date)
* All files are organized: \spacenamefolder with subfolders for \files, \images, \avatars
* Export space data to JSON or TXT file
* Restrict messages by number of messages, number of days, from- date or from-to date
* Display: messages grouped per month, with navigation at the top
* Display: show full user names
* Display: show (linked or downloaded) user avatars
* Display: attached file-names + size
* Display: "@mentions" in a different color
* Display: quoted or formatted text
* Display: external users in different color (users with other domain)
* Display: images in popup when clicked
* Print: just like it appears on the screen

## It doesn't:
* Clean your dishes
* Download whiteboards (unless you post a snapshot)
* Download/display files shared in external Enterprise Content Management systems (Onedrive/Sharepoint)
* Display reactions to messages (not accessible via API)
* Render cards

## NOTE:

* The message TIME **displayed** is in the UTC timezone. The timezone on your device defines how this UTC time/date is displayed. A message send at 12:43 CEST is stored as 10:43 UTC. When you change your timezone to PDT (UTC-7) it will be displayed as 03:43.
* When **printing** the generated HTML file in Firefox: File, Print, check "print background colors and images", then print or save to PDF
* To store your Webex token in an environment variable:
  * Windows: ```set WEBEX_ARCHIVE_TOKEN=YOUR_TOKEN_HERE```
  * Mac: ```export WEBEX_ARCHIVE_TOKEN='YOUR_TOKEN_HERE'```


<a name="start"/>

# Start

1. Make sure you meet the requirements

2. Run the script to _create the configuration file_ "webexspacearchive-config.ini" (if it does not exist)

3. In the webexspacearchive-config.ini file, update your developer token. Save the file.

4. Now you can:
* Run the script with a search argument as a parameter to find the space ID. Example: 'python webex-space-archive.py spacename'
* Run the script without parameters to archive a space that is configured in the .ini file.
* Run the script with the name of an .ini file to use that .ini file.


**UPGRADE?**
Replace the .py file and keep the configuration file (.ini). 
To get changes in the .ini file, run the script once without .ini file and it will create one for you with the latest remarks and features.


<a name="configuration"/>

# Configuration
Edit the following variables in the python file:

---

**Personal Token**: you can find this on [developer.webex.com](https://developer.webex.com/docs/api/getting-started), login (top right of the page) and then scroll down to "Your Personal Access Token".
_NOTE_ see the 'NOTE' section above to see how you can also use an environment variable to store your token!
> **mytoken = "YOUR_TOKEN_HERE"**

***NOTE***: This token is valid for 12 hours! Then you have to get a new Personal Access Token.

---

**Space ID**: To find this, first save your developer token in the .ini file. Then run the script with a search arguments as a parameter. It will list all spaces+spaceId that match you search argument.
Alternatively: go to [Webex Developer List rooms](https://developer.webex.com/docs/api/v1/rooms/list-rooms), make sure you're logged in, set the 'max' parameter to '900' and click Run.
If you don't see the RUN button, make sure 'test mode' is turned on (top of page, under "Documentation")
TIP: to get the space ID of a space that you are in, in the client go to help / copy space details. Then in Webex talk to the bot "spaceidbot@webex.bot" and paste the space details. In return you get the space ID to be used here
> **myspaceid = "YOUR_SPACE_ID_HERE"**


---

**Downloadfiles**: do you want to download images or images & files? Think about it. Downloading images *and* files can significantly increase the archive time and consume disk space.  Downloaded images or files are stored in the subfolder. Options:
> **downloadfiles = info**

- "no"         : (default) no downloads, only show the text "file attachment"
- "info"       : no downloads, only show the filename and size
- "images"     : download images only
- "files"      : download files *and* images

---

**UserAvatar**: Do you want to show the user avatar or an icon? Avatars are not downloaded but *linked*. That means the script will get the user Avatar URL and use that in the HTML file. So the images are not downloaded to your hard-drive. Needs an internet connection in order to display the Avatar images.
> **useravatar = link**

- "no"        : (default) show user initials
- "link"      : link to avatar images (needs internet connection!)
- "download"  : download avatar images

---

**Max Messages**: Restrict the number of messages that are archived.  Some spaces contain 100,000 messages and you may not want to archive all of them. To archive the *last* 5000 messages:
> **maxtotalmessages = 5000**

- (empty)     : (default) last 1,000 messages
- 4000        : (example) download the last 4,000 messages
- 60d         : (example) download messages from the last 60 days. 120d = 120 days
- 22052021-   : (example) download messages after May 22nd 2021 (ddmmyyyy-) *****
- 22052021-18082021: download messages between May 22nd and August 18 2021 (ddmmyyyy-ddmmyyyy) *****
* = date format configurable in the .py code, variable 'maxmsg_format'


---

**OutputFilename**: Enter the file name of the output HTML file. If EMPTY the filename will be the same as the Archived Space name (recommended).
> **outputfilename = yourfilename.html**

---

**Sorting**: of archived messages.
> **sortoldnew = yes**

- "yes"   : (default) last message at the bottom (like in the Webex client)
- "no"     : latest message at the top

---

**OutputJSON**: Besides the .html file, how would you like to store your messages?
> **outputjson = no**

- "no"        :(default) only generate .html file
- "yes/both"  :output message data as .json and .txt file
- "json"      :output message data as .json file
- "txt"       :output message data as .txt file



<a name="troubleshooting"></a>

# Troubleshooting
Most of the errors should be handles by the script.
* **SSL Issue**: On a Mac: the default SSL is outdated & unsupported. Check out the *readme.rtf* in your Python Application folder. That folder also contains a "Install certificates.command" which should do the work for you.


<a name="releasenotes"></a>

# Release Notes

## Enhancements in release v25 - February 10th 2022

**Important Enhancements / fixes that may require your attention**
- REQUIREMENTS: Python 3.9 - the code will check for this version. I have not tested with older versions.
- CONFIG: Get TOKEN from _environment variable_ "WEBEX_ARCHIVE_TOKEN" if the .ini does not have a token. Great for batch operations
- CONFIG: Run script with .ini filename as parameter for batch operations. Store your token in an environment variable
- REQUEST: NEW! "download=no" ONLY shows the text: "attached_file" without filename/size. Get filename/size? "download=info"
- BUG: Messages without a parent only appeared in the JSON file, not in the .txt or .html files.
- BUG: More than 9 messages per thread were not shown in html/txt (tnx ojchase!) 
- BUG: Shared code on-screen: no wrapping but when printing: wrapping so no content goes lost.

**NEW**
- FUNCTIONAL: Table of content: YEARS are now collapsable (one click. Default: expanded)
- FUNCTIONAL: Create some image/file SIZE stats (total image/file size, avg image/file size)
- FUNCTIONAL: End script with 2 beeps. (1=attention, 3=error)
- VISUAL: "updated" field now showing the updated date/time 
- VISUAL: in top-10 user domains also show the remaining user domain count
- VISUAL: For txt export, prefix threaded messages in the TXT export with ">> " to visualize the thread
- VISUAL: Space name (header) wraps if long
- VISUAL: "Top-10 user" statistics, added "# messages" to make it clear that it's the number of msg
- VISUAL: Month headers now have a button to navigate to the top.
- VISUAL: remove underline from month TOC links and last/first message link
- VISUAL: "use this exact format: ddmmyyyy-ddmmyyyy or ddmmyyyy-" now displays the configured dateformat.
- VISUAL: When using a different .ini (via commandline parameter), show the filename in the HTML header
- VISUAL: If download=no/info, add "no downloads" message in the top-of-the-page statistics
- VISUAL: With a custom max_msg dateformat, the INI should use this format in the helptext & error messages
- FILTERING: Ability to enter a startdate without enddate (assuming "today" is the enddate)
- FILTERING: make the maxtotalmessages dateformat (below) configurable (in script, not the .ini)
- FILTERING: archive msg BETWEEN 2 dates. maxtotalmessages = 28052021-28062021  (ddmmyyyy) (chriskoch99)

**FIXED**
- CODE: If a space has NO messages (because of auto-archiving or message age max) error. Now it stops with a message.
- VISUAL: (ojchase) If last space msg = threaded -> shown as a normal message. Fixed.
- VISUAL: Message without html but only text? "\n" and "\n\n"'s are ignored. (ojchase) 
- VISUAL: stats: "...other users" showed msg from total of top-10 domain, now it shows the # of non-top10 users.
- VISUAL: better indication that a card message cannot be displayed.
- VISUAL: expand icon for year on previous line, now on the same line as the year (display-inline)
- VISUAL: if you collaps the last year in the TOC, now it doesn't hide the "last message" link
- VISUAL: if sortoldnew=no, the "last message" link should say "newest message", otherwise "oldest message"
- VISUAL: index table of first 'year' is wider than the next ones. now they are all 300px
- VISUAL: with total/avg file size stats, don't round(2) for anything lower than GB 
- VISUAL: When printing, _long_ strings would not be wrapped: --> 'word-break: break-word;'
- VISUAL: When a _folder_ is configured in the 'outputFileName': throw error message
- VISUAL: html code in "text" field was interpreted (changing layout/fonts/colors/etc)
- BUG: space name with "#", the '#' is removed leaving a space. --> also removing space 
- BUG: wrong brackets in javscript code of generated html (for expand/collapse of months)
- BUG: created parents have a fake user id --> this caused a problem downloading avatars
- BUG: created parents (that did not exist) were not written to JSON output
- BUG: New year detection for the month TOC was done by checking for "Jan". Not good for localized setups. Now checking for the month number!
- CONFIG - (ojchase) When 'maxtotalmessages' in .ini < 21: error. Fixed.
- SEARCH - if no group or direct spaces are found, you still see the header.
- DOC: wrong url in ini (rooms-get documentation))
- TEST: Tested file modified date on WINDOWS! Working!

**OPEN**
- VISUAL: When retrieving messages between 2 dates, the total-message-count may not be 100% accurate. (only affects a statistic in the header)
- TIMEZONE: Generated HTML not using DST ("summertime"), to be addressed in an upcoming release

**NOTE**
- CARDS: cards and buttons won't be visible in the html
- NOTE: The code reads messages with UTC time and displays it in the local timezone without being aware of summer/winter time. In the summer msg times could be off 1 hour.







## Enhancements in release v21 - September 2th 2021

**NEW**
- FILE   - !! downloaded files get the time/date as the message where they were attached to!
- SEARCH - !! results are split in direct & group spaces (separate bots/users and group spaces)
- SEARCH - space search has a progress indicator
- REPORT - performance report shows nr of messages (+ msg/per second)
- AVATAR - downloads: updated code to use the requests library --> removed urllib
- AVATAR - filenames: add ".jpg" to downloaded avatars (because they are .jpg files)
- VISUAL - as Webex cards are way to complex to render, a clear label is added to Cards messages
- VISUAL - show progress bar while generating HTML (this is the most time consuming process)
- VISUAL - show progress bar while retrieving messages (this process also takes a lot of time)
- VISUAL - add thousands separator in statistics to make it easier to read
- VISUAL - align message count to the right (align all stat counts to the right)
- VISUAL - changed font to the -Light variant of HelveticaNeue

**FIXED BUGS**
- LAY-OUT - month msg count, now using class and removed align:right;
- LAY-OUT - many small changes to increase readability and consistency
- VISUAL  - "#7 generating HTML" is now showing that this includes downloading of files
- VISUAL  - step 4c starts on the same line after step4b.
- VISUAL  - performance report reserve more digits for time (7 instead of 3)
- INTERACTION - In very specific scenarios cards can cause an error --> help message with suggestion
- INTERACTION - not all exit commands played 3 beeps
- CODE   - Can't create folder if space name ends with a space. get_roomname return: includes strip()
- CODE   - change api.ciscospark.com to the new webexapis.com
- SEARCH - space search had a bug and is now working reliably and efficient
- SEARCH - Search for spaces --> error 504. Changed the list_rooms max from 900 to 500 and deal with errors
- REBRANDING - change name from Webex Teams to Webex.
- REBRANDING - change filenames to remove 'teams'
- REBRANDING - because of the name change: check for files with the old name, give instructions and stop.
- PROCESSING - messages with many URLs: regex replaced every single url. Now only unique urls are replaced
- READ PEOPLE - when getting >50 personIds->URL length>5000 char->Error. lowered chunksize from 80 to 50.
- REPORT - performance report doesn't crash if "generate HTML" is <1 second.
- OUTPUT - Don't interpret TEXT like "<script" --> change to "<pre>&lt;script".



## Enhancements in release v20 - February 11th 2020

**NEW**
- !! MESSAGE THREADING: Supporting message threading !!
- MESSAGES: Changed message time format so it's easier to read
- MESSAGES: you can see 'Edited' when a message was modified after sending.
- MESSAGES: sender color/format different for external users (now just like in the Teams client)
- LAYOUT: changed left border of threaded message to grey
- IMAGES: multiple images in 1 message? Now shown as grid, not a list.

**FIXED BUGS**
- MENTIONS: code would not display "@all" mentions
- ATTACHMENTS: images with uppercase extensions were not downloaded
- SORTING: "new->old", all messages considered NEW because current_msg_time - prev_msg_time is never > 60s
- ATTACHMENTS: 'jpeg' file not recognized as image because it assumed the extension has 3 characters
- ATTACHMENTS: 'jpeg' images are now embeded (like png/jpg/etc)
- ATTACHMENTS: messages without text (only attachments/images) --> files won't download
- THREADED MESSAGE: with threading, the message order is messed up --> now a msg index is created first
- THREADED MESSAGE: with a # of messages limit, you could run into messages that belong to a previous thread. --> IGNORE those
- THREADED MESSAGE: threaded messages + avatars should be indented
- THREADED MESSAGE: When sorted new-old, threaded messages should be sorted old-new
- THREADED MESSAGE: crossing a month? --> thread reply in Nov on Thread in Oct: showing new month header. --> FIXED
- THREADED MESSAGE: these messages should have grey bar like ">" before it --> border-left!
- MESSAGES: When adds the same URL in a msg multiple times it would only appear once
- INDEX/STATS: index + stats not vertically aligned to top
- ATTACHMENTS with no name / just spaces as a name cause an error.



## Enhancements in release v19a - May 27th 2019
**IMPORTANT**
- PRINT: A printed (to PDF) version of the generated file looks like the screen    (27may2019-v19a)
         *Firefox* tip: File, Print, check "print background colors and images", then print/save to PDF
         
**NEW**
- STATISTICS: add number of different users who have written messages   (24may2019-v19a)
- STATISTICS: add total number of members   (24may2019-v19a)
- ERROR: Avatar download errors are not reported if retries were successful   (22may2019-v19a)

**Fixed bugs**
- LAYOUT: Header is not resizing with browser width: better lay-out/print    (27may2019-v19a)
- LAYOUT: TOC + statistics now have a minimum size: better lay-out/print    (27may2019-v19a)
- PRINT: removed "back to top" arrow from printing    (27may2019-v19a)
- HEADER: 'avatar' setting missing    (27may2019-v19a)
- BUG: remove "back to top" text from month headers?   (27may2019-v19a)



## Enhancements in release v17h-v19 - May 22nd 2019
**IMPORTANT**
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

**NEW**
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

**Fixed bugs**
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
* ~~PRINTing the HTML page to PDF (for example) will mess up lay-out (fixed in v0.19a)~~


<a name="feedback"/>

# Feedback & Support
Please click this link and [enter your feedback](https://tools.sparkintegration.club/forms/joinspace/jv4kauin9bm7cs01va5vhosi3jro6a/) in the text field. If you want me to respond let me know in your message and enter your real email address.

This is based on the older [Webex Teams Space archiver](https://github.com/DJF3/Webex-Teams-Space-Archive). Because of the major updates I published it in *this* repository. 
