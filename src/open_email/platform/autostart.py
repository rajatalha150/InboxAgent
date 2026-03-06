"""Cross-platform auto-start management.

Windows: HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run registry key
Linux: ~/.config/autostart/open-email.desktop file
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("open_email")

APP_NAME = "OpenEmail"
DESKTOP_ENTRY_NAME = "open-email.desktop"


def _get_executable() -> str:
    """Get the path to the current executable."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return f"{sys.executable} -m open_email.main --gui --minimized"


def _is_windows() -> bool:
    return sys.platform == "win32"


def _is_linux() -> bool:
    return sys.platform.startswith("linux")


# --- Linux ---

def _desktop_entry_path() -> Path:
    return Path.home() / ".config" / "autostart" / DESKTOP_ENTRY_NAME


def _linux_set_autostart(enabled: bool) -> None:
    path = _desktop_entry_path()
    if enabled:
        path.parent.mkdir(parents=True, exist_ok=True)
        exe = _get_executable()
        content = (
            "[Desktop Entry]\n"
            f"Name={APP_NAME}\n"
            "Type=Application\n"
            f"Exec={exe}\n"
            "Hidden=false\n"
            "NoDisplay=false\n"
            "X-GNOME-Autostart-enabled=true\n"
            "Comment=Privacy-first local AI email organization agent\n"
        )
        path.write_text(content)
        logger.info("Created autostart entry: %s", path)
    else:
        if path.exists():
            path.unlink()
            logger.info("Removed autostart entry: %s", path)


def _linux_is_enabled() -> bool:
    return _desktop_entry_path().exists()


# --- Windows ---

def _windows_set_autostart(enabled: bool) -> None:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            exe = _get_executable()
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe)
            logger.info("Set Windows autostart registry key")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                logger.info("Removed Windows autostart registry key")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        raise RuntimeError(f"Failed to modify registry: {e}") from e


def _windows_is_enabled() -> bool:
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except (FileNotFoundError, OSError):
        return False


# --- Public API ---

def set_autostart(enabled: bool) -> None:
    """Enable or disable auto-start on boot."""
    if _is_windows():
        _windows_set_autostart(enabled)
    elif _is_linux():
        _linux_set_autostart(enabled)
    else:
        raise NotImplementedError(f"Auto-start not supported on {sys.platform}")


def is_autostart_enabled() -> bool:
    """Check if auto-start is currently enabled."""
    if _is_windows():
        return _windows_is_enabled()
    elif _is_linux():
        return _linux_is_enabled()
    return False
