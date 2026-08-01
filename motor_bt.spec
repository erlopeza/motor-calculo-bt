# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('circuitos.xlsx', '.'),
        ('src', 'src'),
        ('gui', 'gui'),
    ],
    hiddenimports=[
        'openpyxl',
        'openpyxl.styles.stylesheet',
        'docx',
        'pkg_resources',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MotorBT',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
)
