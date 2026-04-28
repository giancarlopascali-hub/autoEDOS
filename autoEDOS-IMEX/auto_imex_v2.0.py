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

class AutoEDOSIMEX_v2:
    def __init__(self, root):
        self.root = root
        self.root.title("autoEDOS-IMEX v2.0 | Multi-Bridge")
        self.root.geometry("800x850")
        self.root.configure(bg="#f3f4f6")

        self.running = False
        self.api_url = tk.StringVar(value="http://localhost:5000")
        
        # Hardware Control State (Sends Proposals)
        self.hw_mode = tk.StringVar(value="folder")
        self.hw_import_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "autoEDOS_IMPORT"))
        self.hw_com_send = tk.StringVar(value="COM100")
        self.hw_baud_rate = tk.StringVar(value="9600")
        self.hw_net_ip = tk.StringVar(value="127.0.0.1")
        self.hw_net_port_send = tk.StringVar(value="8888")
        self.hw_net_protocol = tk.StringVar(value="TCP")
        self.hw_usb_vid = tk.StringVar(value="0x0483")
        self.hw_usb_pid = tk.StringVar(value="0x5740")

        # Analytics Readout State (Receives Results)
        self.ar_mode = tk.StringVar(value="folder")
        self.ar_export_path = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "autoEDOS_EXPORT"))
        self.ar_com_recv = tk.StringVar(value="COM101")
        self.ar_baud_rate = tk.StringVar(value="9600")
        self.ar_net_ip = tk.StringVar(value="127.0.0.1")
        self.ar_net_port_recv = tk.StringVar(value="8889")
        self.ar_net_protocol = tk.StringVar(value="TCP")
        self.ar_usb_vid = tk.StringVar(value="0x0483")
        self.ar_usb_pid = tk.StringVar(value="0x5740")

        self.hw_mode.trace_add("write", self.update_graphic)
        self.ar_mode.trace_add("write", self.update_graphic)

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#9d174d", height=80)
        header.pack(fill="x")
        tk.Label(header, text="autoEDOS-IMEX v2.0", font=("Inter", 18, "bold"), fg="white", bg="#9d174d").pack(pady=10)
        tk.Label(header, text="Unified Hardware Bridge Engine", font=("Inter", 10), fg="#fbcfe8", bg="#9d174d").pack()

        # Global Config
        glb_frame = tk.LabelFrame(self.root, text="autoEDOS Connection", padx=15, pady=10, bg="white", font=("Inter", 9, "bold"))
        glb_frame.pack(fill="x", padx=20, pady=10)
        tk.Label(glb_frame, text="autoEDOS URL:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(glb_frame, textvariable=self.api_url, width=45).grid(row=0, column=1, padx=10)

        # Macro Tabs
        self.macro_tabs = ttk.Notebook(self.root)
        self.macro_tabs.pack(fill="x", padx=20, pady=5)

        # Hardware Control Tab
        hw_frame = tk.Frame(self.macro_tabs, bg="white", padx=15, pady=15)
        self.macro_tabs.add(hw_frame, text=" Hardware Control ")
        self.setup_hw_tab(hw_frame)

        # Analytics Readout Tab
        ar_frame = tk.Frame(self.macro_tabs, bg="white", padx=15, pady=15)
        self.macro_tabs.add(ar_frame, text=" Analytics Readout ")
        self.setup_ar_tab(ar_frame)

        # Graphic Canvas
        self.canvas = tk.Canvas(self.root, height=120, bg="#f3f4f6", highlightthickness=0)
        self.canvas.pack(fill="x", padx=20, pady=5)
        self.update_graphic()

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

    def setup_hw_tab(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Select Peripheral Bridge Mode (Write Proposals)", bg="white", padx=10, pady=10)
        mode_frame.pack(fill="x", pady=(0, 10))
        modes = [("Local Folder", "folder"), ("Serial (COM)", "serial"), ("Network (TCP/UDP)", "network"), ("USB (Direct)", "usb")]
        for text, m in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.hw_mode, value=m, bg="white", command=self.update_hw_panels).pack(side="left", padx=10)

        self.hw_panels = tk.Frame(parent, bg="white")
        self.hw_panels.pack(fill="x")
        
        self.hw_folder_frame = tk.Frame(self.hw_panels, bg="white")
        tk.Label(self.hw_folder_frame, text="IMPORT Folder (Write Proposals):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.hw_folder_frame, textvariable=self.hw_import_path, width=40).grid(row=1, column=0, pady=5)
        tk.Button(self.hw_folder_frame, text="Browse", command=lambda: self.browse_folder(self.hw_import_path)).grid(row=1, column=1, padx=5)

        self.hw_serial_frame = tk.Frame(self.hw_panels, bg="white")
        tk.Label(self.hw_serial_frame, text="COM Send Port:", bg="white").grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(self.hw_serial_frame, textvariable=self.hw_com_send, values=[p.device for p in serial.tools.list_ports.comports()])
        cb.grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.hw_serial_frame, text="Baud Rate:", bg="white").grid(row=1, column=0, sticky="w")
        ttk.Combobox(self.hw_serial_frame, textvariable=self.hw_baud_rate, values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]).grid(row=1, column=1, pady=5, padx=5)

        self.hw_network_frame = tk.Frame(self.hw_panels, bg="white")
        tk.Label(self.hw_network_frame, text="Target IP / Hostname:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.hw_network_frame, textvariable=self.hw_net_ip).grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.hw_network_frame, text="Port (Send proposals):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(self.hw_network_frame, textvariable=self.hw_net_port_send).grid(row=1, column=1, pady=5, padx=5)
        tk.Label(self.hw_network_frame, text="Protocol:", bg="white").grid(row=2, column=0, sticky="w")
        ttk.Combobox(self.hw_network_frame, textvariable=self.hw_net_protocol, values=["TCP", "UDP"]).grid(row=2, column=1, pady=5, padx=5)

        self.hw_usb_frame = tk.Frame(self.hw_panels, bg="white")
        tk.Label(self.hw_usb_frame, text="Vendor ID (VID):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.hw_usb_frame, textvariable=self.hw_usb_vid).grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.hw_usb_frame, text="Product ID (PID):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(self.hw_usb_frame, textvariable=self.hw_usb_pid).grid(row=1, column=1, pady=5, padx=5)

        self.update_hw_panels()

    def setup_ar_tab(self, parent):
        mode_frame = tk.LabelFrame(parent, text="Select Peripheral Bridge Mode (Read Results)", bg="white", padx=10, pady=10)
        mode_frame.pack(fill="x", pady=(0, 10))
        modes = [("Local Folder", "folder"), ("Serial (COM)", "serial"), ("Network (TCP/UDP)", "network"), ("USB (Direct)", "usb")]
        for text, m in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.ar_mode, value=m, bg="white", command=self.update_ar_panels).pack(side="left", padx=10)

        self.ar_panels = tk.Frame(parent, bg="white")
        self.ar_panels.pack(fill="x")
        
        self.ar_folder_frame = tk.Frame(self.ar_panels, bg="white")
        tk.Label(self.ar_folder_frame, text="EXPORT Folder (Read Results):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.ar_folder_frame, textvariable=self.ar_export_path, width=40).grid(row=1, column=0, pady=5)
        tk.Button(self.ar_folder_frame, text="Browse", command=lambda: self.browse_folder(self.ar_export_path)).grid(row=1, column=1, padx=5)

        self.ar_serial_frame = tk.Frame(self.ar_panels, bg="white")
        tk.Label(self.ar_serial_frame, text="COM Recv Port:", bg="white").grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(self.ar_serial_frame, textvariable=self.ar_com_recv, values=[p.device for p in serial.tools.list_ports.comports()])
        cb.grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.ar_serial_frame, text="Baud Rate:", bg="white").grid(row=1, column=0, sticky="w")
        ttk.Combobox(self.ar_serial_frame, textvariable=self.ar_baud_rate, values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]).grid(row=1, column=1, pady=5, padx=5)

        self.ar_network_frame = tk.Frame(self.ar_panels, bg="white")
        tk.Label(self.ar_network_frame, text="Target IP / Hostname:", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.ar_network_frame, textvariable=self.ar_net_ip).grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.ar_network_frame, text="Port (Wait for results):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(self.ar_network_frame, textvariable=self.ar_net_port_recv).grid(row=1, column=1, pady=5, padx=5)
        tk.Label(self.ar_network_frame, text="Protocol:", bg="white").grid(row=2, column=0, sticky="w")
        ttk.Combobox(self.ar_network_frame, textvariable=self.ar_net_protocol, values=["TCP", "UDP"]).grid(row=2, column=1, pady=5, padx=5)

        self.ar_usb_frame = tk.Frame(self.ar_panels, bg="white")
        tk.Label(self.ar_usb_frame, text="Vendor ID (VID):", bg="white").grid(row=0, column=0, sticky="w")
        tk.Entry(self.ar_usb_frame, textvariable=self.ar_usb_vid).grid(row=0, column=1, pady=5, padx=5)
        tk.Label(self.ar_usb_frame, text="Product ID (PID):", bg="white").grid(row=1, column=0, sticky="w")
        tk.Entry(self.ar_usb_frame, textvariable=self.ar_usb_pid).grid(row=1, column=1, pady=5, padx=5)

        self.update_ar_panels()

    def update_hw_panels(self):
        for w in self.hw_panels.winfo_children(): w.pack_forget()
        m = self.hw_mode.get()
        if m == "folder": self.hw_folder_frame.pack(fill="x")
        elif m == "serial": self.hw_serial_frame.pack(fill="x")
        elif m == "network": self.hw_network_frame.pack(fill="x")
        elif m == "usb": self.hw_usb_frame.pack(fill="x")

    def update_ar_panels(self):
        for w in self.ar_panels.winfo_children(): w.pack_forget()
        m = self.ar_mode.get()
        if m == "folder": self.ar_folder_frame.pack(fill="x")
        elif m == "serial": self.ar_serial_frame.pack(fill="x")
        elif m == "network": self.ar_network_frame.pack(fill="x")
        elif m == "usb": self.ar_usb_frame.pack(fill="x")

    def update_graphic(self, *args):
        try:
            self.canvas.delete("all")
        except AttributeError:
            return
            
        bg_color = "#fbcfe8" 
        border_color = "#9d174d"
        text_color = "#4c1d95"
        
        # Space centers across a ~760px width for better spacing
        boxes = [
            (80, "🖥️ autoEDOS", "Sends Proposals", "#e0e7ff"),
            (280, "⚙️ Hardware", "Performs Operation", "#dcfce7"),
            (480, "📈 Analytics", "Analyzes Process", "#fef9c3"),
            (680, "🖥️ autoEDOS", "Receives Results", "#e0e7ff")
        ]
        
        for x, title, sub, color in boxes:
            # width 130px -> from x-65 to x+65
            self.canvas.create_rectangle(x-65, 30, x+65, 90, fill=color, outline=border_color, width=2)
            self.canvas.create_text(x, 50, text=title, font=("Inter", 9, "bold"), fill=text_color)
            self.canvas.create_text(x, 70, text=sub, font=("Inter", 7), fill=text_color)

        # Draw links
        # HW Link
        self.canvas.create_line(145, 60, 215, 60, arrow=tk.LAST, width=2, fill="#4b5563")
        self.canvas.create_text(180, 45, text=self.hw_mode.get().upper(), font=("Inter", 8, "bold"), fill="#059669")

        # Process Link (dotted)
        self.canvas.create_line(345, 60, 415, 60, dash=(4, 4), width=2, fill="#4b5563")

        # AR Link
        self.canvas.create_line(545, 60, 615, 60, arrow=tk.LAST, width=2, fill="#4b5563")
        self.canvas.create_text(580, 45, text=self.ar_mode.get().upper(), font=("Inter", 8, "bold"), fill="#059669")

    def browse_folder(self, var):
        path = filedialog.askdirectory()
        if path: var.set(path)

    def log(self, message, mtype="INFO"):
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{mtype}] {time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def check_resources(self):
        # 1. Hardware Resource Check
        if self.hw_mode.get() == "serial":
            port = self.hw_com_send.get()
            try:
                s = serial.Serial(port)
                s.close()
            except serial.SerialException as e:
                messagebox.showerror("Port in Use", f"Hardware control COM port '{port}' is unavailable or already in use by another program.\n\nDetails: {str(e)}")
                return False
        elif self.hw_mode.get() == "folder":
            p = self.hw_import_path.get()
            if not os.path.exists(p):
                try: os.makedirs(p)
                except Exception as e:
                    messagebox.showerror("Folder Error", f"Cannot create or access folder '{p}'.\n\nDetails: {str(e)}")
                    return False
        
        # 2. Analytics Resource Check
        if self.ar_mode.get() == "serial":
            port = self.ar_com_recv.get()
            # If the same port is used for both TX and RX, it's considered shared by this same program, so it's okay.
            if self.hw_mode.get() == "serial" and port == self.hw_com_send.get():
                pass
            else:
                try:
                    s = serial.Serial(port)
                    s.close()
                except serial.SerialException as e:
                    messagebox.showerror("Port in Use", f"Analytics readout COM port '{port}' is unavailable or already in use by another program.\n\nDetails: {str(e)}")
                    return False
        elif self.ar_mode.get() == "network":
            ip = self.ar_net_ip.get()
            port = int(self.ar_net_port_recv.get())
            protocol = self.ar_net_protocol.get()
            sock_type = socket.SOCK_STREAM if protocol == "TCP" else socket.SOCK_DGRAM
            with socket.socket(socket.AF_INET, sock_type) as s:
                try:
                    s.bind((ip if ip and ip != "127.0.0.1" else "0.0.0.0", port))
                except socket.error as e:
                    messagebox.showerror("Port in Use", f"Analytics network port '{port}' is already in use by another program.\n\nDetails: {str(e)}")
                    return False
        elif self.ar_mode.get() == "folder":
            p = self.ar_export_path.get()
            if not os.path.exists(p):
                try: os.makedirs(p)
                except Exception as e:
                    messagebox.showerror("Folder Error", f"Cannot create or access folder '{p}'.\n\nDetails: {str(e)}")
                    return False
                    
        return True

    def toggle_bridge(self):
        if not self.running:
            if not self.check_resources():
                return
            self.start_bridge()
        else:
            self.stop_bridge()

    def start_bridge(self):
        self.running = True
        self.btn_toggle.config(text="STOP BRIDGE SERVICE", bg="#ef4444")
        self.log(f"Service started. HW Mode: {self.hw_mode.get().upper()} | AR Mode: {self.ar_mode.get().upper()}")
        threading.Thread(target=self.bridge_loop, daemon=True).start()

    def stop_bridge(self):
        self.running = False
        self.btn_toggle.config(text="START BRIDGE SERVICE", bg="#10b981")
        self.log("Service stopped.")

    def bridge_loop(self):
        while self.running:
            try:
                # 1. Pull from Server (Hardware Send)
                self.check_for_proposals()
                
                # 2. Poll hardware for results (Analytics Read)
                ar_mode = self.ar_mode.get()
                if ar_mode == "folder": self.check_local_exports()
                elif ar_mode == "network": self.check_network_input()
                elif ar_mode == "serial": self.check_serial_input()
                elif ar_mode == "usb": self.check_usb_input()

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
        mode = self.hw_mode.get()
        if mode == "folder": self.save_proposal_to_folder(proposal)
        elif mode == "serial": self.send_to_serial(proposal)
        elif mode == "network": self.send_to_network(proposal)
        elif mode == "usb": self.send_to_usb(proposal)

    # --- HW SEND IMPLEMENTATIONS ---

    def save_proposal_to_folder(self, proposal):
        fname = f"Proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fpath = os.path.join(self.hw_import_path.get(), fname)
        if not os.path.exists(self.hw_import_path.get()): os.makedirs(self.hw_import_path.get())
        with open(fpath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=proposal['features_only'][0].keys())
            writer.writeheader()
            writer.writerows(proposal['features_only'])
        self.log(f"Saved: {fname}")

    def send_to_serial(self, proposal):
        self.log(f"Sent via COM {self.hw_com_send.get()} @ {self.hw_baud_rate.get()} baud")

    def send_to_network(self, proposal):
        try:
            msg = json.dumps(proposal).encode()
            if self.hw_net_protocol.get() == "TCP":
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect((self.hw_net_ip.get(), int(self.hw_net_port_send.get())))
                    s.sendall(msg)
            else:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.sendto(msg, (self.hw_net_ip.get(), int(self.hw_net_port_send.get())))
            self.log(f"Network Send: Success to {self.hw_net_ip.get()}:{self.hw_net_port_send.get()}")
        except Exception as e:
            self.log(f"Network Send Error: {e}", "ERR")

    def send_to_usb(self, proposal):
        self.log(f"USB Direct Send: (VID:{self.hw_usb_vid.get()} PID:{self.hw_usb_pid.get()}) - Data queued.")

    # --- AR RECV IMPLEMENTATIONS ---

    def check_local_exports(self):
        path = self.ar_export_path.get()
        if not os.path.exists(path): return
        for fname in os.listdir(path):
            if fname.endswith('.csv') and not fname.startswith('SENT_'):
                with open(os.path.join(path, fname), 'r') as f:
                    data = [r for r in csv.DictReader(f)]
                if self.push_results_to_server(data):
                    os.rename(os.path.join(path, fname), os.path.join(path, "SENT_" + fname))
                    self.log(f"Result Sync: {fname}")

    def check_serial_input(self):
        # Poll COM recv port
        pass

    def check_network_input(self):
        # Create a listener for result packets on self.ar_net_port_recv
        pass

    def check_usb_input(self):
        pass

    def push_results_to_server(self, data):
        try:
            resp = requests.post(f"{self.api_url.get().rstrip('/')}/auto/results", json=data, timeout=5)
            return resp.status_code == 200
        except: return False

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    AutoEDOSIMEX_v2(root)
    root.mainloop()
