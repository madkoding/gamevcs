# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gamevcs/server/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'gamevcs.server',
        'gamevcs.server.models',
        'gamevcs.server.database',
        'gamevcs.server.auth',
        'gamevcs.server.api',
        'gamevcs.server.api.auth',
        'gamevcs.server.api.users',
        'gamevcs.server.api.projects',
        'gamevcs.server.api.branches',
        'gamevcs.server.api.changelists',
        'gamevcs.server.api.locks',
        'gamevcs.server.api.tags',
        'sqlalchemy',
        'sqlalchemy.orm',
        'fastapi',
        'uvicorn',
        'jose',
        'pydantic',
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
    [],
    exclude_binaries=True,
    name='gamevcs-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name='gamevcs-server',
)