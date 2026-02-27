# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['..\__main__.py'],
    pathex=[],
    binaries=[
        (r'..\.conda\Library\bin\libcrypto-3-x64.dll', '.'),
        (r'..\.conda\Library\bin\libssl-3-x64.dll', '.'),
        (r'..\.conda\Library\bin\libexpat.dll', '.'),
        (r'..\.conda\Library\bin\liblzma.dll', '.'),
        (r'..\.conda\Library\bin\LIBBZ2.dll', '.'),
        (r'..\.conda\Library\bin\ffi.dll', '.'),
    ],
    datas=[],
    hiddenimports=['winrt.windows.foundation.collections'],
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
    a.binaries,
    a.datas,
    [],
    name='HRMLink',
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
    version='version.txt',
    icon='./HR-icon.ico'
)
