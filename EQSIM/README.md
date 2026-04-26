# EQSIM - Equipment Simulator

EQSIM is an automated folder monitoring tool designed to simulate equipment data workflows.

## Features
- **Folder A -> B**: Detects new files, copies them to Folder B.
- **Auto-Rename**: Flags processed files in Folder A with a prefix (default `USED_`).
- **Delayed Feedback**: Copies the latest file from Folder C to Folder D after a set delay.
- **Premium UI**: Modern dark-mode dashboard with real-time logs.

## Setup
1. Ensure Python is installed.
2. Run the app:
   - Double-click `run_EQSIM.bat`
   - Or run `python gui.py`
3. The native application window will open automatically.

## Configuration
- **Folder A**: Source folder to watch for new files.
- **Folder B**: Destination for the new files.
- **Folder C**: Source for feedback files (monitors for most recent).
- **Folder D**: Destination for feedback files.
- **Tag**: The prefix added to processed files in Folder A.
- **Delay**: Wait time (seconds) between processing Folder A and copying from Folder C.

## Build Standalone EXE
To create a single executable, install PyInstaller:
```bash
pip install pyinstaller
```
Then run:
```bash
pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" app.py
```
The `.exe` will be in the `dist` folder.
