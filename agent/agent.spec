# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['standalone_agent.py'],
    pathex=[],
    binaries=[],
    datas=[('../protos/*.py', 'protos')],
    hiddenimports=[
        'grpc',
        'google.protobuf',
        'google.protobuf.descriptor',
        'google.protobuf.descriptor_pool',
        'google.protobuf.symbol_database',
        'google.protobuf.internal',
        'google.protobuf.internal.builder',
        'google.protobuf.internal.enum_type_wrapper',
        'google.protobuf.internal.containers',
        'google.protobuf.internal.decoder',
        'google.protobuf.internal.encoder',
        'google.protobuf.internal.extension_dict',
        'google.protobuf.internal.well_known_types',
        'google.protobuf.message',
        'google.protobuf.reflection',
        'google.protobuf.runtime_version',
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
    [],
    name='agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
) 


