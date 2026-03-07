"""cx_Freeze MSI build script for Windows."""

import sys
from pathlib import Path

from cx_Freeze import Executable, setup

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

build_exe_options = {
    "packages": [
        "open_email",
        "open_email.gui",
        "open_email.gui.tabs",
        "open_email.gui.widgets",
        "open_email.platform",
        "PyQt6",
    ],
    "include_files": [
        (str(src_path.parent / "config"), "config"),
    ],
    "excludes": ["tkinter", "unittest"],
}

bdist_msi_options = {
    "upgrade_code": "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}",
    "add_to_path": True,
    "initial_target_dir": r"[ProgramFilesFolder]\InboxAgent",
}

executables = [
    Executable(
        script=str(src_path / "open_email" / "main.py"),
        base="Win32GUI" if sys.platform == "win32" else None,
        target_name="inbox-agent",
        shortcut_name="InboxAgent",
        shortcut_dir="DesktopFolder",
    )
]

setup(
    name="InboxAgent",
    version="0.1.0",
    description="InboxAgent - Privacy-first local AI email organization agent",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
