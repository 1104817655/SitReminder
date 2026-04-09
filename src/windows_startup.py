from __future__ import annotations

import os
import sys
from pathlib import Path

if os.name == "nt":
    import winreg


APP_NAME = "SitReminder"
RUN_KEY = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"


def build_startup_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'

    main_path = Path(__file__).resolve().parent.parent / "main.py"
    return f'"{sys.executable}" "{main_path}"'


def set_autostart(enabled: bool, command: str | None = None) -> None:
    if os.name != "nt":
        return

    cmd = command or build_startup_command()

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def is_autostart_enabled() -> bool:
    if os.name != "nt":
        return False

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
        return bool(value)
    except FileNotFoundError:
        return False
