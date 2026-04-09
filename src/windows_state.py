from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from typing import Iterable

try:
    import psutil
except ImportError:  # pragma: no cover - optional at runtime
    psutil = None


_IS_WINDOWS = os.name == "nt"

if _IS_WINDOWS:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    MONITOR_DEFAULTTONEAREST = 2

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    class MONITORINFO(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", wintypes.DWORD),
        ]


def get_idle_seconds() -> float:
    if not _IS_WINDOWS:
        return 0.0

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0

    ticks = kernel32.GetTickCount()
    elapsed_ms = ticks - info.dwTime
    if elapsed_ms < 0:
        return 0.0
    return elapsed_ms / 1000.0


def get_foreground_process_name() -> str:
    if not _IS_WINDOWS or psutil is None:
        return ""

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    pid = wintypes.DWORD(0)
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return ""

    try:
        return psutil.Process(pid.value).name().lower()
    except (psutil.Error, OSError):
        return ""


def is_meeting_related(keywords: Iterable[str]) -> bool:
    proc = get_foreground_process_name()
    if not proc:
        return False

    lowered = [k.lower().strip() for k in keywords if k and str(k).strip()]
    return any(k in proc for k in lowered)


def is_foreground_fullscreen() -> bool:
    if not _IS_WINDOWS:
        return False

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    if user32.IsIconic(hwnd):
        return False

    rect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return False

    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    if not monitor:
        return False

    monitor_info = MONITORINFO()
    monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info)):
        return False

    win_w = rect.right - rect.left
    win_h = rect.bottom - rect.top
    mon = monitor_info.rcMonitor
    mon_w = mon.right - mon.left
    mon_h = mon.bottom - mon.top

    if win_w <= 0 or win_h <= 0 or mon_w <= 0 or mon_h <= 0:
        return False

    tolerance = 2
    return (
        abs(rect.left - mon.left) <= tolerance
        and abs(rect.top - mon.top) <= tolerance
        and abs(rect.right - mon.right) <= tolerance
        and abs(rect.bottom - mon.bottom) <= tolerance
    )
