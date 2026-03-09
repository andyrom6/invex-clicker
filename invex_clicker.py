import customtkinter as ctk
import ctypes
import ctypes.wintypes as w
import threading
import time
import random
import json
import os
import sys
import winsound

# ══════════════════════════════════════════════════════
#  Windows SendInput Structures (64-bit)
# ══════════════════════════════════════════════════════

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", w.WORD), ("wScan", w.WORD), ("dwFlags", w.DWORD),
                ("time", w.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", w.DWORD),
                ("dwFlags", w.DWORD), ("time", w.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", w.DWORD), ("wParamL", w.WORD), ("wParamH", w.WORD)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", w.DWORD), ("union", INPUT_UNION)]

INPUT_SIZE = ctypes.sizeof(INPUT)

# ══════════════════════════════════════════════════════
#  InputEngine — all SendInput calls in one place
# ══════════════════════════════════════════════════════

KEYS = {
    "Space": (0x20, 0x39), "E": (0x45, 0x12), "F": (0x46, 0x21),
    "R": (0x52, 0x13), "Q": (0x51, 0x10), "W": (0x57, 0x11),
    "A": (0x41, 0x1E), "S": (0x53, 0x1F), "D": (0x44, 0x20),
    "Z": (0x5A, 0x2C), "X": (0x58, 0x2D), "C": (0x43, 0x2E),
    "V": (0x56, 0x2F), "B": (0x42, 0x30), "G": (0x47, 0x22),
    "H": (0x48, 0x23), "I": (0x49, 0x17), "J": (0x4A, 0x24),
    "K": (0x4B, 0x25), "L": (0x4C, 0x26), "M": (0x4D, 0x32),
    "N": (0x4E, 0x31), "O": (0x4F, 0x18), "P": (0x50, 0x19),
    "T": (0x54, 0x14), "U": (0x55, 0x16), "Y": (0x59, 0x15),
    "1": (0x31, 0x02), "2": (0x32, 0x03), "3": (0x33, 0x04),
    "4": (0x34, 0x05), "5": (0x35, 0x06), "6": (0x36, 0x07),
    "7": (0x37, 0x08), "8": (0x38, 0x09), "9": (0x39, 0x0A),
    "0": (0x30, 0x0B), "Enter": (0x0D, 0x1C), "Shift": (0x10, 0x2A),
    "Tab": (0x09, 0x0F),
}

HOTKEY_MAP = {"F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
              "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
              "F9": 0x78, "F10": 0x79, "Insert": 0x2D, "Home": 0x24, "End": 0x23,
              "Escape": 0x1B}


class InputEngine:
    @staticmethod
    def key_down(vk, scan):
        inp = INPUT(); inp.type = 1
        inp.union.ki.wVk = vk; inp.union.ki.wScan = scan
        inp.union.ki.dwFlags = 0x0008
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)

    @staticmethod
    def key_up(vk, scan):
        inp = INPUT(); inp.type = 1
        inp.union.ki.wVk = vk; inp.union.ki.wScan = scan
        inp.union.ki.dwFlags = 0x0008 | 0x0002
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)

    @staticmethod
    def key_press(vk, scan, hold=0.05):
        InputEngine.key_down(vk, scan)
        time.sleep(hold)
        InputEngine.key_up(vk, scan)

    @staticmethod
    def mouse_click(button="left"):
        if button == "left":
            down, up = 0x0002, 0x0004
        else:
            down, up = 0x0008, 0x0010
        inp = INPUT(); inp.type = 0; inp.union.mi.dwFlags = down
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)
        time.sleep(0.02)
        inp2 = INPUT(); inp2.type = 0; inp2.union.mi.dwFlags = up
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp2), INPUT_SIZE)

    @staticmethod
    def mouse_move_relative(dx, dy):
        inp = INPUT(); inp.type = 0
        inp.union.mi.dx = dx; inp.union.mi.dy = dy
        inp.union.mi.dwFlags = 0x0001  # MOUSEEVENTF_MOVE
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)

    @staticmethod
    def mouse_move_abs(x, y):
        ctypes.windll.user32.SetCursorPos(x, y)

    @staticmethod
    def mouse_down(button="right"):
        flag = 0x0008 if button == "right" else 0x0002
        inp = INPUT(); inp.type = 0; inp.union.mi.dwFlags = flag
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)

    @staticmethod
    def mouse_up(button="right"):
        flag = 0x0010 if button == "right" else 0x0004
        inp = INPUT(); inp.type = 0; inp.union.mi.dwFlags = flag
        ctypes.windll.user32.SendInput(1, ctypes.byref(inp), INPUT_SIZE)

# ══════════════════════════════════════════════════════
#  Profile Manager
# ══════════════════════════════════════════════════════

PROFILE_DIR = os.path.join(os.environ.get("APPDATA", "."), "InvexClicker", "profiles")
os.makedirs(PROFILE_DIR, exist_ok=True)


class ProfileManager:
    @staticmethod
    def list_profiles():
        try:
            return [f.replace(".json", "") for f in os.listdir(PROFILE_DIR) if f.endswith(".json")]
        except Exception:
            return []

    @staticmethod
    def save(name, data):
        with open(os.path.join(PROFILE_DIR, f"{name}.json"), "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(name):
        with open(os.path.join(PROFILE_DIR, f"{name}.json"), "r") as f:
            return json.load(f)

    @staticmethod
    def delete(name):
        p = os.path.join(PROFILE_DIR, f"{name}.json")
        if os.path.exists(p):
            os.remove(p)

# ══════════════════════════════════════════════════════
#  Colors
# ══════════════════════════════════════════════════════

BG         = "#0B0D21"
SURFACE    = "#131832"
SURFACE_2  = "#1A2040"
BORDER     = "#1E3555"
GLOW       = "#2A5A7A"
ACCENT     = "#7B6CF6"
ACCENT_H   = "#9B8FFF"
ACCENT_DIM = "#1F1A40"
CYAN       = "#4AD8E0"
CYAN_H     = "#6DE8EE"
GREEN      = "#4ADE80"
GREEN_H    = "#6BEB9A"
GREEN_DIM  = "#0D2E1A"
RED        = "#FF4D6A"
RED_H      = "#FF6680"
ORANGE     = "#FFB86C"
YELLOW     = "#FFE066"
TEXT       = "#E8ECF4"
TEXT_2     = "#A0AACC"
TEXT_DIM   = "#5C6690"
TEXT_OFF   = "#2A3050"

# ══════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════

def sleep_check(delay, event):
    """Sleep in small steps, stop early if event is set."""
    elapsed = 0
    while elapsed < delay and not event.is_set():
        step = min(0.01, delay - elapsed)
        time.sleep(step)
        elapsed += step

ctk.set_appearance_mode("dark")

# ══════════════════════════════════════════════════════
#  MAIN APP
# ══════════════════════════════════════════════════════

class InvexClicker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Invex Clicker v3")
        self.geometry("510x740")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.attributes("-topmost", True)

        # Panic controller — all stop events
        self.stop_events = []
        self.key_running = False
        self.click_running = False
        self.afk_running = False
        self.combo_running = False
        self.key_holding = False
        self.key_count = 0
        self.click_count = 0
        self.session_start = time.time()
        self.timer_remaining = 0
        self.timer_active = False
        self.crosshair_win = None
        self.active_keys = []
        self.combo_steps = []

        # Hotkey config
        self.hotkey_vk = 0x75   # F6
        self.panic_vk = 0x1B   # Escape

        self._build_header()
        self._build_tabs()
        self._build_log()
        self._build_status_bar()
        self._tick_session()

        # Hotkey listener
        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    # ─── HEADER ───
    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=60)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        logo = ctk.CTkFrame(hdr, fg_color="transparent")
        logo.pack(side="left", padx=20)
        ctk.CTkLabel(logo, text="\u25C7", font=ctk.CTkFont(size=22), text_color=CYAN).pack(side="left")
        ctk.CTkLabel(logo, text="INVEX", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(logo, text="CLICKER", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=CYAN).pack(side="left", padx=(6, 0))

        ver = ctk.CTkFrame(hdr, fg_color=SURFACE_2, corner_radius=8, width=40, height=24,
                           border_width=1, border_color=GLOW)
        ver.pack(side="right", padx=20); ver.pack_propagate(False)
        ctk.CTkLabel(ver, text="v3", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CYAN).pack(expand=True)

        ctk.CTkFrame(self, fg_color=GLOW, height=1, corner_radius=0).pack(fill="x")

    # ─── TABS ───
    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self, fg_color=BG, corner_radius=0,
            segmented_button_fg_color=SURFACE_2,
            segmented_button_selected_color=GREEN,
            segmented_button_selected_hover_color=GREEN_H,
            segmented_button_unselected_color=SURFACE_2,
            segmented_button_unselected_hover_color="#253050",
            text_color="#0B0D21", text_color_disabled=TEXT_2
        )
        self.tabview.pack(fill="both", expand=True, padx=0, pady=0)

        for t in ["Auto Key", "Auto Click", "Anti-AFK", "Combos", "Settings"]:
            self.tabview.add(t)

        self._build_key_tab(self.tabview.tab("Auto Key"))
        self._build_click_tab(self.tabview.tab("Auto Click"))
        self._build_afk_tab(self.tabview.tab("Anti-AFK"))
        self._build_combo_tab(self.tabview.tab("Combos"))
        self._build_settings_tab(self.tabview.tab("Settings"))

    # ══════════════════════════════════════════
    #  AUTO KEY TAB
    # ══════════════════════════════════════════

    def _build_key_tab(self, tab):
        tab.configure(fg_color=BG)
        c = ctk.CTkFrame(tab, fg_color="transparent")
        c.pack(fill="both", expand=True, padx=14, pady=6)

        # Stats row
        sr = ctk.CTkFrame(c, fg_color="transparent"); sr.pack(fill="x", pady=(0, 8))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.key_stat_count = self._mini_stat(sr, "PRESSES", "0", ACCENT, 0)
        self.key_stat_speed = self._mini_stat(sr, "SPEED", "10/s", CYAN, 1)
        self.key_stat_key = self._mini_stat(sr, "KEY", "Space", ORANGE, 2)

        # Card
        card = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card.pack(fill="x")

        # Status
        sh = ctk.CTkFrame(card, fg_color="transparent"); sh.pack(fill="x", padx=16, pady=(12, 8))
        self.key_dot = ctk.CTkFrame(sh, width=8, height=8, corner_radius=4, fg_color=TEXT_OFF)
        self.key_dot.pack(side="left")
        self.key_status = ctk.CTkLabel(sh, text="Idle", font=ctk.CTkFont(size=11), text_color=TEXT_DIM)
        self.key_status.pack(side="left", padx=(6, 0))
        ctk.CTkFrame(card, fg_color=GLOW, height=1).pack(fill="x", padx=16)

        # Key + Mode
        r1 = ctk.CTkFrame(card, fg_color="transparent"); r1.pack(fill="x", padx=16, pady=(10, 0))
        r1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r1, text="Key", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).grid(row=0, column=0, sticky="w")
        self.key_sel = ctk.CTkOptionMenu(r1, values=list(KEYS.keys()), width=90, height=28,
            fg_color=SURFACE_2, button_color=ACCENT, button_hover_color=ACCENT_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=11), corner_radius=6,
            command=lambda v: self.key_stat_key.configure(text=v))
        self.key_sel.set("Space"); self.key_sel.grid(row=0, column=1, sticky="e")

        r2 = ctk.CTkFrame(card, fg_color="transparent"); r2.pack(fill="x", padx=16, pady=(8, 0))
        r2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r2, text="Mode", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).grid(row=0, column=0, sticky="w")
        self.key_mode = ctk.CTkSegmentedButton(r2, values=["Spam", "Hold"],
            font=ctk.CTkFont(size=10, weight="bold"), fg_color=SURFACE_2,
            selected_color=ACCENT, selected_hover_color=ACCENT_H,
            unselected_color=SURFACE_2, unselected_hover_color=BORDER,
            text_color=TEXT, corner_radius=6, height=28)
        self.key_mode.set("Spam"); self.key_mode.grid(row=0, column=1, sticky="e")

        # Speed
        sf = ctk.CTkFrame(card, fg_color="transparent"); sf.pack(fill="x", padx=16, pady=(10, 0))
        sft = ctk.CTkFrame(sf, fg_color="transparent"); sft.pack(fill="x")
        ctk.CTkLabel(sft, text="Speed", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).pack(side="left")
        self.key_speed_lbl = ctk.CTkLabel(sft, text="10 /sec", font=ctk.CTkFont(size=11, weight="bold"), text_color=ACCENT)
        self.key_speed_lbl.pack(side="right")
        self.key_speed = ctk.CTkSlider(sf, from_=1, to=20, number_of_steps=19,
            button_color=ACCENT, button_hover_color=ACCENT_H,
            fg_color=SURFACE_2, progress_color=CYAN, height=14)
        self.key_speed.set(10); self.key_speed.pack(fill="x", pady=(4, 0))
        self.key_speed.configure(command=lambda v: self.key_speed_lbl.configure(text=f"{int(v)} /sec"))

        # Options
        opts = ctk.CTkFrame(card, fg_color="transparent"); opts.pack(fill="x", padx=16, pady=(8, 0))
        self.key_human_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(opts, text="Humanize", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.key_human_var, onvalue="on", offvalue="off",
            button_color=ACCENT, button_hover_color=ACCENT_H, fg_color=SURFACE_2,
            progress_color=ACCENT, height=22).pack(side="left")

        # Multi-key
        mk = ctk.CTkFrame(card, fg_color="transparent"); mk.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(mk, text="Multi-Key", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).pack(side="left")
        self.multi_key = ctk.CTkEntry(mk, placeholder_text="e.g. E, F, Space", width=170, height=28,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.multi_key.pack(side="right")

        # Button
        self.key_btn = ctk.CTkButton(card, text="START", font=ctk.CTkFont(size=14, weight="bold"),
            height=42, fg_color=ACCENT, hover_color=ACCENT_H, text_color="#FFF",
            corner_radius=8, command=self._toggle_key)
        self.key_btn.pack(fill="x", padx=16, pady=(12, 14))

    # ══════════════════════════════════════════
    #  AUTO CLICK TAB
    # ══════════════════════════════════════════

    def _build_click_tab(self, tab):
        tab.configure(fg_color=BG)
        c = ctk.CTkFrame(tab, fg_color="transparent")
        c.pack(fill="both", expand=True, padx=14, pady=6)

        sr = ctk.CTkFrame(c, fg_color="transparent"); sr.pack(fill="x", pady=(0, 8))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.click_stat_count = self._mini_stat(sr, "CLICKS", "0", CYAN, 0)
        self.click_stat_speed = self._mini_stat(sr, "SPEED", "10/s", ACCENT, 1)
        self.click_stat_type = self._mini_stat(sr, "BUTTON", "Left", ORANGE, 2)

        card = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card.pack(fill="x")

        sh = ctk.CTkFrame(card, fg_color="transparent"); sh.pack(fill="x", padx=16, pady=(12, 8))
        self.click_dot = ctk.CTkFrame(sh, width=8, height=8, corner_radius=4, fg_color=TEXT_OFF)
        self.click_dot.pack(side="left")
        self.click_status = ctk.CTkLabel(sh, text="Idle", font=ctk.CTkFont(size=11), text_color=TEXT_DIM)
        self.click_status.pack(side="left", padx=(6, 0))
        ctk.CTkFrame(card, fg_color=GLOW, height=1).pack(fill="x", padx=16)

        # Button type
        r1 = ctk.CTkFrame(card, fg_color="transparent"); r1.pack(fill="x", padx=16, pady=(10, 0))
        r1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(r1, text="Button", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).grid(row=0, column=0, sticky="w")
        self.click_type = ctk.CTkSegmentedButton(r1, values=["Left", "Right"],
            font=ctk.CTkFont(size=10, weight="bold"), fg_color=SURFACE_2,
            selected_color=CYAN, selected_hover_color=CYAN_H,
            unselected_color=SURFACE_2, unselected_hover_color=BORDER,
            text_color=TEXT, corner_radius=6, height=28,
            command=lambda v: self.click_stat_type.configure(text=v))
        self.click_type.set("Left"); self.click_type.grid(row=0, column=1, sticky="e")

        # Speed
        sf = ctk.CTkFrame(card, fg_color="transparent"); sf.pack(fill="x", padx=16, pady=(10, 0))
        sft = ctk.CTkFrame(sf, fg_color="transparent"); sft.pack(fill="x")
        ctk.CTkLabel(sft, text="Speed", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).pack(side="left")
        self.click_speed_lbl = ctk.CTkLabel(sft, text="10 /sec", font=ctk.CTkFont(size=11, weight="bold"), text_color=CYAN)
        self.click_speed_lbl.pack(side="right")
        self.click_speed = ctk.CTkSlider(sf, from_=1, to=20, number_of_steps=19,
            button_color=CYAN, button_hover_color=CYAN_H, fg_color=SURFACE_2, progress_color=CYAN, height=14)
        self.click_speed.set(10); self.click_speed.pack(fill="x", pady=(4, 0))
        self.click_speed.configure(command=lambda v: self.click_speed_lbl.configure(text=f"{int(v)} /sec"))

        # Humanize
        o1 = ctk.CTkFrame(card, fg_color="transparent"); o1.pack(fill="x", padx=16, pady=(8, 0))
        self.click_human_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o1, text="Humanize", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.click_human_var, onvalue="on", offvalue="off",
            button_color=CYAN, button_hover_color=CYAN_H, fg_color=SURFACE_2,
            progress_color=CYAN, height=22).pack(side="left")

        # Burst mode
        o2 = ctk.CTkFrame(card, fg_color="transparent"); o2.pack(fill="x", padx=16, pady=(6, 0))
        self.burst_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o2, text="Burst mode", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.burst_var, onvalue="on", offvalue="off",
            button_color=CYAN, button_hover_color=CYAN_H, fg_color=SURFACE_2,
            progress_color=CYAN, height=22).pack(side="left")
        self.burst_count = ctk.CTkEntry(o2, placeholder_text="10", width=60, height=26,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.burst_count.pack(side="right")
        ctk.CTkLabel(o2, text="Count:", font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(side="right", padx=(0, 4))

        # Fixed position
        o3 = ctk.CTkFrame(card, fg_color="transparent"); o3.pack(fill="x", padx=16, pady=(6, 0))
        self.fixed_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o3, text="Fixed position", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.fixed_var, onvalue="on", offvalue="off",
            button_color=CYAN, button_hover_color=CYAN_H, fg_color=SURFACE_2,
            progress_color=CYAN, height=22).pack(side="left")

        coord = ctk.CTkFrame(card, fg_color="transparent"); coord.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(coord, text="X", font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(side="left")
        self.pos_x = ctk.CTkEntry(coord, placeholder_text="960", width=60, height=26,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.pos_x.pack(side="left", padx=(4, 10))
        ctk.CTkLabel(coord, text="Y", font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(side="left")
        self.pos_y = ctk.CTkEntry(coord, placeholder_text="540", width=60, height=26,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.pos_y.pack(side="left", padx=(4, 10))
        ctk.CTkButton(coord, text="Pick", font=ctk.CTkFont(size=10, weight="bold"), width=44, height=26,
            fg_color=SURFACE_2, hover_color=BORDER, text_color=CYAN, corner_radius=6,
            border_width=1, border_color=BORDER, command=self._pick_pos).pack(side="left")

        # Button
        self.click_btn = ctk.CTkButton(card, text="START", font=ctk.CTkFont(size=14, weight="bold"),
            height=42, fg_color=CYAN, hover_color=CYAN_H, text_color="#0A0A0F",
            corner_radius=8, command=self._toggle_click)
        self.click_btn.pack(fill="x", padx=16, pady=(12, 14))

        # Cursor display
        cur = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=10, border_width=1, border_color=GLOW)
        cur.pack(fill="x", pady=(8, 0))
        ci = ctk.CTkFrame(cur, fg_color="transparent"); ci.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(ci, text="Cursor", font=ctk.CTkFont(size=11, weight="bold"), text_color=TEXT_2).pack(side="left")
        self.cursor_lbl = ctk.CTkLabel(ci, text="X: 0  Y: 0",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color=CYAN)
        self.cursor_lbl.pack(side="right")
        self._tick_cursor()

    # ══════════════════════════════════════════
    #  ANTI-AFK TAB
    # ══════════════════════════════════════════

    def _build_afk_tab(self, tab):
        tab.configure(fg_color=BG)
        c = ctk.CTkFrame(tab, fg_color="transparent")
        c.pack(fill="both", expand=True, padx=14, pady=6)

        card = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card.pack(fill="x")

        sh = ctk.CTkFrame(card, fg_color="transparent"); sh.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(sh, text="Anti-AFK", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT).pack(side="left")
        self.afk_dot = ctk.CTkFrame(sh, width=8, height=8, corner_radius=4, fg_color=TEXT_OFF)
        self.afk_dot.pack(side="right")
        ctk.CTkFrame(card, fg_color=GLOW, height=1).pack(fill="x", padx=16)

        desc = ctk.CTkLabel(card, text="Keep your character active while AFK. Enable the actions you want below.",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM, wraplength=400)
        desc.pack(padx=16, pady=(10, 6), anchor="w")

        # Checkboxes
        self.afk_spin_var = ctk.StringVar(value="on")
        self.afk_wasd_var = ctk.StringVar(value="on")
        self.afk_jump_var = ctk.StringVar(value="off")
        self.afk_jitter_var = ctk.StringVar(value="off")

        opts = [
            ("Camera Spin", "Slowly rotates camera to stay active", self.afk_spin_var, ACCENT),
            ("Random Movement", "Presses W/A/S/D randomly", self.afk_wasd_var, CYAN),
            ("Random Jump", "Jumps at random intervals", self.afk_jump_var, GREEN),
            ("Mouse Jitter", "Tiny random mouse movements", self.afk_jitter_var, ORANGE),
        ]

        for label, desc_text, var, color in opts:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(6, 0))
            ctk.CTkSwitch(row, text="", variable=var, onvalue="on", offvalue="off",
                button_color=color, button_hover_color=color, fg_color=BORDER,
                progress_color=color, height=22, width=40).pack(side="left")
            tf = ctk.CTkFrame(row, fg_color="transparent"); tf.pack(side="left", padx=(8, 0))
            ctk.CTkLabel(tf, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT).pack(anchor="w")
            ctk.CTkLabel(tf, text=desc_text, font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(anchor="w")

        self.afk_btn = ctk.CTkButton(card, text="START ANTI-AFK", font=ctk.CTkFont(size=14, weight="bold"),
            height=42, fg_color=GREEN, hover_color="#00C853", text_color="#0A0A0F",
            corner_radius=8, command=self._toggle_afk)
        self.afk_btn.pack(fill="x", padx=16, pady=(16, 16))

        # Info
        info = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=10, border_width=1, border_color=GLOW)
        info.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(info, text="Tip: Camera Spin + Random Movement is the most reliable combo for staying in-game.",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM, wraplength=420).pack(padx=14, pady=10)

    # ══════════════════════════════════════════
    #  COMBOS TAB
    # ══════════════════════════════════════════

    def _build_combo_tab(self, tab):
        tab.configure(fg_color=BG)
        c = ctk.CTkFrame(tab, fg_color="transparent")
        c.pack(fill="both", expand=True, padx=14, pady=6)

        card = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card.pack(fill="x")

        sh = ctk.CTkFrame(card, fg_color="transparent"); sh.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(sh, text="Key Combos", font=ctk.CTkFont(size=14, weight="bold"), text_color=TEXT).pack(side="left")
        self.combo_dot = ctk.CTkFrame(sh, width=8, height=8, corner_radius=4, fg_color=TEXT_OFF)
        self.combo_dot.pack(side="right")
        ctk.CTkFrame(card, fg_color=GLOW, height=1).pack(fill="x", padx=16)

        ctk.CTkLabel(card, text="Build a sequence of keys with delays between them.",
            font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(padx=16, pady=(8, 6), anchor="w")

        # Sequence display
        self.combo_list_frame = ctk.CTkScrollableFrame(card, fg_color=SURFACE_2, corner_radius=8,
            height=120, border_width=1, border_color=GLOW)
        self.combo_list_frame.pack(fill="x", padx=16, pady=(0, 8))
        self.combo_labels = []

        # Add step controls
        add_row = ctk.CTkFrame(card, fg_color="transparent"); add_row.pack(fill="x", padx=16, pady=(0, 4))
        self.combo_key_sel = ctk.CTkOptionMenu(add_row, values=list(KEYS.keys()), width=80, height=28,
            fg_color=SURFACE_2, button_color=ACCENT, button_hover_color=ACCENT_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=11), corner_radius=6)
        self.combo_key_sel.set("Z"); self.combo_key_sel.pack(side="left")

        ctk.CTkLabel(add_row, text="Delay (ms):", font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(side="left", padx=(10, 4))
        self.combo_delay = ctk.CTkEntry(add_row, placeholder_text="100", width=60, height=28,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.combo_delay.pack(side="left")

        ctk.CTkButton(add_row, text="Add", font=ctk.CTkFont(size=11, weight="bold"), width=50, height=28,
            fg_color=ACCENT, hover_color=ACCENT_H, text_color="#FFF", corner_radius=6,
            command=self._combo_add).pack(side="left", padx=(10, 0))
        ctk.CTkButton(add_row, text="Clear", font=ctk.CTkFont(size=11, weight="bold"), width=50, height=28,
            fg_color=SURFACE_2, hover_color=BORDER, text_color=RED, corner_radius=6,
            border_width=1, border_color=BORDER, command=self._combo_clear).pack(side="left", padx=(6, 0))

        # Loop toggle
        loop_row = ctk.CTkFrame(card, fg_color="transparent"); loop_row.pack(fill="x", padx=16, pady=(6, 0))
        self.combo_loop_var = ctk.StringVar(value="on")
        ctk.CTkSwitch(loop_row, text="Loop continuously", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.combo_loop_var, onvalue="on", offvalue="off",
            button_color=ACCENT, button_hover_color=ACCENT_H, fg_color=SURFACE_2,
            progress_color=ACCENT, height=22).pack(side="left")

        self.combo_btn = ctk.CTkButton(card, text="START COMBO", font=ctk.CTkFont(size=14, weight="bold"),
            height=42, fg_color=ORANGE, hover_color="#FFB347", text_color="#0A0A0F",
            corner_radius=8, command=self._toggle_combo)
        self.combo_btn.pack(fill="x", padx=16, pady=(12, 14))

    # ══════════════════════════════════════════
    #  SETTINGS TAB
    # ══════════════════════════════════════════

    def _build_settings_tab(self, tab):
        tab.configure(fg_color=BG)
        c = ctk.CTkScrollableFrame(tab, fg_color=BG)
        c.pack(fill="both", expand=True, padx=14, pady=6)

        # ── Hotkeys card ──
        card1 = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card1.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(card1, text="Hotkeys", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkFrame(card1, fg_color=BORDER, height=1).pack(fill="x", padx=16)

        hk1 = ctk.CTkFrame(card1, fg_color="transparent"); hk1.pack(fill="x", padx=16, pady=(8, 0))
        hk1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hk1, text="Toggle Hotkey", font=ctk.CTkFont(size=11), text_color=TEXT_2).grid(row=0, column=0, sticky="w")
        self.hotkey_sel = ctk.CTkOptionMenu(hk1, values=[k for k in HOTKEY_MAP if k != "Escape"],
            width=90, height=28, fg_color=SURFACE_2, button_color=ACCENT, button_hover_color=ACCENT_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=11), corner_radius=6,
            command=self._on_hotkey_change)
        self.hotkey_sel.set("F6"); self.hotkey_sel.grid(row=0, column=1, sticky="e")

        hk2 = ctk.CTkFrame(card1, fg_color="transparent"); hk2.pack(fill="x", padx=16, pady=(8, 12))
        hk2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(hk2, text="Panic Key (stop all)", font=ctk.CTkFont(size=11), text_color=TEXT_2).grid(row=0, column=0, sticky="w")
        self.panic_sel = ctk.CTkOptionMenu(hk2, values=list(HOTKEY_MAP.keys()),
            width=90, height=28, fg_color=SURFACE_2, button_color=RED, button_hover_color=RED_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=11), corner_radius=6,
            command=self._on_panic_change)
        self.panic_sel.set("Escape"); self.panic_sel.grid(row=0, column=1, sticky="e")

        # ── Timer card ──
        card2 = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card2.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(card2, text="Session Timer", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkFrame(card2, fg_color=BORDER, height=1).pack(fill="x", padx=16)

        tr = ctk.CTkFrame(card2, fg_color="transparent"); tr.pack(fill="x", padx=16, pady=(8, 0))
        ctk.CTkLabel(tr, text="Auto-stop after (minutes):", font=ctk.CTkFont(size=11), text_color=TEXT_2).pack(side="left")
        self.timer_entry = ctk.CTkEntry(tr, placeholder_text="30", width=60, height=28,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.timer_entry.pack(side="right")

        tb = ctk.CTkFrame(card2, fg_color="transparent"); tb.pack(fill="x", padx=16, pady=(8, 0))
        self.timer_lbl = ctk.CTkLabel(tb, text="Not set", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT_DIM)
        self.timer_lbl.pack(side="left")
        ctk.CTkButton(tb, text="Start Timer", font=ctk.CTkFont(size=11, weight="bold"), width=90, height=28,
            fg_color=GREEN, hover_color="#00C853", text_color="#0A0A0F", corner_radius=6,
            command=self._start_timer).pack(side="right")
        ctk.CTkButton(tb, text="Cancel", font=ctk.CTkFont(size=11, weight="bold"), width=60, height=28,
            fg_color=SURFACE_2, hover_color=BORDER, text_color=RED, corner_radius=6,
            border_width=1, border_color=BORDER, command=self._cancel_timer).pack(side="right", padx=(0, 6))

        ctk.CTkLabel(card2, text="When timer ends: all macros stop + beep alert",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(padx=16, pady=(4, 12), anchor="w")

        # ── Crosshair card ──
        card3 = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card3.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(card3, text="Crosshair Overlay", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkFrame(card3, fg_color=BORDER, height=1).pack(fill="x", padx=16)

        cr1 = ctk.CTkFrame(card3, fg_color="transparent"); cr1.pack(fill="x", padx=16, pady=(8, 0))
        self.cross_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(cr1, text="Enable crosshair", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.cross_var, onvalue="on", offvalue="off",
            button_color=RED, button_hover_color=RED_H, fg_color=SURFACE_2,
            progress_color=RED, height=22, command=self._toggle_crosshair).pack(side="left")

        cr2 = ctk.CTkFrame(card3, fg_color="transparent"); cr2.pack(fill="x", padx=16, pady=(6, 0))
        ctk.CTkLabel(cr2, text="Color", font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(side="left")
        self.cross_color = ctk.CTkOptionMenu(cr2, values=["Red", "Green", "Cyan", "Yellow", "White"],
            width=80, height=26, fg_color=SURFACE_2, button_color=RED, button_hover_color=RED_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=10), corner_radius=6)
        self.cross_color.set("Red"); self.cross_color.pack(side="left", padx=(8, 16))
        ctk.CTkLabel(cr2, text="Size", font=ctk.CTkFont(size=11), text_color=TEXT_DIM).pack(side="left")
        self.cross_size = ctk.CTkSlider(cr2, from_=2, to=20, number_of_steps=18,
            button_color=RED, button_hover_color=RED_H, fg_color=BORDER, progress_color=RED,
            height=12, width=100)
        self.cross_size.set(6); self.cross_size.pack(side="left", padx=(8, 0))

        ctk.CTkLabel(card3, text="Transparent overlay dot at screen center. Click-through.",
            font=ctk.CTkFont(size=10), text_color=TEXT_DIM).pack(padx=16, pady=(4, 12), anchor="w")

        # ── Profiles card ──
        card4 = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card4.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(card4, text="Profiles", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkFrame(card4, fg_color=BORDER, height=1).pack(fill="x", padx=16)

        pr1 = ctk.CTkFrame(card4, fg_color="transparent"); pr1.pack(fill="x", padx=16, pady=(8, 0))
        self.profile_sel = ctk.CTkOptionMenu(pr1, values=ProfileManager.list_profiles() or ["(none)"],
            width=150, height=28, fg_color=SURFACE_2, button_color=ACCENT, button_hover_color=ACCENT_H,
            text_color=TEXT, dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
            dropdown_hover_color=SURFACE_2, font=ctk.CTkFont(size=11), corner_radius=6)
        self.profile_sel.pack(side="left")

        pr2 = ctk.CTkFrame(card4, fg_color="transparent"); pr2.pack(fill="x", padx=16, pady=(8, 12))
        self.profile_name = ctk.CTkEntry(pr2, placeholder_text="Profile name", width=140, height=28,
            fg_color=SURFACE_2, border_color=GLOW, text_color=TEXT, font=ctk.CTkFont(size=11), corner_radius=6)
        self.profile_name.pack(side="left")
        ctk.CTkButton(pr2, text="Save", font=ctk.CTkFont(size=10, weight="bold"), width=44, height=28,
            fg_color=ACCENT, hover_color=ACCENT_H, text_color="#FFF", corner_radius=6,
            command=self._save_profile).pack(side="left", padx=(6, 0))
        ctk.CTkButton(pr2, text="Load", font=ctk.CTkFont(size=10, weight="bold"), width=44, height=28,
            fg_color=SURFACE_2, hover_color=BORDER, text_color=CYAN, corner_radius=6,
            border_width=1, border_color=BORDER, command=self._load_profile).pack(side="left", padx=(4, 0))
        ctk.CTkButton(pr2, text="Del", font=ctk.CTkFont(size=10, weight="bold"), width=38, height=28,
            fg_color=SURFACE_2, hover_color=BORDER, text_color=RED, corner_radius=6,
            border_width=1, border_color=BORDER, command=self._del_profile).pack(side="left", padx=(4, 0))

        # ── General card ──
        card5 = ctk.CTkFrame(c, fg_color=SURFACE, corner_radius=14, border_width=1, border_color=GLOW)
        card5.pack(fill="x", pady=(0, 8))
        g1 = ctk.CTkFrame(card5, fg_color="transparent"); g1.pack(fill="x", padx=16, pady=12)
        self.on_top_var = ctk.StringVar(value="on")
        ctk.CTkSwitch(g1, text="Always on top", font=ctk.CTkFont(size=11), text_color=TEXT_2,
            variable=self.on_top_var, onvalue="on", offvalue="off",
            button_color=ACCENT, button_hover_color=ACCENT_H, fg_color=SURFACE_2,
            progress_color=ACCENT, height=22,
            command=lambda: self.attributes("-topmost", self.on_top_var.get() == "on")).pack(side="left")

    # ─── LOG ───
    def _build_log(self):
        log_frame = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        log_frame.pack(fill="x", side="bottom")
        ctk.CTkLabel(log_frame, text="Activity", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=TEXT_DIM).pack(anchor="w", padx=12, pady=(6, 2))
        self.log_text = ctk.CTkTextbox(log_frame, fg_color=SURFACE_2, text_color=TEXT_DIM,
            font=ctk.CTkFont(family="Consolas", size=9), corner_radius=6, height=60, border_width=0)
        self.log_text.pack(fill="x", padx=8, pady=(0, 6))
        self.log_text.configure(state="disabled")

    # ─── STATUS BAR ───
    def _build_status_bar(self):
        ctk.CTkFrame(self, fg_color=GLOW, height=1, corner_radius=0).pack(fill="x", side="bottom")
        bar = ctk.CTkFrame(self, fg_color=SURFACE, height=30, corner_radius=0)
        bar.pack(fill="x", side="bottom"); bar.pack_propagate(False)

        self.stat_presses = ctk.CTkLabel(bar, text="0 presses", font=ctk.CTkFont(size=9), text_color=TEXT_DIM)
        self.stat_presses.pack(side="left", padx=10)
        self.stat_clicks = ctk.CTkLabel(bar, text="0 clicks", font=ctk.CTkFont(size=9), text_color=TEXT_DIM)
        self.stat_clicks.pack(side="left", padx=4)
        self.session_lbl = ctk.CTkLabel(bar, text="00:00", font=ctk.CTkFont(family="Consolas", size=9), text_color=TEXT_DIM)
        self.session_lbl.pack(side="right", padx=10)
        self.timer_status = ctk.CTkLabel(bar, text="", font=ctk.CTkFont(size=9), text_color=ORANGE)
        self.timer_status.pack(side="right", padx=4)

    # ══════════════════════════════════════════
    #  HELPERS
    # ══════════════════════════════════════════

    def _mini_stat(self, parent, label, value, color, col):
        card = ctk.CTkFrame(parent, fg_color=SURFACE, corner_radius=12, border_width=1, border_color=GLOW, height=62)
        card.grid(row=0, column=col, sticky="nsew", padx=4); card.pack_propagate(False)
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=9, weight="bold"), text_color=TEXT_DIM).pack(pady=(10, 0))
        lbl = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
        lbl.pack(pady=(2, 0)); return lbl

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _tick_session(self):
        elapsed = int(time.time() - self.session_start)
        m, s = divmod(elapsed, 60); h, m = divmod(m, 60)
        self.session_lbl.configure(text=f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}")
        self.after(1000, self._tick_session)

    def _tick_cursor(self):
        pt = w.POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        self.cursor_lbl.configure(text=f"X: {pt.x}  Y: {pt.y}")
        self.after(50, self._tick_cursor)

    def _new_stop_event(self):
        ev = threading.Event()
        self.stop_events.append(ev)
        return ev

    # ══════════════════════════════════════════
    #  PANIC STOP
    # ══════════════════════════════════════════

    def _panic_stop(self):
        for ev in self.stop_events:
            ev.set()
        if self.key_running: self._stop_key()
        if self.click_running: self._stop_click()
        if self.afk_running: self._stop_afk()
        if self.combo_running: self._stop_combo()
        self._log("PANIC STOP — all macros halted")

    # ══════════════════════════════════════════
    #  HOTKEY LISTENER
    # ══════════════════════════════════════════

    def _hotkey_listener(self):
        prev_hk = False; prev_pk = False
        while True:
            # Toggle hotkey
            hk = ctypes.windll.user32.GetAsyncKeyState(self.hotkey_vk) & 0x8000 != 0
            if hk and not prev_hk:
                self.after(0, self._hotkey_toggle)
            prev_hk = hk
            # Panic key
            pk = ctypes.windll.user32.GetAsyncKeyState(self.panic_vk) & 0x8000 != 0
            if pk and not prev_pk:
                self.after(0, self._panic_stop)
            prev_pk = pk
            time.sleep(0.04)

    def _hotkey_toggle(self):
        if self.key_running or self.click_running:
            if self.key_running: self._stop_key()
            if self.click_running: self._stop_click()
        else:
            self._start_key()

    def _on_hotkey_change(self, v):
        self.hotkey_vk = HOTKEY_MAP[v]
    def _on_panic_change(self, v):
        self.panic_vk = HOTKEY_MAP[v]

    # ══════════════════════════════════════════
    #  AUTO KEY LOGIC
    # ══════════════════════════════════════════

    def _get_keys(self):
        multi = self.multi_key.get().strip()
        if multi:
            keys = [k.strip().capitalize() for k in multi.split(",") if k.strip().capitalize() in KEYS]
            if keys: return keys
        return [self.key_sel.get()]

    def _toggle_key(self):
        if self.key_running: self._stop_key()
        else: self._start_key()

    def _start_key(self):
        self.key_running = True; self.key_count = 0
        self.active_keys = self._get_keys()
        mode = self.key_mode.get()
        self.key_btn.configure(text="STOP", fg_color=RED, hover_color=RED_H)
        self.key_dot.configure(fg_color=GREEN)
        self.key_status.configure(text="Running", text_color=GREEN)
        self._log(f"Key: {', '.join(self.active_keys)} ({mode})")
        ev = self._new_stop_event()
        if mode == "Hold":
            threading.Thread(target=self._key_hold, args=(ev,), daemon=True).start()
        else:
            threading.Thread(target=self._key_spam, args=(ev,), daemon=True).start()

    def _stop_key(self):
        was_hold = self.key_holding; self.key_running = False; self.key_holding = False
        if was_hold:
            for k in self.active_keys:
                vk, sc = KEYS[k]; InputEngine.key_up(vk, sc)
        self.key_btn.configure(text="START", fg_color=ACCENT, hover_color=ACCENT_H)
        self.key_dot.configure(fg_color=TEXT_OFF)
        self.key_status.configure(text="Idle", text_color=TEXT_DIM)

    def _key_spam(self, ev):
        while self.key_running and not ev.is_set():
            for k in self.active_keys:
                if not self.key_running or ev.is_set(): break
                vk, sc = KEYS[k]; InputEngine.key_press(vk, sc)
                self.key_count += 1
            self.after(0, lambda: self.key_stat_count.configure(text=f"{self.key_count:,}"))
            self.after(0, lambda: self.stat_presses.configure(text=f"{self.key_count:,} presses"))
            delay = 1.0 / max(1, int(self.key_speed.get()))
            if self.key_human_var.get() == "on": delay *= random.uniform(0.7, 1.3)
            sleep_check(delay, ev)

    def _key_hold(self, ev):
        self.key_holding = True
        for k in self.active_keys:
            vk, sc = KEYS[k]; InputEngine.key_down(vk, sc)
        while self.key_running and not ev.is_set():
            time.sleep(0.05)

    # ══════════════════════════════════════════
    #  AUTO CLICK LOGIC
    # ══════════════════════════════════════════

    def _toggle_click(self):
        if self.click_running: self._stop_click()
        else: self._start_click()

    def _start_click(self):
        self.click_running = True; self.click_count = 0
        self.click_btn.configure(text="STOP", fg_color=RED, hover_color=RED_H, text_color="#FFF")
        self.click_dot.configure(fg_color=GREEN)
        self.click_status.configure(text="Running", text_color=GREEN)
        self._log(f"Clicker: {self.click_type.get()}")
        ev = self._new_stop_event()
        threading.Thread(target=self._click_loop, args=(ev,), daemon=True).start()

    def _stop_click(self):
        self.click_running = False
        self.click_btn.configure(text="START", fg_color=CYAN, hover_color=CYAN_H, text_color="#0A0A0F")
        self.click_dot.configure(fg_color=TEXT_OFF)
        self.click_status.configure(text="Idle", text_color=TEXT_DIM)

    def _click_loop(self, ev):
        burst = self.burst_var.get() == "on"
        try: burst_max = int(self.burst_count.get()) if burst else 0
        except: burst_max = 10

        while self.click_running and not ev.is_set():
            if self.fixed_var.get() == "on":
                try:
                    x, y = int(self.pos_x.get()), int(self.pos_y.get())
                    InputEngine.mouse_move_abs(x, y); time.sleep(0.005)
                except: pass
            btn = "left" if self.click_type.get() == "Left" else "right"
            InputEngine.mouse_click(btn)
            self.click_count += 1
            self.after(0, lambda: self.click_stat_count.configure(text=f"{self.click_count:,}"))
            self.after(0, lambda: self.stat_clicks.configure(text=f"{self.click_count:,} clicks"))
            if burst and self.click_count >= burst_max:
                self.after(0, self._stop_click)
                self._log(f"Burst done: {burst_max} clicks")
                return
            delay = 1.0 / max(1, int(self.click_speed.get()))
            if self.click_human_var.get() == "on": delay *= random.uniform(0.7, 1.3)
            sleep_check(delay, ev)

    def _pick_pos(self):
        self._log("Pick position: click in 3 seconds...")
        def do():
            time.sleep(3)
            pt = w.POINT(); ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            self.pos_x.delete(0, "end"); self.pos_x.insert(0, str(pt.x))
            self.pos_y.delete(0, "end"); self.pos_y.insert(0, str(pt.y))
            self._log(f"Position: {pt.x}, {pt.y}")
        threading.Thread(target=do, daemon=True).start()

    # ══════════════════════════════════════════
    #  ANTI-AFK LOGIC
    # ══════════════════════════════════════════

    def _toggle_afk(self):
        if self.afk_running: self._stop_afk()
        else: self._start_afk()

    def _start_afk(self):
        self.afk_running = True
        self.afk_btn.configure(text="STOP ANTI-AFK", fg_color=RED, hover_color=RED_H, text_color="#FFF")
        self.afk_dot.configure(fg_color=GREEN)
        self._log("Anti-AFK started")
        ev = self._new_stop_event()
        threading.Thread(target=self._afk_loop, args=(ev,), daemon=True).start()

    def _stop_afk(self):
        self.afk_running = False
        self.afk_btn.configure(text="START ANTI-AFK", fg_color=GREEN, hover_color="#00C853", text_color="#0A0A0F")
        self.afk_dot.configure(fg_color=TEXT_OFF)

    def _afk_loop(self, ev):
        while self.afk_running and not ev.is_set():
            if self.afk_spin_var.get() == "on":
                InputEngine.mouse_down("right")
                for _ in range(20):
                    if ev.is_set(): break
                    InputEngine.mouse_move_relative(random.randint(3, 8), random.randint(-2, 2))
                    time.sleep(0.05)
                InputEngine.mouse_up("right")
                sleep_check(random.uniform(0.5, 1.5), ev)

            if self.afk_wasd_var.get() == "on" and not ev.is_set():
                key = random.choice(["W", "A", "S", "D"])
                vk, sc = KEYS[key]
                InputEngine.key_down(vk, sc)
                sleep_check(random.uniform(0.3, 1.2), ev)
                InputEngine.key_up(vk, sc)

            if self.afk_jump_var.get() == "on" and not ev.is_set():
                vk, sc = KEYS["Space"]
                InputEngine.key_press(vk, sc)
                sleep_check(random.uniform(1.5, 4.0), ev)

            if self.afk_jitter_var.get() == "on" and not ev.is_set():
                InputEngine.mouse_move_relative(random.randint(-4, 4), random.randint(-4, 4))

            sleep_check(random.uniform(1.0, 3.0), ev)

    # ══════════════════════════════════════════
    #  COMBO LOGIC
    # ══════════════════════════════════════════

    def _combo_add(self):
        key = self.combo_key_sel.get()
        try: delay = int(self.combo_delay.get())
        except: delay = 100
        self.combo_steps.append({"key": key, "delay": delay})
        self._refresh_combo_list()

    def _combo_clear(self):
        self.combo_steps.clear()
        self._refresh_combo_list()

    def _refresh_combo_list(self):
        for w_lbl in self.combo_labels:
            w_lbl.destroy()
        self.combo_labels.clear()

        if not self.combo_steps:
            lbl = ctk.CTkLabel(self.combo_list_frame, text="No steps added",
                font=ctk.CTkFont(size=11), text_color=TEXT_OFF)
            lbl.pack(pady=10); self.combo_labels.append(lbl)
            return

        for i, step in enumerate(self.combo_steps):
            txt = f"  {i+1}. Press [{step['key']}]  →  wait {step['delay']}ms"
            lbl = ctk.CTkLabel(self.combo_list_frame, text=txt,
                font=ctk.CTkFont(family="Consolas", size=11), text_color=TEXT_2, anchor="w")
            lbl.pack(fill="x", padx=4, pady=1)
            self.combo_labels.append(lbl)

    def _toggle_combo(self):
        if self.combo_running: self._stop_combo()
        else: self._start_combo()

    def _start_combo(self):
        if not self.combo_steps:
            self._log("No combo steps!"); return
        self.combo_running = True
        self.combo_btn.configure(text="STOP COMBO", fg_color=RED, hover_color=RED_H, text_color="#FFF")
        self.combo_dot.configure(fg_color=GREEN)
        self._log(f"Combo started ({len(self.combo_steps)} steps)")
        ev = self._new_stop_event()
        threading.Thread(target=self._combo_loop, args=(ev,), daemon=True).start()

    def _stop_combo(self):
        self.combo_running = False
        self.combo_btn.configure(text="START COMBO", fg_color=ORANGE, hover_color="#FFB347", text_color="#0A0A0F")
        self.combo_dot.configure(fg_color=TEXT_OFF)

    def _combo_loop(self, ev):
        while self.combo_running and not ev.is_set():
            for step in self.combo_steps:
                if not self.combo_running or ev.is_set(): return
                vk, sc = KEYS[step["key"]]
                InputEngine.key_press(vk, sc)
                sleep_check(step["delay"] / 1000.0, ev)
            if self.combo_loop_var.get() != "on":
                self.after(0, self._stop_combo)
                self._log("Combo finished (one-shot)")
                return

    # ══════════════════════════════════════════
    #  SESSION TIMER
    # ══════════════════════════════════════════

    def _start_timer(self):
        try: mins = int(self.timer_entry.get())
        except: mins = 30
        self.timer_remaining = mins * 60
        self.timer_active = True
        self._log(f"Timer set: {mins} minutes")
        ev = self._new_stop_event()
        threading.Thread(target=self._timer_loop, args=(ev,), daemon=True).start()

    def _cancel_timer(self):
        self.timer_active = False
        self.timer_lbl.configure(text="Cancelled", text_color=RED)
        self.timer_status.configure(text="")
        self._log("Timer cancelled")

    def _timer_loop(self, ev):
        while self.timer_remaining > 0 and self.timer_active and not ev.is_set():
            m, s = divmod(self.timer_remaining, 60)
            txt = f"{m:02}:{s:02}"
            self.after(0, lambda t=txt: self.timer_lbl.configure(text=t, text_color=ORANGE))
            self.after(0, lambda t=txt: self.timer_status.configure(text=f"Timer: {t}"))
            time.sleep(1)
            self.timer_remaining -= 1

        if self.timer_active and self.timer_remaining <= 0:
            self.timer_active = False
            self.after(0, self._panic_stop)
            self.after(0, lambda: self.timer_lbl.configure(text="Done!", text_color=GREEN))
            self.after(0, lambda: self.timer_status.configure(text=""))
            self.after(0, lambda: self._log("Timer expired — all macros stopped"))
            try: winsound.Beep(1000, 300); winsound.Beep(1200, 300); winsound.Beep(1500, 500)
            except: pass

    # ══════════════════════════════════════════
    #  CROSSHAIR OVERLAY
    # ══════════════════════════════════════════

    def _toggle_crosshair(self):
        if self.cross_var.get() == "on":
            self._show_crosshair()
        else:
            self._hide_crosshair()

    def _show_crosshair(self):
        if self.crosshair_win: self._hide_crosshair()

        import tkinter as tk
        colors = {"Red": "#FF0000", "Green": "#00FF00", "Cyan": "#00FFFF", "Yellow": "#FFFF00", "White": "#FFFFFF"}
        color = colors.get(self.cross_color.get(), "#FF0000")
        size = int(self.cross_size.get())
        win_size = size * 4 + 4
        chroma = "#010101"

        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = sw // 2 - win_size // 2; y = sh // 2 - win_size // 2

        self.crosshair_win = tk.Toplevel(self)
        self.crosshair_win.overrideredirect(True)
        self.crosshair_win.attributes("-topmost", True)
        self.crosshair_win.attributes("-transparentcolor", chroma)
        self.crosshair_win.geometry(f"{win_size}x{win_size}+{x}+{y}")
        self.crosshair_win.configure(bg=chroma)

        # Make click-through on Windows
        hwnd = ctypes.windll.user32.FindWindowW(None, None)
        # Use the winfo_id approach
        try:
            hwnd = self.crosshair_win.winfo_id()
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex_style | 0x80000 | 0x20)  # WS_EX_LAYERED | WS_EX_TRANSPARENT
        except: pass

        canvas = tk.Canvas(self.crosshair_win, width=win_size, height=win_size, bg=chroma, highlightthickness=0)
        canvas.pack()
        cx, cy = win_size // 2, win_size // 2
        # Draw cross
        canvas.create_line(cx - size, cy, cx + size, cy, fill=color, width=2)
        canvas.create_line(cx, cy - size, cx, cy + size, fill=color, width=2)
        # Center dot
        canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, fill=color, outline=color)

        self._log("Crosshair enabled")

    def _hide_crosshair(self):
        if self.crosshair_win:
            self.crosshair_win.destroy()
            self.crosshair_win = None
            self._log("Crosshair disabled")

    # ══════════════════════════════════════════
    #  PROFILES
    # ══════════════════════════════════════════

    def _get_current_config(self):
        return {
            "key": self.key_sel.get(), "key_speed": int(self.key_speed.get()),
            "key_mode": self.key_mode.get(), "key_humanize": self.key_human_var.get(),
            "multi_key": self.multi_key.get(),
            "click_type": self.click_type.get(), "click_speed": int(self.click_speed.get()),
            "click_humanize": self.click_human_var.get(),
            "burst": self.burst_var.get(), "burst_count": self.burst_count.get(),
            "afk_spin": self.afk_spin_var.get(), "afk_wasd": self.afk_wasd_var.get(),
            "afk_jump": self.afk_jump_var.get(), "afk_jitter": self.afk_jitter_var.get(),
            "combo_steps": self.combo_steps,
            "hotkey": self.hotkey_sel.get(), "panic_key": self.panic_sel.get(),
        }

    def _apply_config(self, cfg):
        try:
            self.key_sel.set(cfg.get("key", "Space"))
            self.key_speed.set(cfg.get("key_speed", 10))
            self.key_mode.set(cfg.get("key_mode", "Spam"))
            self.key_human_var.set(cfg.get("key_humanize", "off"))
            self.multi_key.delete(0, "end"); self.multi_key.insert(0, cfg.get("multi_key", ""))
            self.click_type.set(cfg.get("click_type", "Left"))
            self.click_speed.set(cfg.get("click_speed", 10))
            self.click_human_var.set(cfg.get("click_humanize", "off"))
            self.burst_var.set(cfg.get("burst", "off"))
            self.burst_count.delete(0, "end"); self.burst_count.insert(0, cfg.get("burst_count", "10"))
            self.afk_spin_var.set(cfg.get("afk_spin", "on"))
            self.afk_wasd_var.set(cfg.get("afk_wasd", "on"))
            self.afk_jump_var.set(cfg.get("afk_jump", "off"))
            self.afk_jitter_var.set(cfg.get("afk_jitter", "off"))
            self.combo_steps = cfg.get("combo_steps", [])
            self._refresh_combo_list()
            self.hotkey_sel.set(cfg.get("hotkey", "F6"))
            self._on_hotkey_change(cfg.get("hotkey", "F6"))
            self.panic_sel.set(cfg.get("panic_key", "Escape"))
            self._on_panic_change(cfg.get("panic_key", "Escape"))
        except Exception as e:
            self._log(f"Profile load error: {e}")

    def _save_profile(self):
        name = self.profile_name.get().strip()
        if not name: self._log("Enter a profile name"); return
        ProfileManager.save(name, self._get_current_config())
        self._refresh_profiles()
        self._log(f"Profile saved: {name}")

    def _load_profile(self):
        name = self.profile_sel.get()
        if name == "(none)": return
        try:
            cfg = ProfileManager.load(name)
            self._apply_config(cfg)
            self._log(f"Profile loaded: {name}")
        except Exception as e:
            self._log(f"Load error: {e}")

    def _del_profile(self):
        name = self.profile_sel.get()
        if name == "(none)": return
        ProfileManager.delete(name)
        self._refresh_profiles()
        self._log(f"Profile deleted: {name}")

    def _refresh_profiles(self):
        profiles = ProfileManager.list_profiles() or ["(none)"]
        self.profile_sel.configure(values=profiles)
        self.profile_sel.set(profiles[0])


if __name__ == "__main__":
    app = InvexClicker()
    app.mainloop()
