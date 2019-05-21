# Webex-Teams-Space-Archive-v2
Archive Cisco Webex Teams Space messages to a single HTML file. It is based on the older [Webex Teams Space archiver](https://github.com/DJF3/Webex-Teams-Space-Archive). Given the major updates I published it in *this* repository. You can use one or the other. 
NOTE: This code was written for a customer as an example. I specifically wanted 1 (one) .py file that did everything. It's not beautiful code but it works :-)

<img src="https://raw.githubusercontent.com/DJF3/Webex-Teams-Space-Archive-v2/master/webexteams-archive-screenshot.jpg" width="400px">height="whatever"

# REQUIREMENTS
* A (free) [Webex Teams](https://www.webex.com/team-collaboration.html) account
* Python 3.6 or higher
* Python '[requests](http://docs.python-requests.org/en/master/user/install/#install)' library
* Be a member of the Webex Teams Space you want to archive
* Mac: SSL fix (see troubleshooting section at the end)


# Features
### DOES: 
* Archive all messages
* Group per month
* Show full names 
* Show (linked) Avatars
* Display hyperlinks
* Display attached file-names
* Display "@mentions" in a different color
* Display formatted text
* Display quoted text 
* Display external users in different color (users with other domain)
* Download all images or images+files 
* Image attachments display in popup when clicked

### DOESN'T: 

* Clean your dishes
* *Download* user avatar files
 


# Start

When you start, execute the script once. It will not see the configuration file "webexteamsarchive-config.ini" and create one. 

Edit webexteamsarchive-config.ini and update the configuration items listed below and re-run the script to make it work. 


# Configuration
Edit the following variables in the python file:

---
> mytoken = "YOUR_TOKEN_HERE"

Personal Token: you can find this on [developer.webex.com](https://developer.webex.com/docs/api/getting-started), login (top right of the page) and then scroll down to "Your Personal Access Token".

***NOTE***: This token is valid for 12 hours! Then you have to get a new Personal Access Token.

---
> myroom = "YOUR_ROOM_ID_HERE"

Room ID: you can find this on [Webex Teams Developer List rooms](https://developer.webex.com/endpoint-rooms-get.html), make sure you're logged in, set the 'max' parameter to '900' and click Run.
If you don't see the RUN button, make sure 'test mode' is turned on (top of page, under "Documentation")

---
> downloadfiles = no

Downloadfiles: do you want to download images or images & files? Think about it. Downloading images *and* files can significantly increase the archive time and consume disk space.  Downloaded images or files are stored in the subfolder. Options:
- "no"         : (default) no downloads, only show the text "file attachment"
- "images"  : download images only
- "files"       : download files *and* images

---
> useravatar = link

Do you want to show the user avatar or an icon? Avatars are not downloaded but *linked*. That means the script will get the user Avatar URL and use that in the HTML file. So the images are not downloaded to your hard-drive. Needs an internet connection in order to display the Avatar images. 
- "link"   : (default) link to user Avatar image.
- ""         : show avatar icon

---
> maxtotalmessages = 5000

Restrict the number of messages that are archived.  Some spaces contain 100,000 messages and you may not want to archive all of them. When configured it will archive the *last* 5000 (example) messages. 
Default: 5000

---
> outputfilename = yourfilename.html

Enter the file name of the output HTML file. If EMPTY the filename will be the same as the Archived Space name.

---
> sortoldnew = yes

Sorting of archived messages.
- "yes"   : (default) last message at the bottom (like in the Teams client)
- "no"     : latest message at the top

---


# Roadmap
* **FILE**: add date in generated html filename?
* **WEB**: make this script web-based
   * Login using Webex Teams (oAuth)
   * Select space to archive
   * Space messages are exported to an HTML file
   * User receives 1:1 message from a Bot with the HTML file attached
* ~~DATE: display in different color (easier to scan for specific day)~~
* ~~DATE: include 'day-of-week'? i.e. "monday, february 2 2016"~~
* ~~DATE: use local Date format settings? (yyyy/mm/dd vs. dd-mm-yyyy)~~
* ~~DISPLAY: reverse order of messages, from old to new?~~
* ~~ATTACHMENTS: attached? show file names~~
* ~~ATTACHMENTS: download?~~
* ~~MESSAGES: support markup text~~
* ~~MESSAGES: support retrieving >1000 messages~~
* ~~MAX: Allow configuration of maximum number of messages~~
* ~~RUN: display detailed progress when running~~
* ~~DISPLAY: Hover over user name to see the email address~~
* ~~DISPLAY: Avatar, configurable.~~
* ~~TECH: Deal with rate-limiting~~
* ~~DISPLAY: images: click to zoom in or out~~





# Troubleshooting
Most of the errors should be handles by the script. 
* **SSL Issue**: On a Mac: the default SSL is outdated & unsupported. Check out the *readme.rtf* in your Python Application folder. That folder also contains a "Install certificates.command" which should do the work for you. 





