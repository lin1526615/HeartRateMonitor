chcp 65001 > nul

.\.conda\python -m nuitka ^
  --output-dir=_nuitka/1.3.8-beta.2 ^
  --output-filename=HRMLink.exe ^
  --enable-plugin=pyqt5 ^
  --include-package=bleak ^
  --include-package=winrt ^
  --include-package=winrt.windows.foundation.collections ^
  --onefile ^
  --standalone ^
  --windows-console-mode=disable ^
  --remove-output ^
  --lto=no ^
  --company-name="Zero_linofe" ^
  --product-name="HRMLink" ^
     --file-version=1.3.8.1 ^
  --product-version=1.3.8.1 ^
  --file-description="通过低功耗蓝牙协议获取心率并显示 | Compiled using Nuitka" ^
  --copyright="Copyright (C) 2025 Zero_linofe | GPL-3.0 License" ^
  --windows-icon-from-ico=HR-icon.ico ^
  __main__.py
