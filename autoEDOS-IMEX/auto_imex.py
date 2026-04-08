import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import serial
import serial.tools.list_ports
import threading
import time
import json
import csv
import io
import os
import socket
from datetime import datetime

class AutoEDOSIMEX:
    def __init__(self, root):
        self.root = root
        self.root.title("autoEDOS-IMEX | Multi-Bridge")
        self.root.geometry("750x750")
        self.root.configure(bg="#f3f4f6")

        self.running = False
        self.api_url = tk.StringVar(value="http://localhost:5000")
        
        # Mode State
        self.mode = tk.StringVar(value="folder")
        
        # 1. Folder Mode State
        self.import_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "autoEDOS_IMPORT"))
        self.export_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "autoEDOS_EXPORT"))

        # 2. Serial State
        self.com_send = tk.StringVar(value="COM100")
        self.com_recv = tk.StringVar(value="COM101")
        self.baud_rate = tk.StringVar(value="9600")
        
        # 3. Network State
        self.net_ip = tk.StringVar(value="127.0.0.1")
        self.net_port_send = tk.StringVar(value="8888")
        self.net_port_recv = tk.StringVar(value="8889")
        self.net_protocol = tk.StringVar(value="TCP")

        # 4. USB State (Generic parameters)
        self.usb_vid = tk.StringVar(value="0x0483")
        self.usb_pid = tk.StringVar(value="0x5740")

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#9d174d", height=80)
        header.pack(fill="x")
        tk.Label(header, text="autoEDOS-IMEX", font=("Inter", 18, "bold"), fg="white", bg="#9d174d").pack(pady=10)
        tk.Label(header, text="Unified Hardware Bridge Engine", font=("Inter", 10), fg="#fbcfe8", bg="#9d174d").pack()

        # Global Config
        glb_frame = tk.LabelFrame(self.root, text="autoEDOS Connection", padx=15, pady=10, bg="white", font=("Inter", 9, "bold"))
        glb_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(glb_frame, text="autoEDOS URL:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(glb_frame, textvariable=self.api_url, width=45).grid(row=0, column=1, padx=10)

        # Mode Selection
        mode_frame = tk.LabelFrame(self.root, text="Select Peripheral Bridge Mode", bg="#f3f4f6", padx=10, pady=10)
        mode_frame.pack(fill="x", padx=20, pady=5)
        modes = [("Local Folder", "folder"), ("Serial (COM)", "serial"), ("Network (TCP/UDP)", "network"), ("USB (Direct)", "usb")]
        for text, m in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode, value=m, bg="#f3f4f6").pack(side="left", padx=12)

        # Notebook for Mode-Specific Settings
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=20, pady=10)

        # Tab 1: Folder
        folder_tab = tk.Frame(self.tabs, bg="white", padx=15, pady=15)
        self.tabs.add(folder_tab, text=" Folder Settings ")
        self.add_folder_ui(folder_tab)

        # Tab 2: Serial
        serial_tab = tk.Frame(self.tabs, bg="white", padx=15, pady=15)
        self.tabs.add(serial_tab, text=" Serial (COM) ")
        self.add_serial_ui(serial_tab)

        # Tab 3: Network
        net_tab = tk.Frame(self.tabs, bg="white", padx=15, pady=15)
        self.tabs.add(net_tab, text=" Network (I/O) ")
        self.add_network_ui(net_tab)

        # Tab 4: USB
        usb_tab = tk.Frame(self.tabs, bg="white", padx=15, pady=15)
        self.tabs.add(usb_tab, text=" USB (Direct) ")
        self.add_usb_ui(usb_tab)

        # Control
        self.btn_toggle = tk.Button(self.root, text="START BRIDGE SERVICE", command=self.toggle_bridge, 
                                    bg="#10b981", fg="white", font=("Inter", 12, "bold"), 
                                    padx=20, pady=12, borderwidth=0)
        self.btn_toggle.pack(pady=10)

        # Log
        log_frame = tk.LabelFrame(self.root, text="System Activity Log", padx=10, pady=10, bg="white")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_text = tk.Text(log_frame, height=8, font=("Consolas", 8), state="disabled")
        self.log_text.pack(fill="both", expand=True)

    def add_folder_ui(self, parent):
        tk.Label(parent, text="IMPORT Folder (Write Proposals):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.import_path, width=40).grid(row=1, column=0, pady=5)
        tk.Button(parent, text="Browse", command=lambda: self.browse_folder(self.import_path)).grid(row=1, column=1, padx=5)
        
        tk.Label(parent, text="EXPORT Folder (Read Results):", bg="white").grid(row=2, column=0, sticky="w", pady=(10,0))
        tk.Entry(parent, textvariable=self.export_path, width=40).grid(row=3, column=0, pady=5)
        tk.Button(parent, text="Browse", command=lambda: self.browse_folder(self.export_path)).grid(row=3, column=1, padx=5)

    def add_serial_ui(self, parent):
        tk.Label(parent, text="COM Send Port:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.com_send).grid(row=0, column=1, pady=5)
        
        tk.Label(parent, text="COM Recv Port:", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.com_recv).grid(row=1, column=1, pady=5)
        
        tk.Label(parent, text="Baud Rate (Speed):", bg="white").grid(row=2, column=0, sticky="w")
        bauds = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        ttk.Combobox(parent, textvariable=self.baud_rate, values=bauds, width=17).grid(row=2, column=1, pady=5)

    def add_network_ui(self, parent):
        tk.Label(parent, text="Target IP / Hostname:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.net_ip).grid(row=0, column=1, pady=5)
        
        tk.Label(parent, text="Port (Send proposals):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.net_port_send).grid(row=1, column=1, pady=5)

        tk.Label(parent, text="Port (Wait for results):", bg="white").grid(row=2, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.net_port_recv).grid(row=2, column=1, pady=5)

        tk.Label(parent, text="Protocol:", bg="white").grid(row=3, column=0, sticky="w")
        ttk.Combobox(parent, textvariable=self.net_protocol, values=["TCP", "UDP"], width=17).grid(row=3, column=1, pady=5)

    def add_usb_ui(self, parent):
        tk.Label(parent, text="Vendor ID (VID):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.usb_vid).grid(row=0, column=1, pady=5)
        
        tk.Label(parent, text="Product ID (PID):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(parent, textvariable=self.usb_pid).grid(row=1, column=1, pady=5)
        
        tk.Label(parent, text="Communication Driver:", bg="white").grid(row=2, column=0, sticky="w")
        tk.Label(parent, text="Generic HID / WinUSB", bg="white", fg="gray").grid(row=2, column=1, pady=5, sticky="w")

    def browse_folder(self, var):
        path = filedialog.askdirectory()
        if path: var.set(path)

    def log(self, message, mtype="INFO"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{mtype}] {time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def toggle_bridge(self):
        if not self.running: self.start_bridge()
        else: self.stop_bridge()

    def start_bridge(self):
        self.running = True
        self.btn_toggle.config(text="STOP BRIDGE SERVICE", bg="#ef4444")
        self.log(f"Service started. Bridging autoEDOS -> {self.mode.get().upper()} hardware.")
        threading.Thread(target=self.bridge_loop, daemon=True).start()

    def stop_bridge(self):
        self.running = False
        self.btn_toggle.config(text="START BRIDGE SERVICE", bg="#10b981")
        self.log("Service stopped.")

    def bridge_loop(self):
        while self.running:
            try:
                # 1. Pull from Server
                self.check_for_proposals()
                
                # 2. Poll hardware for results
                mode = self.mode.get()
                if mode == "folder": self.check_local_exports()
                elif mode == "network": self.check_network_input()
                elif mode == "serial": self.check_serial_input()
                elif mode == "usb": self.check_usb_input()

            except Exception as e:
                self.log(str(e), "ERR")
            time.sleep(5)

    def check_for_proposals(self):
        base_url = self.api_url.get().rstrip('/')
        try:
            resp = requests.get(f"{base_url}/auto/proposal", timeout=3)
            if resp.status_code == 200:
                p = resp.json()
                self.log(f"Prop collected from server ({p.get('iteration')})")
                self.dispatch_to_hardware(p)
        except: pass

    def dispatch_to_hardware(self, proposal):
        mode = self.mode.get()
        if mode == "folder": self.save_proposal_to_folder(proposal)
        elif mode == "serial": self.send_to_serial(proposal)
        elif mode == "network": self.send_to_network(proposal)
        elif mode == "usb": self.send_to_usb(proposal)

    # --- MODE IMPLEMENTATIONS (Stubs/Basics) ---

    def save_proposal_to_folder(self, proposal):
        fname = f"Proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fpath = os.path.join(self.import_path.get(), fname)
        if not os.path.exists(self.import_path.get()): os.makedirs(self.import_path.get())
        with open(fpath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=proposal['features_only'][0].keys())
            writer.writeheader()
            writer.writerows(proposal['features_only'])
        self.log(f"Saved: {fname}")

    def send_to_serial(self, proposal):
        # Implementation using self.baud_rate.get()
        self.log(f"Sent via COM {self.com_send.get()} @ {self.baud_rate.get()} baud")

    def check_serial_input(self):
        # Poll COM recv port
        pass

    def send_to_network(self, proposal):
        try:
            msg = json.dumps(proposal).encode()
            if self.net_protocol.get() == "TCP":
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((self.net_ip.get(), int(self.net_port_send.get())))
                    s.sendall(msg)
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(msg, (self.net_ip.get(), int(self.net_port_send.get())))
            self.log(f"Network Send: Success to {self.net_ip.get()}:{self.net_port_send.get()}")
        except Exception as e:
            self.log(f"Network Send Error: {e}", "ERR")

    def check_network_input(self):
        # Create a listener for result packets on self.net_port_recv
        pass

    def send_to_usb(self, proposal):
        self.log(f"USB Direct Send: (VID:{self.usb_vid.get()} PID:{self.usb_pid.get()}) - Data queued.")

    def check_usb_input(self):
        pass

    def check_local_exports(self):
        path = self.export_path.get()
        if not os.path.exists(path): return
        for fname in os.listdir(path):
            if fname.endswith('.csv') and not fname.startswith('SENT_'):
                with open(os.path.join(path, fname), 'r') as f:
                    data = [r for r in csv.DictReader(f)]
                if self.push_results_to_server(data):
                    os.rename(os.path.join(path, fname), os.path.join(path, "SENT_" + fname))
                    self.log(f"Result Sync: {fname}")

    def push_results_to_server(self, data):
        try:
            resp = requests.post(f"{self.api_url.get().rstrip('/')}/auto/results", json=data, timeout=5)
            return resp.status_code == 200
        except: return False

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    AutoEDOSIMEX(root)
    root.mainloop()
