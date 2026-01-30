# RL Deminimizer

Bring Rocket League to the front the moment a match starts. RL Deminimizer monitors the Rocket League log file and automatically restores the game window when a server reserves your slot or when loading begins.

## Quick Start (Recommended - No Python required)

Download the latest standalone Windows executable from the [Releases page](https://github.com/YellowGTO/RL-Deminimizer/releases/latest).

1. Download `RL-Deminimizer.exe` (or the versioned file shown in the release).
2. Run the executable directly — no installation needed.

## Features
- Detects match start from the Rocket League `Launch.log` file.
- Restores and focuses the Rocket League window if it's minimized.
- Simple Tkinter UI with start/stop monitoring.
- Optional "start with Windows" autostart.
- Shows time since the last match detection.

## Requirements
- Windows
- Python 3.10+ recommended
- Rocket League installed and launched at least once
- Python packages:
  - `pygetwindow`

## Install
1. Create/activate a virtual environment (optional but recommended).
2. Install dependencies:

```powershell
pip install pygetwindow
```

## Run
```powershell
python RLjoin.py
```

You should see a small window titled **RL Deminimizer**. Leave it running while you queue into matches.

## How it works
RL Deminimizer tails Rocket League's log file and watches for these triggers:
- `ReserveConnection` (earliest match signal)
- `Travel to` (backup trigger)

When a trigger appears, the app attempts to restore and focus the Rocket League window.

## Autostart
Enable **Start with Windows** in the UI to create an autostart script in your Windows Startup folder. Disable it to remove the script.

## Configuration
These settings are defined at the top of `RLjoin.py`:
- `LOG_PATH`: location of Rocket League's `Launch.log`
- `TRIGGERS`: list of log strings that indicate a match is starting

## Troubleshooting
- **Log file not found**: Make sure Rocket League has been launched at least once. The log should exist at:
  - `C:\Users\<you>\Documents\My Games\Rocket League\TAGame\Logs\Launch.log`
- **Window not restored**: Ensure the Rocket League window title contains "Rocket League" and the game is running.
- **Nothing happens**: Check that monitoring is **On** and that new log lines are being written (queue into a match to test).

## Notes
- This app only brings the window to the front if it is minimized.
- It does not join matches automatically; it only restores focus when a match is detected.
