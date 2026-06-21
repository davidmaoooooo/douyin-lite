# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

added_files = [
    ('api/', 'api/'),
    ('utils/', 'utils/'),
    ('lib/runtime/', 'lib/runtime/'),
    ('lib/reverse/FIXED_keystream.json', 'lib/reverse/'),
    ('lib/reverse/time_mapping_sample.json', 'lib/reverse/'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'flask', 'flask_cors', 'httpx', 'loguru', 'ujson', 'browser_cookie3',
        'api', 'api.user', 'api.video', 'api.search',
        'api.recommend', 'api.common_api', 'api.live_api', 'api.direct_api',
        'utils', 'utils.request', 'utils.cookies', 'utils.util',
        'utils.execjs_fix', 'utils.abogus_pure',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'tests'],
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
    [],
    name='douyin-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
