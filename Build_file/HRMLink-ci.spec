# -*- mode: python ; coding: utf-8 -*-
#
# GitHub Actions 专用的 PyInstaller 打包配置（新文件，不影响本地用的 HRMLink.spec）
#
# 为什么单独一份？
#   HRMLink.spec 里写死了 ..\.conda\Library\bin\*.dll 这些本地 conda 环境的绝对依赖，
#   而 GitHub Actions 上的 Python 来自 python.org，根本没有 .conda 目录，
#   直接套用会因路径不存在而缺少 DLL。
#
# 本文件的策略：
#   * 只把"当前 Python 环境里确实存在"的额外 DLL 加进打包列表；
#   * python.org 官方 Python 的 DLL 由 PyInstaller 自带 hook 自动收集，无需干预；
#   * conda / 虚拟环境（包括项目自带的 .conda）则按目录查找后手动补上。
# 这样同一份配置在本地和 CI 上都能用。
import os
import sys

# conda 环境里需要手动补充的原生库（python.org 环境下这些文件不存在，会被自动跳过）
_extra_dll_names = [
    'libcrypto-3-x64.dll',
    'libssl-3-x64.dll',
    'libexpat.dll',
    'liblzma.dll',
    'LIBBZ2.dll',
    'ffi.dll',
]

# 依次查找的目录：项目自带的 .conda → 当前解释器所在的 conda 环境
_extra_dll_dirs = [
    os.path.join(SPECPATH, '..', '.conda', 'Library', 'bin'),
    os.path.join(sys.base_prefix, 'Library', 'bin'),
]


def _find_extra_dll(name):
    for directory in _extra_dll_dirs:
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            return path
    return None


binaries = [(path, '.') for path in map(_find_extra_dll, _extra_dll_names) if path]

a = Analysis(
    [r'..\__main__.py'],
    pathex=[],
    binaries=binaries,
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
