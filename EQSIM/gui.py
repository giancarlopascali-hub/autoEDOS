import os
import time
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

class EQSIMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("EQSIM | Equipment Simulator")
        self.root.geometry("800x700")
        self.root.configure(bg="#0d1117")  # Matching the dark theme
        
        # Appearance
        self.accent_color = "#7c4dff"
        self.bg_card = "#161b22"
        self.text_color = "#f0f6fc"
        self.text_dim = "#8b949e"
        
        # State
        self.active = False
        self.folder_a = tk.StringVar()
        self.folder_b = tk.StringVar()
        self.folder_c = tk.StringVar()
        self.folder_d = tk.StringVar()
        self.tag = tk.StringVar(value="USED_")
        self.delay = tk.DoubleVar(value=1.0)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1c1c3c", height=100)
        header.pack(fill="x")
        tk.Label(header, text="EQSIM", font=("Inter", 28, "bold"), fg=self.accent_color, bg="#1c1c3c").pack(pady=(15, 0))
        tk.Label(header, text="Autonomous Equipment Folder Monitor", font=("Inter", 10), fg=self.text_dim, bg="#1c1c3c").pack()

        main_frame = tk.Frame(self.root, bg="#0d1117", padx=30, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Config Section
        config_frame = tk.LabelFrame(main_frame, text=" CONFIGURATION ", bg=self.bg_card, fg=self.accent_color, 
                                     font=("Inter", 9, "bold"), padx=20, pady=20)
        config_frame.pack(fill="x", pady=10)

        # GRID for folder paths
        folders = [
            ("Watch Folder A (New Files):", self.folder_a),
            ("Destination Folder B:", self.folder_b),
            ("Watch Folder C (Feedback Source):", self.folder_c),
            ("Destination Folder D:", self.folder_d)
        ]

        for i, (label, var) in enumerate(folders):
            tk.Label(config_frame, text=label, bg=self.bg_card, fg=self.text_dim, font=("Inter", 9)).grid(row=i*2, column=0, sticky="w", pady=(5,0))
            entry = tk.Entry(config_frame, textvariable=var, width=60, bg="#000000", fg=self.text_color, borderwidth=0, highlightthickness=1)
            entry.config(highlightbackground="#30363d", highlightcolor=self.accent_color)
            entry.grid(row=i*2+1, column=0, pady=(2,10), sticky="we")
            
            btn = tk.Button(config_frame, text="Browse", command=lambda v=var: self.browse(v), 
                            bg="#21262d", fg=self.text_color, borderwidth=0, padx=10)
            btn.grid(row=i*2+1, column=1, padx=10, pady=(2,10))

        # Tag and Delay
        settings_frame = tk.Frame(config_frame, bg=self.bg_card)
        settings_frame.grid(row=8, column=0, columnspan=2, sticky="w", pady=10)

        tk.Label(settings_frame, text="Processing Tag:", bg=self.bg_card, fg=self.text_dim).pack(side="left")
        tk.Entry(settings_frame, textvariable=self.tag, width=10, bg="#000000", fg=self.text_color).pack(side="left", padx=(5, 20))
        
        tk.Label(settings_frame, text="Delay (sec):", bg=self.bg_card, fg=self.text_dim).pack(side="left")
        tk.Entry(settings_frame, textvariable=self.delay, width=10, bg="#000000", fg=self.text_color).pack(side="left", padx=5)

        # Control Section
        ctrl_frame = tk.Frame(main_frame, bg="#0d1117")
        ctrl_frame.pack(fill="x", pady=10)

        self.btn_toggle = tk.Button(ctrl_frame, text="ACTIVATE SIMULATOR", command=self.toggle, 
                                    bg=self.accent_color, fg="white", font=("Inter", 12, "bold"), 
                                    padx=40, pady=15, borderwidth=0, cursor="hand2")
        self.btn_toggle.pack()

        # Logs Section
        log_frame = tk.LabelFrame(main_frame, text=" OPERATION LOGS ", bg="#0d1117", fg=self.text_dim, 
                                  font=("Inter", 9, "bold"), padx=10, pady=10)
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, bg="#000000", fg="#3fb950", font=("Consolas", 9), 
                                state="disabled", borderwidth=0, padx=10, pady=10)
        self.log_text.pack(fill="both", expand=True)

    def browse(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(os.path.normpath(path))

    def log(self, message):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def toggle(self):
        if not self.active:
            # Validate
            if not all([self.folder_a.get(), self.folder_b.get(), self.folder_c.get(), self.folder_d.get()]):
                messagebox.showwarning("Missing Paths", "Please set all folder paths before activating.")
                return
            
            self.active = True
            self.btn_toggle.config(text="DEACTIVATE SIMULATOR", bg="#f85149")
            self.log("EQSIM ACTIVATED")
            threading.Thread(target=self.monitor_loop, daemon=True).start()
        else:
            self.active = False
            self.btn_toggle.config(text="ACTIVATE SIMULATOR", bg=self.accent_color)
            self.log("EQSIM DEACTIVATED")

    def monitor_loop(self):
        while self.active:
            try:
                f_a = self.folder_a.get()
                f_b = self.folder_b.get()
                f_c = self.folder_c.get()
                f_d = self.folder_d.get()
                tag = self.tag.get()
                delay = self.delay.get()

                if not os.path.exists(f_a):
                    time.sleep(1)
                    continue

                # Scan A
                files = os.listdir(f_a)
                new_files = [f for f in files if not f.startswith(tag) and os.path.isfile(os.path.join(f_a, f))]

                for filename in new_files:
                    if not self.active: break
                    
                    path_a = os.path.join(f_a, filename)
                    path_b = os.path.join(f_b, filename)
                    
                    # 1. Copy A to B
                    self.log(f"Detected: {filename}. Copying to B...")
                    if not os.path.exists(f_b): os.makedirs(f_b)
                    shutil.copy2(path_a, path_b)
                    
                    # 2. Rename A
                    new_name_a = tag + filename
                    os.rename(path_a, os.path.join(f_a, new_name_a))
                    self.log(f"Flagged in A: {new_name_a}")
                    
                    # 3. Delay
                    self.log(f"Waiting {delay}s...")
                    time.sleep(delay)
                    
                    # 4. Copy most recent UNFLAGGED from C to D
                    if os.path.exists(f_c):
                        files_c = [f for f in os.listdir(f_c) if os.path.isfile(os.path.join(f_c, f)) and not f.startswith(tag)]
                        if files_c:
                            f_paths = [os.path.join(f_c, f) for f in files_c]
                            latest_path = max(f_paths, key=os.path.getmtime)
                            latest_name = os.path.basename(latest_path)
                            
                            self.log(f"Latest in C: {latest_name}. Copying to D...")
                            if not os.path.exists(f_d): os.makedirs(f_d)
                            shutil.copy2(latest_path, os.path.join(f_d, latest_name))
                            
                            # 5. Rename C
                            new_name_c = tag + latest_name
                            os.rename(latest_path, os.path.join(f_c, new_name_c))
                            self.log(f"Flagged in C: {new_name_c}")
                        else:
                            self.log("No unflagged files in C.")
                    else:
                        self.log(f"Error: Folder C not found.", "ERR")

            except Exception as e:
                self.log(f"Error: {str(e)}")
            
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    # Simple style adjustments for ttk
    style = ttk.Style()
    style.theme_use('clam')
    app = EQSIMApp(root)
    root.mainloop()
