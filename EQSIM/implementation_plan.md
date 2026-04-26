# EQSIM Implementation Plan

EQSIM is a standalone folder monitoring and file simulation tool designed to automate data transfer between equipment folders.

## Features
- **Real-time Monitoring**: Watches Folder A for new files.
- **Automated Processing**:
  1. Detects new file in A.
  2. Copies file to Folder B.
  3. Renames original file in A with a prefix (default: `USED_`).
  4. Waits for a configurable delay (default: 1s).
  5. Finds the most recent file in Folder C and copies it to Folder D.
- **Configurable UI**: Modern, glassmorphism-style dashboard to select folders, tags, and delays.
- **Control**: Easy Activate/Deactivate toggle with live operation logs.

## Architecture
- **Backend (Python/Flask)**: Handles file system operations and status polling.
- **Frontend (Vanilla HTML/CSS/JS)**: Clean, responsive UI with a premium dark-mode aesthetic.
- **Threading**: Monitoring runs in a background thread to keep the UI responsive.

## File Structure
- `app.py`: Main Flask application and monitoring logic.
- `templates/index.html`: UI structure.
- `static/style.css`: Premium styling (Glassmorphism).
- `static/script.js`: UI logic and API interaction.
