# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for InboxAgent."""

import sys
from pathlib import Path

block_cipher = None

src_path = Path("..") / "src"

a = Analysis(
    [str(src_path / "open_email" / "main.py")],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        (str(Path("..") / "config"), "config"),
    ],
    hiddenimports=[
        "open_email.gui",
        "open_email.gui.app",
        "open_email.gui.agent_thread",
        "open_email.gui.tabs.dashboard",
        "open_email.gui.tabs.accounts",
        "open_email.gui.tabs.rules",
        "open_email.gui.tabs.logs",
        "open_email.gui.tabs.settings",
        "open_email.gui.widgets.log_handler",
        "open_email.platform.autostart",
        "open_email.agent_core",
        "open_email.config_loader",
        "open_email.email_parser",
        "open_email.imap_client",
        "open_email.rule_engine",
        "open_email.actions",
        "open_email.ai_classifier",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    exclude_binaries=True,
    name="inbox-agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='inbox-agent'
)
