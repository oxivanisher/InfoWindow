![InfoWindow on a shelf](infowindow.jpg)

# InfoWindow

Raspberry Pi powered e-ink display showing calendar, todo items and weather in an always-on state.
Built for the **Waveshare 7.5" V2 three-colour (black/red/white)** e-ink display.

The goal is not a full-featured PIM — it is an *in your face* reminder of what is coming up next.
Details stay in your calendar app, phone, or browser.

<div align="center">
  <a href="#features">Features</a> |
  <a href="#hardware-setup">Hardware</a> |
  <a href="#installation">Installation</a> |
  <a href="#configuration">Configuration</a> |
  <a href="#running">Running</a> |
  <a href="#local-development">Local development</a>
</div>

---

## Features

| Area | Backends |
|---|---|
| **Calendar** | Google Calendar, CalDAV (Nextcloud etc.) |
| **Todo** | Google Tasks, CalDAV (Nextcloud etc.), Teamwork |
| **Weather** | OpenWeatherMap (current conditions) |

Multiple backends can be enabled simultaneously — results are merged and sorted.

---

## Hardware setup

### Enable SPI
```bash
sudo raspi-config   # Interface Options → SPI → Enable
sudo reboot
```

### System packages
```bash
sudo apt install python3-dev libopenjp2-7 libxslt1.1
```

### Clone this repo
```bash
git clone https://github.com/oxivanisher/InfoWindow.git /home/pi/InfoWindow
```

### Clone the Waveshare e-Paper driver
The driver is not bundled — clone it separately and symlink it into the project.
Waveshare occasionally restructures their repo, so the path may need adjusting.
```bash
git clone https://github.com/waveshareteam/e-Paper.git /home/pi/e-Paper
ln -s /home/pi/e-Paper/RaspberryPi_JetsonNano/python/lib/waveshare_epd/ \
      /home/pi/InfoWindow/driver
```

---

## Installation

```bash
cd /home/pi/InfoWindow
python3 -m venv venv
source venv/bin/activate
pip install -e ".[rpi,google,caldav]"
```

Install only the extras you need:

| Extra | Installs |
|---|---|
| `rpi` | Raspberry Pi GPIO libraries (required on Pi) |
| `google` | Google Calendar / Tasks API client |
| `caldav` | CalDAV client (Nextcloud, etc.) |
| `todoist` | Todoist stub *(v8 API discontinued — not functional)* |

---

## Configuration

Copy the sample and fill in your details:
```bash
cp config.json-sample config.json
```

### General
| Key | Values | Description |
|---|---|---|
| `rotation` | `0` / `180` | `0` for desktop use, `180` if mounted hanging from a shelf |
| `timeformat` | `12h` / `24h` | Clock format used throughout |
| `sunday_first_dow` | `true` / `false` | Week start day for calendar grouping |
| `cell_spacing` | integer | Pixel padding inside cells |
| `timezone` | e.g. `Europe/Zurich` | Local timezone |

### Weather — OpenWeatherMap
```json
"weather": {
    "api_key": "your-owm-key",
    "city": "Zurich,CH",
    "units": "metric"
}
```
`units` accepts `metric`, `imperial`, or `standard` (Kelvin).

### Google Calendar and Tasks

1. Go to the [Google Cloud Console](https://console.cloud.google.com/apis/).
2. Create a project (e.g. `infowindow`).
3. Create an [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).
4. Create an [OAuth 2.0 client ID](https://console.cloud.google.com/apis/credentials) (type: *Desktop app*).
5. Download the JSON file and save it as `google_secret.json` in the project directory.

Enable the backends in `config.json`:
```json
"calendar_google": { "enabled": true, "additional": ["Contacts", "Birthdays"] },
"todo_google":     { "enabled": true }
```

> **Note:** There is a known Google API bug where repeated tasks stop appearing once one
> instance is marked complete. See the [Google support thread](https://support.google.com/calendar/thread/3706294).

### CalDAV (Nextcloud etc.)

For Nextcloud the CalDAV URL is usually:
`https://cloud.example.com/remote.php/dav/calendars/USERNAME`

```json
"calendar_caldav": {
    "enabled": true,
    "caldav_url": "https://cloud.example.com/remote.php/dav/calendars/USERNAME",
    "username": "john",
    "password": "secret",
    "additional": ["Personal", "Birthdays"]
},
"todo_caldav": {
    "enabled": true,
    "caldav_url": "https://cloud.example.com/remote.php/dav/calendars/USERNAME",
    "username": "john",
    "password": "secret",
    "additional": ["Tasks"]
}
```

`additional` is a list of calendar names to include. Leave it empty (`[]`) to include all.

`ignored` (under `calendar`) is a list of event titles to suppress from the display.

---

## Running

### First run — Google authentication
If you use Google backends, run the script **manually once** so the OAuth flow can open
interactively and save a token:
```bash
source venv/bin/activate
python infowindow.py
```

Subsequent runs use the saved `token.pickle` and refresh it automatically.

### systemd (recommended)

The `dist/` directory contains ready-to-use systemd units.
Link them into place — no need to copy, so pulling updates keeps them current:

```bash
sudo ln -s /home/pi/InfoWindow/dist/infowindow.service          /etc/systemd/system/
sudo ln -s /home/pi/InfoWindow/dist/infowindow.timer            /etc/systemd/system/
sudo ln -s /home/pi/InfoWindow/dist/infowindow-screensaver.service /etc/systemd/system/
sudo ln -s /home/pi/InfoWindow/dist/infowindow-screensaver.timer   /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now infowindow.timer
sudo systemctl enable --now infowindow-screensaver.timer
```

> **Note:** The service files currently hardcode `User=pi`. Adjust if your username differs.

The **updater** runs every 6 minutes. The **screensaver** runs once daily at 05:01 to cycle
the display through black, red, and white — preventing image retention.

#### Useful commands
```bash
journalctl -u infowindow -f          # live logs from the updater
journalctl -u infowindow-screensaver # screensaver logs
systemctl status infowindow.timer    # next scheduled run
```

---

## Optional: extend SD-card lifetime

Add this line to `/etc/fstab` and reboot to keep `/tmp` in RAM:
```
tmpfs    /tmp    tmpfs    defaults,noatime,nosuid,size=100m    0 0
```

---

## Local development

The display driver is not available outside a Raspberry Pi, but a **mock display**
activates automatically on any other machine. It composites the black and red layers
into a colour preview PNG and opens it with your default image viewer.

```bash
# One-time setup (no rpi extra needed)
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[google,caldav]"

# Run
python infowindow.py
# → preview saved to /tmp/InfoWindowPreview.png
```

The mock faithfully reproduces the Waveshare rendering rules: red wins over black when
both layers have ink at the same pixel.
