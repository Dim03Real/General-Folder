import tkinter as tk
from tkinter import messagebox
import time
import threading
import pickle
from pynput import mouse, keyboard
import ctypes
from ctypes import wintypes

# Real mouse click and scroll using SendInput
PUL = ctypes.POINTER(ctypes.c_ulong)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", PUL)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("mi", MOUSEINPUT)]

def send_click(x, y, down=True):
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    abs_x = int(x * 65535 / screen_width)
    abs_y = int(y * 65535 / screen_height)

    flags_move = 0x8000 | 0x0001
    flags_click = 0x0002 if down else 0x0004

    inp_move = INPUT(type=0, mi=MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0, dwFlags=flags_move, time=0, dwExtraInfo=None))
    inp_click = INPUT(type=0, mi=MOUSEINPUT(dx=abs_x, dy=abs_y, mouseData=0, dwFlags=flags_click, time=0, dwExtraInfo=None))

    ctypes.windll.user32.SendInput(1, ctypes.byref(inp_move), ctypes.sizeof(inp_move))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp_click), ctypes.sizeof(inp_click))

def send_scroll(dx, dy):
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_HWHEEL = 0x01000
    mouseData = dy * 120 if dy else dx * 120
    flags = MOUSEEVENTF_WHEEL if dy else MOUSEEVENTF_HWHEEL
    inp = INPUT(type=0, mi=MOUSEINPUT(dx=0, dy=0, mouseData=mouseData, dwFlags=flags, time=0, dwExtraInfo=None))
    ctypes.windll.user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))

# Globals
recording = False
playing = False
looping = False
events = []
start_time = 0
stop_loop_flag = False
loop_count = 0

keyboard_controller = keyboard.Controller()

def on_mouse_move(x, y):
    if recording:
        events.append(('move', time.time() - start_time, (x, y)))

def on_mouse_click(x, y, button, pressed):
    if recording and button.name == 'left':
        events.append(('click', time.time() - start_time, (x, y, pressed)))

def on_mouse_scroll(x, y, dx, dy):
    if recording:
        events.append(('scroll', time.time() - start_time, (x, y, dx, dy)))

def on_key_press(key):
    if recording:
        events.append(('key_press', time.time() - start_time, key))

def on_key_release(key):
    if recording:
        events.append(('key_release', time.time() - start_time, key))

def playback(evts, stop_on_end=False):
    global playing, looping, stop_loop_flag, loop_count
    if stop_loop_flag:
        return

    start_play = time.time()
    for event in evts:
        if stop_loop_flag:
            break
        etype, etime, edata = event
        time.sleep(max(0, start_play + etime - time.time()))

        if etype == 'move':
            x, y = edata
            send_click(x, y, down=False)
        elif etype == 'click':
            x, y, pressed = edata
            send_click(x, y, down=pressed)
        elif etype == 'scroll':
            x, y, dx, dy = edata
            send_scroll(dx, dy)
        elif etype == 'key_press':
            try: keyboard_controller.press(edata)
            except: pass
        elif etype == 'key_release':
            try: keyboard_controller.release(edata)
            except: pass

    if looping and not stop_loop_flag:
        loop_count += 1
        loop_count_label.config(text=f"Count: {loop_count}", fg="#00ffff")
        playback(evts, stop_on_end=stop_on_end)
    else:
        if stop_on_end:
            playing = False
            looping = False
            update_ui_ready()

def update_ui_ready():
    global loop_count
    loop_count = 0
    loop_count_label.config(text="Count: 0", fg="#aaaaaa")
    status_label.config(text="Ready", fg="#00ff00")
    set_button_state(record_button, True)
    set_button_state(play_back_button, True)
    set_button_state(loop_button, True)
    set_button_state(stop_loop_button, False)

def set_button_state(button, enabled):
    if enabled:
        button.config(state="normal", fg=button.custom_fg, bg="#222222", activebackground="#555555", cursor="hand2")
    else:
        button.config(state="disabled", fg="#555555", bg="#111111", cursor="arrow")

def update_timer():
    if recording:
        elapsed = time.time() - start_time
        record_timer_label.config(text=f"Timer: {elapsed:.1f}s", fg="#ff4444")
        root.after(100, update_timer)
    else:
        record_timer_label.config(text="Timer: 0.0s", fg="white")

def toggle_record():
    global recording, start_time, events
    if playing or looping:
        messagebox.showwarning("Warning", "Cannot record during playback or loop!")
        return

    if recording:
        recording = False
        with open("recording.pkl", "wb") as f:
            pickle.dump(events, f)
        status_label.config(text="Ready", fg="#00ff00")
        record_button.config(text="⏺ Record")
        update_timer()
        set_button_state(play_back_button, True)
        set_button_state(loop_button, True)
    else:
        events.clear()
        start_time = time.time()
        recording = True
        status_label.config(text="Recording...", fg="#ff5555")
        record_button.config(text="⏹ Stop Recording")
        set_button_state(play_back_button, False)
        set_button_state(loop_button, False)
        update_timer()

def play_back():
    global playing, recording, stop_loop_flag
    if recording:
        messagebox.showwarning("Warning", "Cannot play back during recording!")
        return
    if playing or looping:
        messagebox.showwarning("Warning", "Playback already running!")
        return

    try:
        with open("recording.pkl", "rb") as f:
            evts = pickle.load(f)
    except:
        status_label.config(text="No recording found", fg="#ff5555")
        return

    playing = True
    stop_loop_flag = False
    status_label.config(text="Playing...", fg="#00ff00")
    set_button_state(record_button, False)
    set_button_state(play_back_button, False)
    set_button_state(loop_button, False)
    set_button_state(stop_loop_button, True)

    threading.Thread(target=lambda: playback(evts, stop_on_end=True), daemon=True).start()

def loop_playback():
    global playing, looping, stop_loop_flag, loop_count
    if recording:
        messagebox.showwarning("Warning", "Cannot loop playback during recording!")
        return
    if playing or looping:
        messagebox.showwarning("Warning", "Playback already running!")
        return

    try:
        with open("recording.pkl", "rb") as f:
            evts = pickle.load(f)
    except:
        status_label.config(text="No recording found", fg="#ff5555")
        return

    playing = False
    looping = True
    stop_loop_flag = False
    loop_count = 1
    loop_count_label.config(text=f"Count: {loop_count}", fg="#00ffff")
    status_label.config(text="Looping...", fg="#00ffff")
    set_button_state(record_button, False)
    set_button_state(play_back_button, False)
    set_button_state(loop_button, False)
    set_button_state(stop_loop_button, True)

    threading.Thread(target=lambda: playback(evts, stop_on_end=False), daemon=True).start()

def stop_loop():
    global stop_loop_flag, playing, looping
    stop_loop_flag = True
    playing = False
    looping = False
    update_ui_ready()

# Listeners
mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click, on_scroll=on_mouse_scroll).start()
keyboard.Listener(on_press=on_key_press, on_release=on_key_release).start()

def on_activate_record(): root.after(0, toggle_record)
def on_activate_play(): root.after(0, play_back)
def on_activate_loop(): root.after(0, loop_playback)
def on_activate_stop(): root.after(0, stop_loop)

# Keybind customization
keybinds = {'record': '<f1>', 'play': '<f2>', 'loop': '<f3>', 'stop': '<f4>'}
hotkey_listener = None

def start_hotkeys():
    global hotkey_listener
    if hotkey_listener:
        hotkey_listener.stop()
    hotkey_listener = keyboard.GlobalHotKeys({
        keybinds['record']: on_activate_record,
        keybinds['play']: on_activate_play,
        keybinds['loop']: on_activate_loop,
        keybinds['stop']: on_activate_stop,
    })
    hotkey_listener.start()

def stop_hotkeys():
    global hotkey_listener
    if hotkey_listener:
        hotkey_listener.stop()
        hotkey_listener = None

def open_keybind_window():
    stop_hotkeys()
    kb_win = tk.Toplevel(root)
    kb_win.title("Customize Keybinds")
    kb_win.configure(bg="black")
    kb_win.geometry("400x300")
    kb_win.resizable(False, False)

    info_label = tk.Label(kb_win, text="Click on a box and press a key to set the keybind.", fg="white", bg="black", font=("Segoe UI", 10))
    info_label.pack(pady=10)

    entries = {}

    def on_key_press(event, action):
        key = event.keysym.lower()
        if len(key) == 1:
            key = key
        else:
            key = f"<{key}>"
        entries[action].delete(0, tk.END)
        entries[action].insert(0, key)
        keybinds[action] = key
        update_keybind_hint()

    def save_keybinds():
        messagebox.showinfo("Saved", "Keybinds saved.")
        kb_win.destroy()
        start_hotkeys()
        update_keybind_hint()

    for action, label_text in zip(keybinds.keys(), ["Record", "Play", "Loop", "Stop"]):
        frame = tk.Frame(kb_win, bg="black")
        frame.pack(pady=5, fill="x", padx=20)

        label = tk.Label(frame, text=label_text, fg="white", bg="black", font=("Segoe UI", 12))
        label.pack(side="left")

        entry = tk.Entry(frame, font=("Segoe UI", 12), width=10, justify="center", bg="#222222", fg="white", insertbackground="white", relief="flat")
        entry.pack(side="right")
        entry.insert(0, keybinds[action])
        entries[action] = entry

        entry.bind("<Key>", lambda e, a=action: on_key_press(e, a))
        entry.bind("<KeyRelease>", lambda e: "break")
        entry.bind("<FocusIn>", lambda e: e.widget.delete(0, tk.END))

    save_btn = tk.Button(kb_win, text="Save", command=save_keybinds,
                         bg="#222222", fg="white", activebackground="#555555",
                         font=("Segoe UI", 12), relief="flat", cursor="hand2")
    save_btn.pack(pady=20)

    kb_win.grab_set()
    kb_win.focus_set()

# GUI setup
root = tk.Tk()
root.title("TinyTask by:Dimreal03")
root.configure(bg="black")
frame = tk.Frame(root, bg="black", padx=20, pady=20)
frame.pack()

btn_style = {"width": 15, "font": ("Segoe UI", 12, "bold"), "bg": "#222222", "activebackground": "#555555", "cursor": "hand2", "relief": "flat"}

record_button = tk.Button(frame, text="⏺ Record", command=toggle_record, **btn_style)
record_button.custom_fg = "#ff4444"
record_button.config(fg=record_button.custom_fg)
record_button.grid(row=0, column=0, padx=8, pady=8)

play_back_button = tk.Button(frame, text="▶ Play", command=play_back, **btn_style)
play_back_button.custom_fg = "#44ff44"
play_back_button.config(fg=play_back_button.custom_fg)
play_back_button.grid(row=0, column=1, padx=8, pady=8)

loop_button = tk.Button(frame, text="🔁 Loop", command=loop_playback, **btn_style)
loop_button.custom_fg = "#00ffff"
loop_button.config(fg=loop_button.custom_fg)
loop_button.grid(row=0, column=2, padx=8, pady=8)

stop_loop_button = tk.Button(frame, text="■ Stop", command=stop_loop, state="disabled", bg="#111111", fg="#555555", cursor="arrow", relief="flat")
stop_loop_button.custom_fg = "#ff4444"
stop_loop_button.grid(row=0, column=3, padx=8, pady=8)

emoji_button = tk.Button(frame, text="⚙️", command=open_keybind_window,
                         width=3, font=("Segoe UI", 14), bg="#222222", fg="white",
                         activebackground="#555555", cursor="hand2", relief="flat")
emoji_button.grid(row=0, column=4, padx=8, pady=8)

status_label = tk.Label(root, text="Ready", font=("Segoe UI", 14, "bold"), fg="#00ff00", bg="black")
status_label.pack(pady=(10, 0))

record_timer_label = tk.Label(root, text="Timer: 0.0s", font=("Segoe UI", 12), fg="white", bg="black")
record_timer_label.pack(pady=(5, 0))

loop_count_label = tk.Label(root, text="Count: 0", font=("Segoe UI", 12), fg="#aaaaaa", bg="black")
loop_count_label.pack(pady=(5, 15))

keybind_hint_label = tk.Label(root, text="", font=("Segoe UI", 10), fg="#aaaaaa", bg="black")
keybind_hint_label.pack(pady=(0, 10))

def update_keybind_hint():
    def prettify(k):
        if k.startswith("<") and k.endswith(">"):
            return k[1:-1].upper()
        return k.upper()
    text = f"Keybinds: Record = {prettify(keybinds['record'])}, Play = {prettify(keybinds['play'])}, Loop = {prettify(keybinds['loop'])}, Stop = {prettify(keybinds['stop'])}"
    keybind_hint_label.config(text=text)

update_keybind_hint()
start_hotkeys()
root.mainloop()
