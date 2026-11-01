"""校验 PyInstaller 打包产物是否完整（供 GitHub Actions 使用）。

为什么需要这一步：
    PyInstaller 只有在能解析到依赖时才会把原生 DLL 打进包里。
    如果构建机的 Python 环境缺少某些 DLL，打包过程本身仍然是"成功"的，
    但生成的 exe 运行时会因为 _ssl / _ctypes 等模块加载失败而崩溃。
    这里直接读取 PyInstaller 生成的 TOC，确认关键文件确实被打进了产物。

用法：
    python .github/scripts/check_bundle.py [TOC 路径]
    不传参数时自动在 build/ci/*/PKG-00.toc 中查找最新的一份。
"""

from __future__ import annotations

import ast
import pathlib
import sys

# (显示名, 可接受的产物文件名片段, 缺失时的说明)
# 片段写法同时兼容 conda（libssl-3-x64.dll / ffi.dll）与 python.org（libssl-3.dll / libffi-8.dll）
REQUIRED: list[tuple[str, tuple[str, ...], str]] = [
    ("libssl", ("libssl",), "SSL 支持（检查更新需要访问 https）"),
    ("libcrypto", ("libcrypto",), "SSL / hashlib 支持"),
    ("libffi", ("libffi", "ffi.dll"), "ctypes 支持"),
    ("liblzma", ("liblzma",), "lzma 支持"),
    ("Qt5Core", ("qt5core.dll",), "Qt 核心库"),
    ("Qt5Widgets", ("qt5widgets.dll",), "Qt 控件库"),
    ("qwindows", ("qwindows.dll",), "Qt Windows 平台插件（缺少时窗口无法显示）"),
]


def resolve_toc() -> pathlib.Path:
    """定位 PyInstaller 生成的 TOC 文件。"""
    if len(sys.argv) > 1:
        return pathlib.Path(sys.argv[1])
    # --workpath build/ci 下的子目录名取自 spec 文件名，因此用通配匹配
    candidates = sorted(
        pathlib.Path("build/ci").glob("*/PKG-00.toc"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("build/ci 下没有找到任何 PKG-00.toc")
    return candidates[0]


def load_binary_names(toc_path: pathlib.Path) -> list[str]:
    data = ast.literal_eval(toc_path.read_text(encoding="utf-8"))
    # PyInstaller 的 TOC 结构：(打包文件名, 选项字典, [(产物内路径, 源路径, 类型), ...])
    entries = data[2]
    return [
        entry[0].lower()
        for entry in entries
        if len(entry) >= 3 and entry[2] == "BINARY"
    ]


def find_matches(name: str, alternatives: tuple[str, ...]) -> list[str]:
    return [alt for alt in alternatives if alt in name]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    try:
        toc_path = resolve_toc()
    except FileNotFoundError as exc:
        print(f"[失败] {exc}")
        print("       PyInstaller 打包可能没有完成，或 --workpath 与这里不一致。")
        return 1

    if not toc_path.is_file():
        print(f"[失败] 找不到 {toc_path}")
        return 1

    binary_names = load_binary_names(toc_path)

    missing = [
        (label, reason)
        for label, alternatives, reason in REQUIRED
        if not any(find_matches(name, alternatives) for name in binary_names)
    ]

    if missing:
        print(f"[失败] {toc_path} 中的打包产物缺少以下必需文件：")
        for label, reason in missing:
            print(f"  - {label:<12} {reason}")
        print(f"\n产物中共有 {len(binary_names)} 个二进制文件，实际清单：")
        for name in sorted(binary_names):
            print(f"  {name}")
        return 1

    print(f"[通过] {toc_path}：{len(binary_names)} 个二进制文件，关键依赖齐全")
    for label, alternatives, _ in REQUIRED:
        matched = sorted({name for name in binary_names if any(a in name for a in alternatives)})
        print(f"  - {label:<12} -> {', '.join(matched)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
