# modbuilder.spec

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

script_path = os.path.join(os.getcwd(), "modbuilder.py")
hidden_imports = collect_submodules('deca') + collect_submodules('modbuilder.plugins')

base_dir = os.getcwd()
data_paths = [
    ("modbuilder/org", "org"),
    ("modbuilder/plugins", "plugins"),
    ("modbuilder/saves", "saves"),
    ("deca", "deca"),
    ("modbuilder/name_map.yaml", ".")
]
datas = [(os.path.join(base_dir, src), dst) for src, dst in data_paths]

a = Analysis(
    [script_path],
    pathex=[os.getcwd()],
    #binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name="modbuilder",
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.datas,
    strip=False,
    upx=True,
    name="modbuilder"
)
