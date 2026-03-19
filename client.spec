# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gamevcs/client/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'gamevcs.client',
        'gamevcs.client.commands',
        'gamevcs.client.commands.init',
        'gamevcs.client.commands.status',
        'gamevcs.client.commands.add',
        'gamevcs.client.commands.commit',
        'gamevcs.client.commands.shelve',
        'gamevcs.client.commands.branches',
        'gamevcs.client.commands.tags',
        'gamevcs.client.commands.locks',
        'gamevcs.client.commands.get',
        'gamevcs.client.tui',
        'gamevcs.client.api',
        'click',
        'rich',
        'requests',
        'xxhash',
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
    name='gamevcs',
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
    name='gamevcs',
)