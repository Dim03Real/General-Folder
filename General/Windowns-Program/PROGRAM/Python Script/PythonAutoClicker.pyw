import threading
import time
import tkinter as tk
from tkinter import ttk
from pynput import keyboard
from pynput.mouse import Button, Controller
from ttkthemes import ThemedTk

mouse = Controller()
clicking = False
custom_key = keyboard.Key.f8  # Default toggle key

def start_clicking():
    global clicking
    if not clicking:
        clicking = True
        update_ui()
        threading.Thread(target=click_loop, daemon=True).start()

def stop_clicking():
    global clicking
    clicking = False
    update_ui()

def toggle_clicking():
    global clicking
    clicking = not clicking
    update_ui()
    if clicking:
        threading.Thread(target=click_loop, daemon=True).start()

def update_ui():
    if clicking:
        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        status_label.config(text="Ready ✅", foreground="lime")
    else:
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        status_label.config(text="Not ready ❌", foreground="red")

def click_loop():
    while clicking:
        try:
            delay = float(cps_entry.get()) / 1000.0
        except:
            delay = 0.001
        mouse.click(Button.left)
        time.sleep(delay)

def on_press(key):
    global custom_key
    if key == custom_key:
        toggle_clicking()

keyboard.Listener(on_press=on_press, daemon=True).start()

def open_settings():
    settings = ThemedTk(theme="equilux")
    settings.title("Settings ⚙️")
    settings.geometry("300x200")
    settings.configure(bg="#222")
    settings.resizable(False, False)

    def set_new_key():
        key_display.config(text="Press a key...")

        def on_new_key_press(k):
            nonlocal key_listener
            if hasattr(k, 'char') or isinstance(k, keyboard.Key):
                global custom_key
                custom_key = k
                key_display.config(text=f"Set to: {k}")
                hotkey_label.config(text=f"Hotkey: {k} to toggle")
                key_listener.stop()

        key_listener = keyboard.Listener(on_press=on_new_key_press)
        key_listener.start()

    ttk.Label(settings, text="Set Custom Toggle Key", font=("Segoe UI", 10, "bold")).pack(pady=10)
    key_display = ttk.Label(settings, text=f"Current: {custom_key}", font=("Segoe UI", 10))
    key_display.pack()
    ttk.Button(settings, text="Change Keybind", command=set_new_key).pack(pady=10)
    ttk.Label(settings, text="(Press the key you want after clicking)", font=("Segoe UI", 8), foreground="gray").pack(pady=5)
    settings.mainloop()

# GUI setup
root = ThemedTk(theme="equilux")
root.title("⚡ Inverted Auto Clicker")
root.geometry("430x430")
root.resizable(False, False)
root.configure(bg="#333")

style = ttk.Style()
style.configure("TLabel", foreground="white", background="#333")
style.configure("TButton", font=("Segoe UI", 10, "bold"))

tk.Label(root, text="Inverted Auto Clicker", font=("Segoe UI", 14, "bold"), bg="#333", fg="white").pack(pady=10)

frame = ttk.Frame(root)
frame.pack(pady=5)

ttk.Label(frame, text="Manual Speed (milliseconds):").pack(side=tk.LEFT, padx=5)

cps_entry = tk.Entry(frame, width=10, bg="#444", fg="white", insertbackground="white")
cps_entry.insert(0, "500")
cps_entry.pack(side=tk.LEFT)

# Preset options with values and font colors
preset_options = {
    "Insane (0 ms)": ("0", "black"),
    "Fast (100 ms)": ("100", "red"),
    "Medium (500 ms)": ("500", "orange"),
    "Slow (1000 ms)": ("1000", "green")
}

# Preset display label
preset_label = tk.Label(root, text="", font=("Segoe UI", 12, "bold"), bg="#333")
preset_label.pack()

# Custom dropdown replacement
def show_custom_dropdown():
    dropdown = tk.Toplevel(root)
    dropdown.overrideredirect(True)
    x = root.winfo_x() + dropdown_button.winfo_x()
    y = root.winfo_y() + dropdown_button.winfo_y() + dropdown_button.winfo_height()
    dropdown.geometry(f"200x120+{x}+{y}")
    dropdown.configure(bg="#222")

    for label, (value, color) in preset_options.items():
        item = tk.Label(dropdown, text=label, fg=color, bg="#222", font=("Segoe UI", 10), anchor="w")
        item.pack(fill="x", padx=5, pady=2)

        def callback(lbl=label, val=value, col=color):
            cps_entry.delete(0, tk.END)
            cps_entry.insert(0, val)
            preset_label.config(text=lbl, fg=col)
            dropdown.destroy()

        item.bind("<Button-1>", lambda e, cb=callback: cb())

    dropdown.focus_force()
    dropdown.bind("<FocusOut>", lambda e: dropdown.destroy())

# Fake dropdown button
dropdown_button = ttk.Button(root, text="Choose speed preset", command=show_custom_dropdown)
dropdown_button.pack(pady=10)

status_label = ttk.Label(root, text="Not ready ❌", foreground="red", font=("Segoe UI", 10, "bold"))
status_label.pack(pady=10)

button_frame = ttk.Frame(root)
button_frame.pack(pady=5)

start_button = ttk.Button(button_frame, text="Start", command=start_clicking)
start_button.grid(row=0, column=0, padx=10)

stop_button = ttk.Button(button_frame, text="Stop", command=stop_clicking, state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=10)

settings_button = ttk.Button(root, text="⚙️", width=3, command=open_settings)
settings_button.place(x=10, y=390)

hotkey_label = ttk.Label(root, text="Hotkey: F8 to toggle", font=("Segoe UI", 9), foreground="gray")
hotkey_label.pack(pady=5)

ttk.Label(root, text="made by Tim & dimreal03", font=("Segoe UI", 8), foreground="gray").pack(side=tk.BOTTOM, pady=10)

root.mainloop()
