# ping-menubar

A minimal macOS menubar app that displays real-time ping times as a compact visualization.

<div style="display: flex; gap: 10px;">
  <img src="sc.png" />
</div>

### Configuration options
```
PING_HOST = "1.1.1.1"
PING_INTERVAL = 2.0  # seconds
PING_SAMPLES = 16    # number of readings to show
PING_WAIT = 1000     # ping -W value in ms

# Ping time ranges and colors (RGB)
TIERS = [
    {"limit": 0, "color": NSColor.colorWithRed_green_blue_alpha_(0, 0, 0, 1.0)},
    {"limit": 70, "color": NSColor.colorWithRed_green_blue_alpha_(13/255, 215/255, 33/255, 1.0)},
    {"limit": 150, "color": NSColor.colorWithRed_green_blue_alpha_(209/255, 214/255, 39/255, 1.0)},
    {"limit": 300, "color": NSColor.colorWithRed_green_blue_alpha_(209/255, 15/255, 29/255, 1.0)},
]

BAR_WIDTH = 3
BAR_HEIGHT = 18
```

## Installation Options

### Quick Start (Run from Python)
```bash
# Optional: Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run directly
python ping-menubar.py
```

### Install as App (required to launch at login)
```bash
# Install build dependencies
pip install -r requirements.txt
pip install setuptools==70.3.0
pip install py2app

# Build app
python3 setup.py py2app

# Copy to Applications
cp -r "dist/ping-menubar.app" /Applications/
```

### Create dmg for distribution
```bash
# Install create-dmg
brew install create-dmg

# Build dmg
rm ping-menubar.dmg; create-dmg \
  --volname "Ping Menubar" \
  --window-size 400 160 \
  --icon-size 50 \
  --app-drop-link 270 100 \
  --icon "ping-menubar.app" 90 100 \
  "ping-menubar.dmg" dist
```
