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
from PIL import Image

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
#  InputEngine
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
        inp.union.mi.dwFlags = 0x0001
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
#  Design System v5 — Sidebar + Depth
# ══════════════════════════════════════════════════════

# 4-level depth system (Proxima-style)
D0 = "#0a0a0a"    # Void — window bg
D1 = "#0f0f0f"    # Surface — sidebar, cards
D2 = "#161616"    # Raised — inner containers
D3 = "#1e1e1e"    # Elevated — inputs, hover bg

# Interactive
BTN     = "#2b2d31"    # Button default
BTN_H   = "#3b3d41"    # Button hover

# Accent — single hero color + support
ACCENT  = "#4a9eff"    # Primary blue
ACCENT_H= "#5eb0ff"    # Blue hover
ACCENT_D= "#2b5a8f"    # Blue dark / pressed

# Support accents (used sparingly)
GREEN   = "#34d399"
GREEN_H = "#6ee7b7"
RED     = "#ef4444"
RED_H   = "#f87171"
ORANGE  = "#fb923c"
ORANGE_H= "#fdba74"

# Text — 4 levels
T1 = "#ffffff"     # Primary / headings
T2 = "#c9d1d9"    # Body text
T3 = "#8a8a8a"    # Secondary / labels
T4 = "#5a5a5a"    # Muted / disabled

# ══════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════

def sleep_check(delay, event):
    elapsed = 0
    while elapsed < delay and not event.is_set():
        step = min(0.01, delay - elapsed)
        time.sleep(step)
        elapsed += step

ctk.set_appearance_mode("dark")

# ══════════════════════════════════════════════════════
#  MAIN APP — Sidebar Layout
# ══════════════════════════════════════════════════════

class InvexClicker(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Invex Clicker")
        self.geometry("720x600")
        self.resizable(False, False)
        self.configure(fg_color=D0)
        self.attributes("-topmost", True)

        # Window icon
        ico_name = "roblox_alt_macos_bigsur_icon_189774.ico"
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ico_name)
        if not os.path.exists(icon_path) and hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, ico_name)
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
            self.after(200, lambda: self.iconbitmap(icon_path))
        self._icon_path = icon_path

        # State
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
        self.hotkey_vk = 0x75
        self.panic_vk = 0x1B
        self.nav_buttons = {}
        self.pages = {}
        self.current_page = None

        self._build_sidebar()
        self._build_content_area()
        self._build_pages()
        self._show_page("key")
        self._tick_session()

        threading.Thread(target=self._hotkey_listener, daemon=True).start()

    # ─────────────────────────────────────────
    #  SIDEBAR
    # ─────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=D1, width=180, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Brand
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.pack(fill="x", padx=16, pady=(20, 6))

        # App icon from .ico file
        try:
            ico_img = Image.open(self._icon_path)
            ico_img = ico_img.resize((32, 32), Image.LANCZOS)
            self._sidebar_icon = ctk.CTkImage(light_image=ico_img, dark_image=ico_img, size=(32, 32))
            ctk.CTkLabel(brand, image=self._sidebar_icon, text="").pack(side="left")
        except Exception:
            icon = ctk.CTkFrame(brand, fg_color=ACCENT, width=32, height=32, corner_radius=8)
            icon.pack(side="left")

        tf = ctk.CTkFrame(brand, fg_color="transparent")
        tf.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(tf, text="INVEX", font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color=T1).pack(anchor="w")
        ctk.CTkLabel(tf, text="Clicker v5", font=ctk.CTkFont(size=10),
                     text_color=T4).pack(anchor="w")

        # Separator
        ctk.CTkFrame(self.sidebar, fg_color=D3, height=1).pack(fill="x", padx=16, pady=(16, 12))

        # Nav section label
        ctk.CTkLabel(self.sidebar, text="MACROS", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=T4).pack(anchor="w", padx=20, pady=(0, 4))

        # Nav items
        nav_items = [
            ("key",      "Auto Key",    "\u2328"),
            ("click",    "Auto Click",  "\u25CB"),
            ("afk",      "Anti-AFK",    "\u26A1"),
            ("combo",    "Combos",      "\u2263"),
        ]
        for page_id, label, ico in nav_items:
            self._nav_button(page_id, f" {ico}  {label}")

        ctk.CTkFrame(self.sidebar, fg_color=D3, height=1).pack(fill="x", padx=16, pady=(12, 12))
        ctk.CTkLabel(self.sidebar, text="SYSTEM", font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=T4).pack(anchor="w", padx=20, pady=(0, 4))
        self._nav_button("settings", " \u2699  Settings")

        # Bottom status area
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # Live stats at bottom of sidebar
        stats_frame = ctk.CTkFrame(self.sidebar, fg_color=D2, corner_radius=10)
        stats_frame.pack(fill="x", padx=12, pady=(0, 12))

        si = ctk.CTkFrame(stats_frame, fg_color="transparent")
        si.pack(fill="x", padx=12, pady=10)

        self.side_status_dot = ctk.CTkFrame(si, width=8, height=8, corner_radius=4, fg_color=T4)
        self.side_status_dot.pack(side="left")
        self.side_status_lbl = ctk.CTkLabel(si, text="Idle", font=ctk.CTkFont(size=10),
                                             text_color=T4)
        self.side_status_lbl.pack(side="left", padx=(6, 0))

        self.session_lbl = ctk.CTkLabel(si, text="00:00",
                                         font=ctk.CTkFont(family="Consolas", size=10),
                                         text_color=T4)
        self.session_lbl.pack(side="right")

        s2 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        s2.pack(fill="x", padx=12, pady=(0, 10))
        self.stat_presses = ctk.CTkLabel(s2, text="0 presses",
                                          font=ctk.CTkFont(size=9), text_color=T4)
        self.stat_presses.pack(side="left")
        self.stat_clicks = ctk.CTkLabel(s2, text="0 clicks",
                                         font=ctk.CTkFont(size=9), text_color=T4)
        self.stat_clicks.pack(side="right")

        self.timer_status = ctk.CTkLabel(self.sidebar, text="",
                                          font=ctk.CTkFont(size=9), text_color=ORANGE)
        self.timer_status.pack(pady=(0, 8))

    def _nav_button(self, page_id, label):
        btn = ctk.CTkButton(
            self.sidebar, text=label, anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent", hover_color=D3,
            text_color=T3, height=36, corner_radius=8,
            command=lambda p=page_id: self._show_page(p))
        btn.pack(fill="x", padx=10, pady=1)
        self.nav_buttons[page_id] = btn

    def _show_page(self, page_id):
        # Update nav highlight
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(fg_color=ACCENT, text_color=T1, hover_color=ACCENT_H)
            else:
                btn.configure(fg_color="transparent", text_color=T3, hover_color=D3)
        # Show/hide pages
        for pid, frame in self.pages.items():
            if pid == page_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        self.current_page = page_id

    # ─────────────────────────────────────────
    #  CONTENT AREA
    # ─────────────────────────────────────────
    def _build_content_area(self):
        # Thin accent line between sidebar and content
        ctk.CTkFrame(self, fg_color=D2, width=1, corner_radius=0).pack(side="left", fill="y")
        self.content = ctk.CTkFrame(self, fg_color=D0, corner_radius=0)
        self.content.pack(side="left", fill="both", expand=True)

    def _build_pages(self):
        for pid in ["key", "click", "afk", "combo", "settings"]:
            page = ctk.CTkFrame(self.content, fg_color=D0, corner_radius=0)
            self.pages[pid] = page
        self._build_key_page(self.pages["key"])
        self._build_click_page(self.pages["click"])
        self._build_afk_page(self.pages["afk"])
        self._build_combo_page(self.pages["combo"])
        self._build_settings_page(self.pages["settings"])

    # ─────────────────────────────────────────
    #  PAGE HEADER HELPER
    # ─────────────────────────────────────────
    def _page_header(self, parent, title, subtitle=""):
        hdr = ctk.CTkFrame(parent, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(hdr, text=title,
                     font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
                     text_color=T1).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(hdr, text=subtitle,
                         font=ctk.CTkFont(size=12), text_color=T4).pack(anchor="w", pady=(2, 0))

    def _card(self, parent, pady=(0, 0)):
        c = ctk.CTkFrame(parent, fg_color=D1, corner_radius=12, border_width=0)
        c.pack(fill="x", padx=24, pady=pady)
        return c

    def _row(self, parent, pady=(0, 0)):
        r = ctk.CTkFrame(parent, fg_color="transparent")
        r.pack(fill="x", padx=20, pady=pady)
        r.grid_columnconfigure(1, weight=1)
        return r

    def _label(self, parent, text):
        return ctk.CTkLabel(parent, text=text,
                            font=ctk.CTkFont(size=13), text_color=T2)

    # ══════════════════════════════════════════
    #  AUTO KEY PAGE
    # ══════════════════════════════════════════
    def _build_key_page(self, page):
        self._page_header(page, "Auto Key", "Spam or hold keys automatically")

        # Stats row
        sr = ctk.CTkFrame(page, fg_color="transparent")
        sr.pack(fill="x", padx=24, pady=(12, 0))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.key_stat_count = self._stat_chip(sr, "Presses", "0", ACCENT, 0)
        self.key_stat_speed = self._stat_chip(sr, "Speed", "10/s", T2, 1)
        self.key_stat_key = self._stat_chip(sr, "Key", "Space", T2, 2)

        # Config card
        card = self._card(page, pady=(12, 0))

        # Key
        r = self._row(card, pady=(16, 0))
        self._label(r, "Key").grid(row=0, column=0, sticky="w")
        self.key_sel = ctk.CTkOptionMenu(
            r, values=list(KEYS.keys()), width=120, height=32,
            fg_color=D3, button_color=BTN, button_hover_color=BTN_H,
            text_color=T1, dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=12), corner_radius=8,
            command=lambda v: self.key_stat_key.configure(text=v))
        self.key_sel.set("Space")
        self.key_sel.grid(row=0, column=1, sticky="e")

        # Mode
        r = self._row(card, pady=(10, 0))
        self._label(r, "Mode").grid(row=0, column=0, sticky="w")
        self.key_mode = ctk.CTkSegmentedButton(
            r, values=["Spam", "Hold"],
            font=ctk.CTkFont(size=12), fg_color=D3,
            selected_color=ACCENT, selected_hover_color=ACCENT_H,
            unselected_color=D3, unselected_hover_color=BTN_H,
            text_color=T1, corner_radius=8, height=32)
        self.key_mode.set("Spam")
        self.key_mode.grid(row=0, column=1, sticky="e")

        # Speed
        sf = ctk.CTkFrame(card, fg_color="transparent")
        sf.pack(fill="x", padx=20, pady=(14, 0))
        sft = ctk.CTkFrame(sf, fg_color="transparent")
        sft.pack(fill="x")
        ctk.CTkLabel(sft, text="Speed", font=ctk.CTkFont(size=13),
                     text_color=T2).pack(side="left")
        self.key_speed_lbl = ctk.CTkLabel(sft, text="10 /sec",
                                           font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                                           text_color=ACCENT)
        self.key_speed_lbl.pack(side="right")
        self.key_speed = ctk.CTkSlider(
            sf, from_=1, to=20, number_of_steps=19,
            button_color="#ffffff", button_hover_color=T2,
            fg_color=D3, progress_color=ACCENT, height=16)
        self.key_speed.set(10)
        self.key_speed.pack(fill="x", pady=(8, 0))
        self.key_speed.configure(command=lambda v: (
            self.key_speed_lbl.configure(text=f"{int(v)} /sec"),
            self.key_stat_speed.configure(text=f"{int(v)}/s")
        ))

        # Divider
        ctk.CTkFrame(card, fg_color=D2, height=1).pack(fill="x", padx=20, pady=(14, 0))

        # Humanize
        opts = ctk.CTkFrame(card, fg_color="transparent")
        opts.pack(fill="x", padx=20, pady=(12, 0))
        self.key_human_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(opts, text="Humanize timing", font=ctk.CTkFont(size=12),
                      text_color=T3, variable=self.key_human_var,
                      onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=ACCENT, height=24).pack(side="left")

        # Multi-key
        mk = ctk.CTkFrame(card, fg_color="transparent")
        mk.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(mk, text="Multi-Key", font=ctk.CTkFont(size=12),
                     text_color=T3).pack(side="left")
        self.multi_key = ctk.CTkEntry(
            mk, placeholder_text="e.g. E, F, Space", width=180, height=32,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=12), corner_radius=8,
            placeholder_text_color=T4)
        self.multi_key.pack(side="right")

        # Start
        self.key_btn = ctk.CTkButton(
            card, text="Start", font=ctk.CTkFont(size=14, weight="bold"),
            height=44, fg_color=ACCENT, hover_color=ACCENT_H, text_color=T1,
            corner_radius=10, command=self._toggle_key)
        self.key_btn.pack(fill="x", padx=20, pady=(16, 20))

    # ══════════════════════════════════════════
    #  AUTO CLICK PAGE
    # ══════════════════════════════════════════
    def _build_click_page(self, page):
        self._page_header(page, "Auto Click", "Click automatically at set speed")

        sr = ctk.CTkFrame(page, fg_color="transparent")
        sr.pack(fill="x", padx=24, pady=(12, 0))
        sr.grid_columnconfigure((0, 1, 2), weight=1)
        self.click_stat_count = self._stat_chip(sr, "Clicks", "0", ACCENT, 0)
        self.click_stat_speed = self._stat_chip(sr, "Speed", "10/s", T2, 1)
        self.click_stat_type = self._stat_chip(sr, "Button", "Left", T2, 2)

        card = self._card(page, pady=(12, 0))

        # Button type
        r = self._row(card, pady=(16, 0))
        self._label(r, "Button").grid(row=0, column=0, sticky="w")
        self.click_type = ctk.CTkSegmentedButton(
            r, values=["Left", "Right"],
            font=ctk.CTkFont(size=12), fg_color=D3,
            selected_color=ACCENT, selected_hover_color=ACCENT_H,
            unselected_color=D3, unselected_hover_color=BTN_H,
            text_color=T1, corner_radius=8, height=32,
            command=lambda v: self.click_stat_type.configure(text=v))
        self.click_type.set("Left")
        self.click_type.grid(row=0, column=1, sticky="e")

        # Speed
        sf = ctk.CTkFrame(card, fg_color="transparent")
        sf.pack(fill="x", padx=20, pady=(14, 0))
        sft = ctk.CTkFrame(sf, fg_color="transparent")
        sft.pack(fill="x")
        ctk.CTkLabel(sft, text="Speed", font=ctk.CTkFont(size=13),
                     text_color=T2).pack(side="left")
        self.click_speed_lbl = ctk.CTkLabel(sft, text="10 /sec",
                                             font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                                             text_color=ACCENT)
        self.click_speed_lbl.pack(side="right")
        self.click_speed = ctk.CTkSlider(
            sf, from_=1, to=20, number_of_steps=19,
            button_color="#ffffff", button_hover_color=T2,
            fg_color=D3, progress_color=ACCENT, height=16)
        self.click_speed.set(10)
        self.click_speed.pack(fill="x", pady=(8, 0))
        self.click_speed.configure(command=lambda v: (
            self.click_speed_lbl.configure(text=f"{int(v)} /sec"),
            self.click_stat_speed.configure(text=f"{int(v)}/s")
        ))

        ctk.CTkFrame(card, fg_color=D2, height=1).pack(fill="x", padx=20, pady=(14, 0))

        # Options
        o1 = ctk.CTkFrame(card, fg_color="transparent")
        o1.pack(fill="x", padx=20, pady=(12, 0))
        self.click_human_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o1, text="Humanize timing", font=ctk.CTkFont(size=12),
                      text_color=T3, variable=self.click_human_var,
                      onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=ACCENT, height=24).pack(side="left")

        o2 = ctk.CTkFrame(card, fg_color="transparent")
        o2.pack(fill="x", padx=20, pady=(8, 0))
        self.burst_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o2, text="Burst mode", font=ctk.CTkFont(size=12),
                      text_color=T3, variable=self.burst_var,
                      onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=ACCENT, height=24).pack(side="left")
        self.burst_count = ctk.CTkEntry(
            o2, placeholder_text="10", width=60, height=30,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.burst_count.pack(side="right")
        ctk.CTkLabel(o2, text="Count:", font=ctk.CTkFont(size=10),
                     text_color=T4).pack(side="right", padx=(0, 6))

        o3 = ctk.CTkFrame(card, fg_color="transparent")
        o3.pack(fill="x", padx=20, pady=(8, 0))
        self.fixed_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(o3, text="Fixed position", font=ctk.CTkFont(size=12),
                      text_color=T3, variable=self.fixed_var,
                      onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=ACCENT, height=24).pack(side="left")

        coord = ctk.CTkFrame(card, fg_color="transparent")
        coord.pack(fill="x", padx=20, pady=(6, 0))
        ctk.CTkLabel(coord, text="X", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=T4).pack(side="left")
        self.pos_x = ctk.CTkEntry(
            coord, placeholder_text="960", width=60, height=28,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.pos_x.pack(side="left", padx=(4, 12))
        ctk.CTkLabel(coord, text="Y", font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=T4).pack(side="left")
        self.pos_y = ctk.CTkEntry(
            coord, placeholder_text="540", width=60, height=28,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.pos_y.pack(side="left", padx=(4, 12))
        ctk.CTkButton(
            coord, text="Pick", font=ctk.CTkFont(size=10, weight="bold"),
            width=50, height=28, fg_color=BTN, hover_color=BTN_H,
            text_color=ACCENT, corner_radius=8,
            command=self._pick_pos).pack(side="left")

        self.click_btn = ctk.CTkButton(
            card, text="Start", font=ctk.CTkFont(size=14, weight="bold"),
            height=44, fg_color=ACCENT, hover_color=ACCENT_H, text_color=T1,
            corner_radius=10, command=self._toggle_click)
        self.click_btn.pack(fill="x", padx=20, pady=(16, 20))

        # Cursor tracker
        cur = ctk.CTkFrame(page, fg_color=D1, corner_radius=10)
        cur.pack(fill="x", padx=24, pady=(10, 0))
        ci = ctk.CTkFrame(cur, fg_color="transparent")
        ci.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(ci, text="Cursor",
                     font=ctk.CTkFont(size=11), text_color=T4).pack(side="left")
        self.cursor_lbl = ctk.CTkLabel(
            ci, text="X: 0  Y: 0",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=ACCENT)
        self.cursor_lbl.pack(side="right")
        self._tick_cursor()

    # ══════════════════════════════════════════
    #  ANTI-AFK PAGE
    # ══════════════════════════════════════════
    def _build_afk_page(self, page):
        self._page_header(page, "Anti-AFK", "Keep your character moving to avoid kicks")

        card = self._card(page, pady=(16, 0))

        self.afk_spin_var = ctk.StringVar(value="on")
        self.afk_wasd_var = ctk.StringVar(value="on")
        self.afk_jump_var = ctk.StringVar(value="off")
        self.afk_jitter_var = ctk.StringVar(value="off")

        afk_opts = [
            ("Camera Spin",      "Slowly rotates camera",   self.afk_spin_var),
            ("Random Movement",  "Random W/A/S/D presses",  self.afk_wasd_var),
            ("Random Jump",      "Jumps at random intervals", self.afk_jump_var),
            ("Mouse Jitter",     "Tiny mouse movements",    self.afk_jitter_var),
        ]

        for i, (label, desc_text, var) in enumerate(afk_opts):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=(16 if i == 0 else 4, 0))

            opt = ctk.CTkFrame(row, fg_color=D2, corner_radius=10)
            opt.pack(fill="x")
            inner = ctk.CTkFrame(opt, fg_color="transparent")
            inner.pack(fill="x", padx=14, pady=12)

            ctk.CTkSwitch(inner, text="", variable=var, onvalue="on", offvalue="off",
                          button_color="#ffffff", button_hover_color=T2,
                          fg_color=D3, progress_color=ACCENT,
                          height=22, width=40).pack(side="left")

            tf = ctk.CTkFrame(inner, fg_color="transparent")
            tf.pack(side="left", padx=(12, 0))
            ctk.CTkLabel(tf, text=label, font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=T1).pack(anchor="w")
            ctk.CTkLabel(tf, text=desc_text, font=ctk.CTkFont(size=10),
                         text_color=T4).pack(anchor="w")

        self.afk_btn = ctk.CTkButton(
            card, text="Start Anti-AFK",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, fg_color=GREEN, hover_color=GREEN_H, text_color="#0a0a0a",
            corner_radius=10, command=self._toggle_afk)
        self.afk_btn.pack(fill="x", padx=20, pady=(16, 20))

    # ══════════════════════════════════════════
    #  COMBOS PAGE
    # ══════════════════════════════════════════
    def _build_combo_page(self, page):
        self._page_header(page, "Combos", "Build key sequences with delays")

        card = self._card(page, pady=(16, 0))

        # Sequence list
        self.combo_list_frame = ctk.CTkScrollableFrame(
            card, fg_color=D2, corner_radius=10,
            height=130, border_width=0)
        self.combo_list_frame.pack(fill="x", padx=20, pady=(16, 8))
        self.combo_labels = []

        # Add controls
        add_row = ctk.CTkFrame(card, fg_color="transparent")
        add_row.pack(fill="x", padx=20, pady=(4, 0))
        self.combo_key_sel = ctk.CTkOptionMenu(
            add_row, values=list(KEYS.keys()), width=90, height=32,
            fg_color=D3, button_color=BTN, button_hover_color=BTN_H,
            text_color=T1, dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=11), corner_radius=8)
        self.combo_key_sel.set("Z")
        self.combo_key_sel.pack(side="left")

        ctk.CTkLabel(add_row, text="Delay:", font=ctk.CTkFont(size=10),
                     text_color=T4).pack(side="left", padx=(14, 4))
        self.combo_delay = ctk.CTkEntry(
            add_row, placeholder_text="100ms", width=70, height=32,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.combo_delay.pack(side="left")

        ctk.CTkButton(
            add_row, text="+ Add", font=ctk.CTkFont(size=11, weight="bold"),
            width=60, height=32, fg_color=ACCENT, hover_color=ACCENT_H,
            text_color=T1, corner_radius=8, command=self._combo_add).pack(
                side="left", padx=(14, 0))
        ctk.CTkButton(
            add_row, text="Clear", font=ctk.CTkFont(size=11, weight="bold"),
            width=56, height=32, fg_color=BTN, hover_color=BTN_H,
            text_color=RED, corner_radius=8,
            command=self._combo_clear).pack(side="left", padx=(6, 0))

        # Loop
        loop_row = ctk.CTkFrame(card, fg_color="transparent")
        loop_row.pack(fill="x", padx=20, pady=(10, 0))
        self.combo_loop_var = ctk.StringVar(value="on")
        ctk.CTkSwitch(loop_row, text="Loop continuously",
                      font=ctk.CTkFont(size=12), text_color=T3,
                      variable=self.combo_loop_var, onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=ACCENT, height=24).pack(side="left")

        self.combo_btn = ctk.CTkButton(
            card, text="Start Combo",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, fg_color=ORANGE, hover_color=ORANGE_H, text_color="#0a0a0a",
            corner_radius=10, command=self._toggle_combo)
        self.combo_btn.pack(fill="x", padx=20, pady=(16, 20))

    # ══════════════════════════════════════════
    #  SETTINGS PAGE
    # ══════════════════════════════════════════
    def _build_settings_page(self, page):
        self._page_header(page, "Settings", "Hotkeys, timer, crosshair & profiles")

        scroll = ctk.CTkScrollableFrame(page, fg_color=D0, border_width=0)
        scroll.pack(fill="both", expand=True, padx=0, pady=(8, 0))

        # ── Hotkeys ──
        card1 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card1.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card1, text="Hotkeys", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))

        r = self._row(card1, pady=(0, 0))
        self._label(r, "Toggle Hotkey").grid(row=0, column=0, sticky="w")
        self.hotkey_sel = ctk.CTkOptionMenu(
            r, values=[k for k in HOTKEY_MAP if k != "Escape"],
            width=100, height=32, fg_color=D3, button_color=BTN,
            button_hover_color=BTN_H, text_color=T1,
            dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=11), corner_radius=8,
            command=self._on_hotkey_change)
        self.hotkey_sel.set("F6")
        self.hotkey_sel.grid(row=0, column=1, sticky="e")

        r = self._row(card1, pady=(8, 16))
        self._label(r, "Panic Key (stop all)").grid(row=0, column=0, sticky="w")
        self.panic_sel = ctk.CTkOptionMenu(
            r, values=list(HOTKEY_MAP.keys()),
            width=100, height=32, fg_color=D3, button_color=BTN,
            button_hover_color=BTN_H, text_color=T1,
            dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=11), corner_radius=8,
            command=self._on_panic_change)
        self.panic_sel.set("Escape")
        self.panic_sel.grid(row=0, column=1, sticky="e")

        # ── Timer ──
        card2 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card2.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card2, text="Session Timer", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))

        tr = ctk.CTkFrame(card2, fg_color="transparent")
        tr.pack(fill="x", padx=20)
        ctk.CTkLabel(tr, text="Auto-stop after (min):", font=ctk.CTkFont(size=12),
                     text_color=T3).pack(side="left")
        self.timer_entry = ctk.CTkEntry(
            tr, placeholder_text="30", width=60, height=32,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.timer_entry.pack(side="right")

        tb = ctk.CTkFrame(card2, fg_color="transparent")
        tb.pack(fill="x", padx=20, pady=(8, 16))
        self.timer_lbl = ctk.CTkLabel(tb, text="Not set",
                                       font=ctk.CTkFont(size=14, weight="bold"),
                                       text_color=T4)
        self.timer_lbl.pack(side="left")
        ctk.CTkButton(
            tb, text="Start", font=ctk.CTkFont(size=11, weight="bold"),
            width=70, height=32, fg_color=GREEN, hover_color=GREEN_H,
            text_color="#0a0a0a", corner_radius=8,
            command=self._start_timer).pack(side="right")
        ctk.CTkButton(
            tb, text="Cancel", font=ctk.CTkFont(size=11, weight="bold"),
            width=60, height=32, fg_color=BTN, hover_color=BTN_H,
            text_color=RED, corner_radius=8,
            command=self._cancel_timer).pack(side="right", padx=(0, 6))

        # ── Crosshair ──
        card3 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card3.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card3, text="Crosshair Overlay", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))

        cr1 = ctk.CTkFrame(card3, fg_color="transparent")
        cr1.pack(fill="x", padx=20)
        self.cross_var = ctk.StringVar(value="off")
        ctk.CTkSwitch(cr1, text="Enable crosshair", font=ctk.CTkFont(size=12),
                      text_color=T3, variable=self.cross_var,
                      onvalue="on", offvalue="off",
                      button_color="#ffffff", button_hover_color=T2,
                      fg_color=D3, progress_color=RED, height=24,
                      command=self._toggle_crosshair).pack(side="left")

        cr2 = ctk.CTkFrame(card3, fg_color="transparent")
        cr2.pack(fill="x", padx=20, pady=(8, 16))
        ctk.CTkLabel(cr2, text="Color", font=ctk.CTkFont(size=11),
                     text_color=T4).pack(side="left")
        self.cross_color = ctk.CTkOptionMenu(
            cr2, values=["Red", "Green", "Cyan", "Yellow", "White"],
            width=80, height=28, fg_color=D3, button_color=BTN,
            button_hover_color=BTN_H, text_color=T1,
            dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=10), corner_radius=8)
        self.cross_color.set("Red")
        self.cross_color.pack(side="left", padx=(8, 16))
        ctk.CTkLabel(cr2, text="Size", font=ctk.CTkFont(size=11),
                     text_color=T4).pack(side="left")
        self.cross_size = ctk.CTkSlider(
            cr2, from_=2, to=20, number_of_steps=18,
            button_color="#ffffff", button_hover_color=T2,
            fg_color=D3, progress_color=RED, height=14, width=100)
        self.cross_size.set(6)
        self.cross_size.pack(side="left", padx=(8, 0))

        # ── Profiles ──
        card4 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card4.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card4, text="Profiles", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))

        pr1 = ctk.CTkFrame(card4, fg_color="transparent")
        pr1.pack(fill="x", padx=20)
        self.profile_sel = ctk.CTkOptionMenu(
            pr1, values=ProfileManager.list_profiles() or ["(none)"],
            width=160, height=32, fg_color=D3, button_color=BTN,
            button_hover_color=BTN_H, text_color=T1,
            dropdown_fg_color=D2, dropdown_text_color=T2,
            dropdown_hover_color=D3, font=ctk.CTkFont(size=11), corner_radius=8)
        self.profile_sel.pack(side="left")

        pr2 = ctk.CTkFrame(card4, fg_color="transparent")
        pr2.pack(fill="x", padx=20, pady=(8, 16))
        self.profile_name = ctk.CTkEntry(
            pr2, placeholder_text="Profile name", width=150, height=32,
            fg_color=D3, border_width=0, text_color=T1,
            font=ctk.CTkFont(size=11), corner_radius=8)
        self.profile_name.pack(side="left")
        ctk.CTkButton(
            pr2, text="Save", font=ctk.CTkFont(size=10, weight="bold"),
            width=48, height=32, fg_color=ACCENT, hover_color=ACCENT_H,
            text_color=T1, corner_radius=8,
            command=self._save_profile).pack(side="left", padx=(8, 0))
        ctk.CTkButton(
            pr2, text="Load", font=ctk.CTkFont(size=10, weight="bold"),
            width=48, height=32, fg_color=BTN, hover_color=BTN_H,
            text_color=ACCENT, corner_radius=8,
            command=self._load_profile).pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            pr2, text="Del", font=ctk.CTkFont(size=10, weight="bold"),
            width=40, height=32, fg_color=BTN, hover_color=BTN_H,
            text_color=RED, corner_radius=8,
            command=self._del_profile).pack(side="left", padx=(4, 0))

        # ── General ──
        card5 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card5.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card5, text="General", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))
        g1 = ctk.CTkFrame(card5, fg_color="transparent")
        g1.pack(fill="x", padx=20, pady=(0, 16))
        self.on_top_var = ctk.StringVar(value="on")
        ctk.CTkSwitch(
            g1, text="Always on top", font=ctk.CTkFont(size=12), text_color=T3,
            variable=self.on_top_var, onvalue="on", offvalue="off",
            button_color="#ffffff", button_hover_color=T2,
            fg_color=D3, progress_color=ACCENT, height=24,
            command=lambda: self.attributes("-topmost", self.on_top_var.get() == "on")
        ).pack(side="left")

        # ── Activity Log ──
        card6 = ctk.CTkFrame(scroll, fg_color=D1, corner_radius=12)
        card6.pack(fill="x", padx=24, pady=(0, 10))
        ctk.CTkLabel(card6, text="Activity Log", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=T1).pack(anchor="w", padx=20, pady=(16, 8))
        self.log_text = ctk.CTkTextbox(
            card6, fg_color=D2, text_color=T4,
            font=ctk.CTkFont(family="Consolas", size=10),
            corner_radius=8, height=100, border_width=0)
        self.log_text.pack(fill="x", padx=20, pady=(0, 16))
        self.log_text.configure(state="disabled")

    # ══════════════════════════════════════════
    #  UI HELPERS
    # ══════════════════════════════════════════

    def _stat_chip(self, parent, label, value, color, col):
        card = ctk.CTkFrame(parent, fg_color=D1, corner_radius=10, height=60)
        card.grid(row=0, column=col, sticky="nsew", padx=4)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=label.upper(),
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=T4).pack(pady=(10, 0))
        lbl = ctk.CTkLabel(card, text=value,
                           font=ctk.CTkFont(size=18, weight="bold"),
                           text_color=color)
        lbl.pack(pady=(0, 0))
        return lbl

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _tick_session(self):
        elapsed = int(time.time() - self.session_start)
        m, s = divmod(elapsed, 60)
        h, m = divmod(m, 60)
        self.session_lbl.configure(text=f"{h}:{m:02}:{s:02}" if h else f"{m:02}:{s:02}")
        self.after(1000, self._tick_session)

    def _tick_cursor(self):
        pt = w.POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        self.cursor_lbl.configure(text=f"X: {pt.x}  Y: {pt.y}")
        self.after(50, self._tick_cursor)

    def _new_stop_event(self):
        ev = threading.Event()
        self.stop_events.append(ev)
        return ev

    def _update_sidebar_status(self, running, text):
        if running:
            self.side_status_dot.configure(fg_color=GREEN)
            self.side_status_lbl.configure(text=text, text_color=GREEN)
        else:
            any_running = self.key_running or self.click_running or self.afk_running or self.combo_running
            if not any_running:
                self.side_status_dot.configure(fg_color=T4)
                self.side_status_lbl.configure(text="Idle", text_color=T4)

    # ══════════════════════════════════════════
    #  PANIC / HOTKEY
    # ══════════════════════════════════════════

    def _panic_stop(self):
        for ev in self.stop_events:
            ev.set()
        if self.key_running:
            self._stop_key()
        if self.click_running:
            self._stop_click()
        if self.afk_running:
            self._stop_afk()
        if self.combo_running:
            self._stop_combo()
        self._log("PANIC STOP - all macros halted")

    def _hotkey_listener(self):
        prev_hk = False
        prev_pk = False
        while True:
            hk = ctypes.windll.user32.GetAsyncKeyState(self.hotkey_vk) & 0x8000 != 0
            if hk and not prev_hk:
                self.after(0, self._hotkey_toggle)
            prev_hk = hk
            pk = ctypes.windll.user32.GetAsyncKeyState(self.panic_vk) & 0x8000 != 0
            if pk and not prev_pk:
                self.after(0, self._panic_stop)
            prev_pk = pk
            time.sleep(0.04)

    def _hotkey_toggle(self):
        if self.key_running or self.click_running:
            if self.key_running:
                self._stop_key()
            if self.click_running:
                self._stop_click()
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
            keys = [k.strip().capitalize() for k in multi.split(",")
                    if k.strip().capitalize() in KEYS]
            if keys:
                return keys
        return [self.key_sel.get()]

    def _toggle_key(self):
        if self.key_running:
            self._stop_key()
        else:
            self._start_key()

    def _start_key(self):
        self.key_running = True
        self.key_count = 0
        self.active_keys = self._get_keys()
        mode = self.key_mode.get()
        self.key_btn.configure(text="Stop", fg_color=RED, hover_color=RED_H)
        self._update_sidebar_status(True, "Active")
        self._log(f"Key: {', '.join(self.active_keys)} ({mode})")
        ev = self._new_stop_event()
        if mode == "Hold":
            threading.Thread(target=self._key_hold, args=(ev,), daemon=True).start()
        else:
            threading.Thread(target=self._key_spam, args=(ev,), daemon=True).start()

    def _stop_key(self):
        was_hold = self.key_holding
        self.key_running = False
        self.key_holding = False
        if was_hold:
            for k in self.active_keys:
                vk, sc = KEYS[k]
                InputEngine.key_up(vk, sc)
        self.key_btn.configure(text="Start", fg_color=ACCENT, hover_color=ACCENT_H)
        self._update_sidebar_status(False, "")

    def _key_spam(self, ev):
        while self.key_running and not ev.is_set():
            for k in self.active_keys:
                if not self.key_running or ev.is_set():
                    break
                vk, sc = KEYS[k]
                InputEngine.key_press(vk, sc)
                self.key_count += 1
            self.after(0, lambda: self.key_stat_count.configure(text=f"{self.key_count:,}"))
            self.after(0, lambda: self.stat_presses.configure(
                text=f"{self.key_count:,} presses"))
            delay = 1.0 / max(1, int(self.key_speed.get()))
            if self.key_human_var.get() == "on":
                delay *= random.uniform(0.7, 1.3)
            sleep_check(delay, ev)

    def _key_hold(self, ev):
        self.key_holding = True
        for k in self.active_keys:
            vk, sc = KEYS[k]
            InputEngine.key_down(vk, sc)
        while self.key_running and not ev.is_set():
            time.sleep(0.05)

    # ══════════════════════════════════════════
    #  AUTO CLICK LOGIC
    # ══════════════════════════════════════════

    def _toggle_click(self):
        if self.click_running:
            self._stop_click()
        else:
            self._start_click()

    def _start_click(self):
        self.click_running = True
        self.click_count = 0
        self.click_btn.configure(text="Stop", fg_color=RED, hover_color=RED_H, text_color=T1)
        self._update_sidebar_status(True, "Active")
        self._log(f"Clicker: {self.click_type.get()}")
        ev = self._new_stop_event()
        threading.Thread(target=self._click_loop, args=(ev,), daemon=True).start()

    def _stop_click(self):
        self.click_running = False
        self.click_btn.configure(text="Start", fg_color=ACCENT, hover_color=ACCENT_H, text_color=T1)
        self._update_sidebar_status(False, "")

    def _click_loop(self, ev):
        burst = self.burst_var.get() == "on"
        try:
            burst_max = int(self.burst_count.get()) if burst else 0
        except Exception:
            burst_max = 10

        while self.click_running and not ev.is_set():
            if self.fixed_var.get() == "on":
                try:
                    x, y = int(self.pos_x.get()), int(self.pos_y.get())
                    InputEngine.mouse_move_abs(x, y)
                    time.sleep(0.005)
                except Exception:
                    pass
            btn = "left" if self.click_type.get() == "Left" else "right"
            InputEngine.mouse_click(btn)
            self.click_count += 1
            self.after(0, lambda: self.click_stat_count.configure(
                text=f"{self.click_count:,}"))
            self.after(0, lambda: self.stat_clicks.configure(
                text=f"{self.click_count:,} clicks"))
            if burst and self.click_count >= burst_max:
                self.after(0, self._stop_click)
                self._log(f"Burst done: {burst_max} clicks")
                return
            delay = 1.0 / max(1, int(self.click_speed.get()))
            if self.click_human_var.get() == "on":
                delay *= random.uniform(0.7, 1.3)
            sleep_check(delay, ev)

    def _pick_pos(self):
        self._log("Pick position: click in 3 seconds...")
        def do():
            time.sleep(3)
            pt = w.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            self.pos_x.delete(0, "end")
            self.pos_x.insert(0, str(pt.x))
            self.pos_y.delete(0, "end")
            self.pos_y.insert(0, str(pt.y))
            self._log(f"Position: {pt.x}, {pt.y}")
        threading.Thread(target=do, daemon=True).start()

    # ══════════════════════════════════════════
    #  ANTI-AFK LOGIC
    # ══════════════════════════════════════════

    def _toggle_afk(self):
        if self.afk_running:
            self._stop_afk()
        else:
            self._start_afk()

    def _start_afk(self):
        self.afk_running = True
        self.afk_btn.configure(text="Stop Anti-AFK", fg_color=RED,
                               hover_color=RED_H, text_color=T1)
        self._update_sidebar_status(True, "Anti-AFK")
        self._log("Anti-AFK started")
        ev = self._new_stop_event()
        threading.Thread(target=self._afk_loop, args=(ev,), daemon=True).start()

    def _stop_afk(self):
        self.afk_running = False
        self.afk_btn.configure(text="Start Anti-AFK", fg_color=GREEN,
                               hover_color=GREEN_H, text_color="#0a0a0a")
        self._update_sidebar_status(False, "")

    def _afk_loop(self, ev):
        while self.afk_running and not ev.is_set():
            if self.afk_spin_var.get() == "on":
                InputEngine.mouse_down("right")
                for _ in range(20):
                    if ev.is_set():
                        break
                    InputEngine.mouse_move_relative(random.randint(3, 8),
                                                    random.randint(-2, 2))
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
                InputEngine.mouse_move_relative(random.randint(-4, 4),
                                                random.randint(-4, 4))

            sleep_check(random.uniform(1.0, 3.0), ev)

    # ══════════════════════════════════════════
    #  COMBO LOGIC
    # ══════════════════════════════════════════

    def _combo_add(self):
        key = self.combo_key_sel.get()
        try:
            delay = int(self.combo_delay.get())
        except Exception:
            delay = 100
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
            lbl = ctk.CTkLabel(self.combo_list_frame, text="No steps added yet",
                               font=ctk.CTkFont(size=11), text_color=T4)
            lbl.pack(pady=10)
            self.combo_labels.append(lbl)
            return

        for i, step in enumerate(self.combo_steps):
            txt = f"  {i+1}. [{step['key']}]  \u2192  {step['delay']}ms"
            lbl = ctk.CTkLabel(self.combo_list_frame, text=txt,
                               font=ctk.CTkFont(family="Consolas", size=11),
                               text_color=T3, anchor="w")
            lbl.pack(fill="x", padx=4, pady=1)
            self.combo_labels.append(lbl)

    def _toggle_combo(self):
        if self.combo_running:
            self._stop_combo()
        else:
            self._start_combo()

    def _start_combo(self):
        if not self.combo_steps:
            self._log("No combo steps!")
            return
        self.combo_running = True
        self.combo_btn.configure(text="Stop Combo", fg_color=RED,
                                 hover_color=RED_H, text_color=T1)
        self._update_sidebar_status(True, "Combo")
        self._log(f"Combo started ({len(self.combo_steps)} steps)")
        ev = self._new_stop_event()
        threading.Thread(target=self._combo_loop, args=(ev,), daemon=True).start()

    def _stop_combo(self):
        self.combo_running = False
        self.combo_btn.configure(text="Start Combo", fg_color=ORANGE,
                                 hover_color=ORANGE_H, text_color="#0a0a0a")
        self._update_sidebar_status(False, "")

    def _combo_loop(self, ev):
        while self.combo_running and not ev.is_set():
            for step in self.combo_steps:
                if not self.combo_running or ev.is_set():
                    return
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
        try:
            mins = int(self.timer_entry.get())
        except Exception:
            mins = 30
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
            self.after(0, lambda: self._log("Timer expired - all macros stopped"))
            try:
                winsound.Beep(1000, 300)
                winsound.Beep(1200, 300)
                winsound.Beep(1500, 500)
            except Exception:
                pass

    # ══════════════════════════════════════════
    #  CROSSHAIR OVERLAY
    # ══════════════════════════════════════════

    def _toggle_crosshair(self):
        if self.cross_var.get() == "on":
            self._show_crosshair()
        else:
            self._hide_crosshair()

    def _show_crosshair(self):
        if self.crosshair_win:
            self._hide_crosshair()

        import tkinter as tk
        colors = {"Red": "#FF0000", "Green": "#00FF00", "Cyan": "#00FFFF",
                  "Yellow": "#FFFF00", "White": "#FFFFFF"}
        color = colors.get(self.cross_color.get(), "#FF0000")
        size = int(self.cross_size.get())
        win_size = size * 4 + 4
        chroma = "#010101"

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = sw // 2 - win_size // 2
        y = sh // 2 - win_size // 2

        self.crosshair_win = tk.Toplevel(self)
        self.crosshair_win.overrideredirect(True)
        self.crosshair_win.attributes("-topmost", True)
        self.crosshair_win.attributes("-transparentcolor", chroma)
        self.crosshair_win.geometry(f"{win_size}x{win_size}+{x}+{y}")
        self.crosshair_win.configure(bg=chroma)

        try:
            hwnd = self.crosshair_win.winfo_id()
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(hwnd, -20,
                                                 ex_style | 0x80000 | 0x20)
        except Exception:
            pass

        canvas = tk.Canvas(self.crosshair_win, width=win_size, height=win_size,
                           bg=chroma, highlightthickness=0)
        canvas.pack()
        cx, cy = win_size // 2, win_size // 2
        canvas.create_line(cx - size, cy, cx + size, cy, fill=color, width=2)
        canvas.create_line(cx, cy - size, cx, cy + size, fill=color, width=2)
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
            "key": self.key_sel.get(),
            "key_speed": int(self.key_speed.get()),
            "key_mode": self.key_mode.get(),
            "key_humanize": self.key_human_var.get(),
            "multi_key": self.multi_key.get(),
            "click_type": self.click_type.get(),
            "click_speed": int(self.click_speed.get()),
            "click_humanize": self.click_human_var.get(),
            "burst": self.burst_var.get(),
            "burst_count": self.burst_count.get(),
            "afk_spin": self.afk_spin_var.get(),
            "afk_wasd": self.afk_wasd_var.get(),
            "afk_jump": self.afk_jump_var.get(),
            "afk_jitter": self.afk_jitter_var.get(),
            "combo_steps": self.combo_steps,
            "hotkey": self.hotkey_sel.get(),
            "panic_key": self.panic_sel.get(),
        }

    def _apply_config(self, cfg):
        try:
            self.key_sel.set(cfg.get("key", "Space"))
            self.key_speed.set(cfg.get("key_speed", 10))
            self.key_mode.set(cfg.get("key_mode", "Spam"))
            self.key_human_var.set(cfg.get("key_humanize", "off"))
            self.multi_key.delete(0, "end")
            self.multi_key.insert(0, cfg.get("multi_key", ""))
            self.click_type.set(cfg.get("click_type", "Left"))
            self.click_speed.set(cfg.get("click_speed", 10))
            self.click_human_var.set(cfg.get("click_humanize", "off"))
            self.burst_var.set(cfg.get("burst", "off"))
            self.burst_count.delete(0, "end")
            self.burst_count.insert(0, cfg.get("burst_count", "10"))
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
        if not name:
            self._log("Enter a profile name")
            return
        ProfileManager.save(name, self._get_current_config())
        self._refresh_profiles()
        self._log(f"Profile saved: {name}")

    def _load_profile(self):
        name = self.profile_sel.get()
        if name == "(none)":
            return
        try:
            cfg = ProfileManager.load(name)
            self._apply_config(cfg)
            self._log(f"Profile loaded: {name}")
        except Exception as e:
            self._log(f"Load error: {e}")

    def _del_profile(self):
        name = self.profile_sel.get()
        if name == "(none)":
            return
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
