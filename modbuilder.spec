# modbuilder.spec

a = Analysis(
    ['modbuilder.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('modbuilder/org', 'org'),
        ('modbuilder/plugins/*.py', 'plugins'),
        ('modbuilder/saves', 'saves'),
        ('deca/*.py', 'deca'),
        ('modbuilder/name_map.yaml', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='modbuilder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='modbuilder',
)
