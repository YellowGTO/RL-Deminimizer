import os
import sys
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk
import pygetwindow as gw

# 1. Setup Paths
# We know this path works from your debug run
LOG_PATH = os.path.expanduser(r'~\Documents\My Games\Rocket League\TAGame\Logs\Launch.log')

# 2. Define Triggers
# "ReserveConnection" = The server has reserved a slot for you (Earliest notification)
# "Travel to" = You are actually loading into the map (Backup trigger)
TRIGGERS = ["ReserveConnection", "Travel to"]

STARTUP_NAME = "RLjoin_autostart.cmd"

def maximize_rocket_league():
    try:
        # We use a partial match because your title includes "DX11, Cooked, etc"
        windows = gw.getWindowsWithTitle('Rocket League')
        
        if windows:
            rl = windows[0]
            if rl.isMinimized:
                print(f"[ACTION] Match found! Maximizing window...")
                rl.restore()   # Un-minimize
                rl.activate()  # Bring to front
                return True
            else:
                print(f"[INFO] Match found, but window is already active.")
                return False
    except Exception as e:
        print(f"[ERROR] Could not maximize window: {e}")
    return False

def get_startup_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None
    return os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup", STARTUP_NAME)


def is_startup_enabled():
    path = get_startup_path()
    return path is not None and os.path.exists(path)


def enable_startup():
    path = get_startup_path()
    if not path:
        return False, "APPDATA not set"

    # Check if we are running as a compiled exe (PyInstaller)
    if getattr(sys, 'frozen', False):
        # In PyInstaller, sys.executable is the path to the actual RL-Deminimizer.exe
        exe_path = sys.executable
        # We just want to run the exe. No arguments needed.
        content = f'@echo off\nstart "" "{exe_path}"\n'
    else:
        # Running as a script (Development mode)
        script_path = os.path.abspath(__file__)
        python_exe = sys.executable
        pythonw = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
        if os.path.exists(pythonw):
            python_exe = pythonw
        content = f'@echo off\nstart "" "{python_exe}" "{script_path}"\n'
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True, ""
    except Exception as e:
        return False, str(e)


def disable_startup():
    path = get_startup_path()
    try:
        if path and os.path.exists(path):
            os.remove(path)
        return True, ""
    except Exception as e:
        return False, str(e)


def format_duration(delta):
    total_seconds = int(delta.total_seconds())
    if total_seconds < 0:
        total_seconds = 0

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes > 0:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


class RLJoinerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RL Joiner")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="Monitoring: Off")
        self.time_var = tk.StringVar(value="Time since last game: —")
        self.show_time_var = tk.BooleanVar(value=True)
        self.startup_var = tk.BooleanVar(value=is_startup_enabled())

        self.monitor_running = False
        self.stop_event = threading.Event()
        # Start timer immediately on launch for the first game
        self.last_game_time = datetime.now()
        self.monitor_thread = None

        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(1000, self._tick)
        self.start_monitor()

    def _build_ui(self):
        padding = {"padx": 12, "pady": 6}

        title = ttk.Label(self.root, text="RL Deminimizer", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, **padding, sticky="w")

        status = ttk.Label(self.root, textvariable=self.status_var)
        status.grid(row=1, column=0, columnspan=2, **padding, sticky="w")

        self.toggle_btn = ttk.Button(self.root, text="Start Monitoring", command=self.toggle_monitor)
        self.toggle_btn.grid(row=2, column=0, **padding, sticky="w")

        time_label = ttk.Label(self.root, textvariable=self.time_var)
        time_label.grid(row=3, column=0, columnspan=2, **padding, sticky="w")

        show_time = ttk.Checkbutton(
            self.root,
            text="Show time since last game",
            variable=self.show_time_var,
            command=self._update_time_label,
        )
        show_time.grid(row=4, column=0, columnspan=2, **padding, sticky="w")

        startup = ttk.Checkbutton(
            self.root,
            text="Start with Windows",
            variable=self.startup_var,
            command=self._toggle_startup,
        )
        startup.grid(row=5, column=0, columnspan=2, **padding, sticky="w")

    def _set_status(self, message):
        self.status_var.set(message)

    def _safe_set_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))

    def _set_last_game_now(self):
        self.last_game_time = datetime.now()
        self.root.after(0, self._update_time_label)

    def _update_time_label(self):
        if not self.show_time_var.get():
            self.time_var.set("")
            return

        if self.last_game_time is None:
            self.time_var.set("Time since last game: —")
            return

        delta = datetime.now() - self.last_game_time
        self.time_var.set(f"Time since last game: {format_duration(delta)}")

    def _tick(self):
        self._update_time_label()
        self.root.after(1000, self._tick)

    def toggle_monitor(self):
        if self.monitor_running:
            self.stop_monitor()
        else:
            self.start_monitor()

    def start_monitor(self):
        if self.monitor_running:
            return
        self.stop_event.clear()
        self.monitor_running = True
        self.toggle_btn.configure(text="Stop Monitoring")
        self._set_status("Monitoring: On")
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitor(self):
        if not self.monitor_running:
            return
        self.stop_event.set()
        self.monitor_running = False
        self.toggle_btn.configure(text="Start Monitoring")
        self._set_status("Monitoring: Off")

    def _toggle_startup(self):
        if self.startup_var.get():
            ok, err = enable_startup()
            if not ok:
                self.startup_var.set(False)
                self._set_status(f"Autostart failed: {err}")
        else:
            ok, err = disable_startup()
            if not ok:
                self.startup_var.set(True)
                self._set_status(f"Autostart remove failed: {err}")

    def _monitor_loop(self):
        while not self.stop_event.is_set():
            if not os.path.exists(LOG_PATH):
                self._safe_set_status(f"Log file not found: {LOG_PATH}")
                time.sleep(2)
                continue

            try:
                with open(LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(0, 2)

                    while not self.stop_event.is_set():
                        line = f.readline()
                        if not line:
                            time.sleep(0.5)
                            continue

                        if any(trigger in line for trigger in TRIGGERS):
                            self._safe_set_status("Match detected — bringing Rocket League to front.")
                            self._set_last_game_now()

                            if maximize_rocket_league():
                                time.sleep(10)
            except Exception as e:
                self._safe_set_status(f"Monitor error: {e}")
                time.sleep(2)

    def on_close(self):
        self.stop_monitor()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RLJoinerApp(root)
    root.mainloop()
