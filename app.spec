# app.spec

# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

if sys.platform == 'darwin':
    exe_extension = ''
    coll_name = 'RoastProfiler.app'
elif sys.platform == 'win32':
    exe_extension = '.exe'
    coll_name = 'RoastProfiler'
elif sys.platform.startswith('linux'):
    exe_extension = ''
    coll_name = 'RoastProfiler'
else:
    raise NotImplementedError(f'Unsupported platform: {sys.platform}')


added_files = [
    ('roastprofiler/templates', 'roastprofiler/templates'),
    ('roastprofiler/static', 'roastprofiler/static'),
    ('data.template', 'roastprofiler/data'),
    ('roastprofiler/roast_profile_template', 'roastprofiler/roast_profile_template'),
    ('roastprofiler/scripts', 'roastprofiler/scripts'),
]


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=['boto3', 'watchdog', 'qrcode'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RoastProfiler' + exe_extension,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True if you want console output during development
)

if sys.platform == 'darwin':
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='RoastProfiler'
    )

    app = BUNDLE(
        coll,
        name=coll_name,
    )
else:
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=coll_name
    )
