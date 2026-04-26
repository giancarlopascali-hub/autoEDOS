import os
import time
import shutil
import threading
import logging
from flask import Flask, render_template, request, jsonify
import tkinter as tk
from tkinter import filedialog


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global state
config = {
    "folder_a": "",
    "folder_b": "",
    "folder_c": "",
    "folder_d": "",
    "tag": "USED_",
    "delay": 1.0,
    "active": False
}

logs = []

def add_log(msg):
    global logs
    timestamp = time.strftime("%H:%M:%S")
    logs.append(f"[{timestamp}] {msg}")
    if len(logs) > 100:
        logs.pop(0)
    logging.info(msg)

def monitor_loop():
    global config
    add_log("Monitor thread started.")
    
    while True:
        if not config["active"]:
            time.sleep(1)
            continue
        
        try:
            folder_a = config["folder_a"]
            folder_b = config["folder_b"]
            folder_c = config["folder_c"]
            folder_d = config["folder_d"]
            tag = config["tag"]
            delay = config["delay"]

            if not all([folder_a, folder_b, folder_c, folder_d]) or not os.path.exists(folder_a):
                time.sleep(1)
                continue

            # Check Folder A for new files (files that don't start with the tag)
            files = os.listdir(folder_a)
            new_files = [f for f in files if not f.startswith(tag) and os.path.isfile(os.path.join(folder_a, f))]

            for filename in new_files:
                if not config["active"]: break
                
                path_a = os.path.join(folder_a, filename)
                path_b = os.path.join(folder_b, filename)
                
                # 1. Copy A to B
                add_log(f"New file detected: {filename}. Copying to Folder B...")
                if not os.path.exists(folder_b):
                    os.makedirs(folder_b)
                shutil.copy2(path_a, path_b)
                
                # 2. Rename A to USED_A
                new_name_a = tag + filename
                path_a_new = os.path.join(folder_a, new_name_a)
                os.rename(path_a, path_a_new)
                add_log(f"Original file renamed to {new_name_a}")
                
                # 3. Wait delay
                add_log(f"Waiting {delay}s before next step...")
                time.sleep(delay)
                
                # 4. Copy most recent UNFLAGGED from C to D
                if os.path.exists(folder_c):
                    # Filter for files that don't start with the tag
                    files_c = [f for f in os.listdir(folder_c) if os.path.isfile(os.path.join(folder_c, f)) and not f.startswith(tag)]
                    
                    if files_c:
                        # Get most recent based on modification time
                        files_c_paths = [os.path.join(folder_c, f) for f in files_c]
                        latest_file_path = max(files_c_paths, key=os.path.getmtime)
                        latest_filename = os.path.basename(latest_file_path)
                        
                        add_log(f"Most recent unflagged file in Folder C: {latest_filename}. Copying to Folder D...")
                        if not os.path.exists(folder_d):
                            os.makedirs(folder_d)
                        shutil.copy2(latest_file_path, os.path.join(folder_d, latest_filename))
                        
                        # 5. Rename file in C to FLAG_filename
                        new_name_c = tag + latest_filename
                        path_c_new = os.path.join(folder_c, new_name_c)
                        os.rename(latest_file_path, path_c_new)
                        add_log(f"Feedback file in Folder C renamed to {new_name_c}")
                    else:
                        add_log("Warning: No unflagged files found in Folder C. Skipping copy to D.")
                else:
                    add_log(f"Warning: Folder C ({folder_c}) does not exist.")

        except Exception as e:
            add_log(f"Error in monitor loop: {str(e)}")
        
        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    global config
    if request.method == 'POST':
        data = request.json
        config["folder_a"] = data.get("folder_a", config["folder_a"])
        config["folder_b"] = data.get("folder_b", config["folder_b"])
        config["folder_c"] = data.get("folder_c", config["folder_c"])
        config["folder_d"] = data.get("folder_d", config["folder_d"])
        config["tag"] = data.get("tag", config["tag"])
        config["delay"] = float(data.get("delay", config["delay"]))
        return jsonify({"status": "success", "config": config})
    return jsonify(config)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({"active": config["active"], "logs": logs})

@app.route('/api/toggle', methods=['POST'])
def toggle_active():
    global config
    data = request.json
    config["active"] = data.get("active", not config["active"])
    status_str = "Activated" if config["active"] else "Deactivated"
    add_log(f"EQSIM {status_str}")
    return jsonify({"active": config["active"]})

@app.route('/api/browse', methods=['POST'])
def browse_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder_path = filedialog.askdirectory()
    root.destroy()
    if folder_path:
        # Normalize path for Windows
        folder_path = os.path.normpath(folder_path)
    return jsonify({"path": folder_path})

if __name__ == '__main__':
    # Start monitor thread
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()
    
    # Run server
    app.run(debug=True, port=5005)
