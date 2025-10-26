import os

BASE_DIR = os.getcwd()  # current folder, safe for PyInstaller spec
LANGS_DIR = os.path.join(BASE_DIR, 'langs')

lang_files = []
for root, dirs, files in os.walk(LANGS_DIR):
    for f in files:
        if f.endswith('.lang'):
            src = os.path.join(root, f)
            rel_path = os.path.relpath(root, BASE_DIR)
            lang_files.append((src, rel_path))

a = Analysis(
    ['sharp.py'],
    pathex=[],
    binaries=[],
    datas=lang_files,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries + a.datas,
    name='sharp',
    debug=False,
    strip=False,
    upx=True,
    console=False
)
