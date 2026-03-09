# Invex Clicker

Roblox macro tool built with Python + customtkinter.

## Key Technical Details
- **SendInput with KEYEVENTF_SCANCODE (0x0008)** — required for Roblox (DirectInput reads scan codes, not virtual keys)
- **64-bit safe ctypes structures** — INPUT struct must be exactly 40 bytes
- **50ms key hold duration** between key_down/key_up for Roblox to register
- **customtkinter** — does NOT support alpha hex colors (no "#RRGGBBAA")
- **PyInstaller** — build with `python -m PyInstaller --onefile --noconsole --name InvexClicker invex_clicker.py`

## Project Structure
- `invex_clicker.py` — single file containing all code (~1200 lines)
- Classes: `InputEngine` (static SendInput wrappers), `ProfileManager` (JSON save/load), `InvexClicker` (main CTk app)
- Profiles stored in `%APPDATA%/InvexClicker/profiles/`

## Features
- 5 tabs: Auto Key, Auto Click, Anti-AFK, Combos, Settings
- Auto Key: spam/hold mode, multi-key, humanize, speed slider
- Auto Click: left/right, burst mode, fixed position, cursor tracker
- Anti-AFK: camera spin, random WASD, jump, mouse jitter
- Combos: key sequence builder with delays, loop toggle
- Settings: hotkeys (F6 toggle, Escape panic), session timer, crosshair overlay, profiles, always-on-top

## Build & Release
- Build: `python -m PyInstaller --onefile --noconsole --name InvexClicker invex_clicker.py`
- GitHub: https://github.com/andyrom6/invex-clicker
- GitHub CLI: `C:\Users\ander\gh_cli\bin\gh.exe`
- Release: `gh release create vX.X dist/InvexClicker.exe --title "..." --notes "..."`

## Design System (v5.0 — Glass Morphism)
- Background: #060611 (ultra deep void)
- Glass panels: #12122A with #252550 edge glow borders
- Surface: #0F0F1E, #161630, #1E1E42
- Primary accent: #8B5CF6 (vibrant purple)
- Cyan: #22D3EE, Green: #34D399, Red: #F87171, Orange: #FB923C
- Glass card pattern: outer glow frame + inner glass frame with 1px border
- Font: Segoe UI, Consolas for monospace
- Corner radius: 18px glass cards, 12px buttons, 14px stat cards
- White slider knobs for better visibility
