![alt text](infowindow.jpg)


# Infowindow
Rapsberry pi powered e-ink display for displaying information in an always on state. There are several other iterations
of this project online, but they didnt do quite what I wanted them to. This is my version. Also keeping up my python
skills as they dont get used as much as they used to!
*Please be aware that this version is built for the v2 version of the e-ink screen!*

The functionality is not meant to be an "end all solution for calendaring and Todo lists" The intent is to provide an
*always  on* display to show me what is coming up next. I can then check in browser, phone, etc for details and updates
to the data. In your face reminder.
<div align="center">
  <a href="#features">Features</a> |
  <a href="#installation">Installation</a> | 
  <a href="#configuration">Configuration</a> | 
  <a href="#running">Running</a>
</div>

## Features
* **Calendar**
  * Google Calendar
  * CalDAV Calendar (added for Nextcloud support)
* **Todo List**
  * Todoist
  * Teamwork.com
  * CalDAV Todos (added for Nextcloud support)
* **Weather**
  * Open Weather Map current data only. Future plan for forecast data.

## Installation
### Raspberry Pi setup
Activate SPI on your Raspberry Pi by using the `raspi-config` tool under Interface Options and reboot.

Also for some RaspiOS versions, you have to install the `libopenjp2-7` package: 
```bash
sudo apt-get install libopenjp2-7 libxslt1
```

### Get software
Clone this repo onto your raspberry pi. Does not really matter where it is, but good option is in the `pi` users home
directory: `/home/pi/InfoWindow`

### Clone the e-Paper driver from waveshare
Waveshare sometimes changes things in their driver. So this part might need some changes, be aware!
```bash
git clone https://github.com/waveshareteam/e-Paper.git /home/pi/e-Paper
ln -s /home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/ /home/pi/InfoWindow/driver
```

### Setup python modules
Run the following commands to install the requirements. I stuck to basic standard modules for
ease of installation.
```bash
cd /home/pi/InfoWindow
export CFLAGS=-fcommon
sudo apt install python3-dev
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

## Configuration
You will need to configure a few things such as API Keys and location. Copy config.json-sample to config.json. Edit
config.json to add your api keys and other information.

## Optional: Increase lifetime of your SD-Card
If you want to increase the lifetime of the SD-Card, add the following line to `/etc/fstab` and reboot: 

`tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0`

With this line, the `/tmp` folder will be held in RAM and will not be written to the SD-Card.

## Optional: Screen saver 
Always displaying the same colors at the same spots might have some negative effect on your E-Ink screen. To remedy
this, there is a simple additional script, which displays all three colors on the whole screen: I recommend to let
this run once every night, i.e. at 1 minute past 5 with:
* Run `crontab -e`
* insert `1   5 * * * /home/pi/InfoWindow/venv/bin/python3 /home/pi/InfoWindow/screensaver.py > /dev/null 2>&1`

### General
* rotation: 0 - This is the rotation of the display in degrees. Leave at zero if you use it as a desktop display. Change
to 180 if you have it mounted and hanging from a shelf.
* timeformat: 12h / 24h

### Todo (Module)
Todoist is the current active module in this code. It only requires `api_key`. Teamwork also requires a 'site' key. If
using google tasks, leave this as null `todo: null`
* api_key: Enter your todoist API key.

There is a bug in the Google API which will prevent to show repeated Tasks once one is marked as completed. See (and
upvote): 
* https://support.google.com/calendar/thread/3706294
* https://support.google.com/calendar/thread/4113489
* https://support.google.com/calendar/thread/111623199
* https://support.google.com/calendar/thread/113398139

### Weather (Module)
Open Weather Map is where the data is coming from in the default module. This requires a few keys.
* api_key: Get your api key from OWM website.
* city: Look at OWM docs to figure what your city name is. Mine is "Sacramento,US"
* units: This can either be `imperial` or `metric`

### Google calendar and ToDo list (Modules)
To use the google APIs, you first have to login to the [google cloud console](https://console.cloud.google.com/apis/).
In the google cloud console, do the following things:
1) Create a project and give it a name, i.e. `infowindow` and switch to the context of this project if not already
   active.
2) Create a [new oauth consent screen](https://console.cloud.google.com/apis/credentials/consent) (just enter a name
   should be enough).
3) Create a [new oauth 2.0 client id](https://console.cloud.google.com/apis/credentials). Choosing type `other` should
   work just fine. Finally, download the json file provided by the google cloud console and store it in the repo
   directory (i.e. `/home/pi/InfoWindow/google_secret.json`) on the Raspberry Pi.  

### CalDAV calendar and ToDo list (Modules)
To use CalDAV, configure the corresponding modules in the `config.json`. If you use a Nextcloud server, you can
find the CalDAV URL in the settings of your calendar. As a example (where `USERNAME` is you username):
`https://cloud.domain.tld/remote.php/dav/calendars/USERNAME`

#### Calendar
There are are additional sections in the config for this module:
* additional: A list of additional calendar names (summary) to fetch. To use i.e. birthdays, add "Contacts" (also if
              you use google in german.
* ignored: A list of events to be removed from the calendar display.
        
## Running
### First Run
You should run the script manually the first time so that Googles auth modules can run interactivly. Once that has
completed you will want to add this to CRON so it runs every few minutes automatically.

### Cron Run (Normal use)
* Run `crontab -e`
* insert `*/6 * * * * /home/pi/InfoWindow/venv/bin/python3 /home/pi/InfoWindow/infowindow.py --cron > /dev/null 2>&1` 
