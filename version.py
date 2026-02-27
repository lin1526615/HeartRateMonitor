# 直接运行脚本生成version.json和bat文件

import sys
IS_FROZEN = getattr(sys, 'frozen', False) or hasattr(sys, "_MEIPASS") or ("__compiled__" in globals())
IS_NUITKA = IS_FROZEN and "__compiled__" in globals()

VER2 = (1, 3, 8, 2)
BINARY_BUILD = 3
v1      = ".".join(map(str, VER2[0:3]))
F_      = "-beta" + (("."+str(BINARY_BUILD)) if BINARY_BUILD else "")
vname = f"{v1}b{VER2[3]}"
Fvname  = v1 +  F_
__version__ = Fvname if IS_FROZEN else vname

if __name__ == "__main__":
    import json
    with open("version.json", "w", encoding="utf-8") as f:
        sdata = {
             "name": "v" + vname
            ,"version": 2
            ,"VER2": VER2
            ,"gxjs": "(更新): 更新检查按钮替换为关于页面, 将下载界面更改为关于页面, 添加版权信息和三方开源许可信息等(1.3.8.2)"
        }
        text = json.dumps(sdata, ensure_ascii=False, indent=2)
        frozendata = {
                 "name": "v" + Fvname
                ,"version": 2
                ,"VER2": VER2
                ,"updateTime": "2025-11-23-22:30:00"
                ,"gxjs": "(1.3.7.3)本次更新和优化了浮窗拖动体验, 修复开机自启长期以来存在的问题等"
                ,"index": f"https://gitcode.com/lin15266115/HeartBeat/releases/v{Fvname}"
                ,"download": f"https://gitcode.com/lin15266115/HeartBeat/releases/download/v{Fvname}/HRMLink.exe"
            }
        frozentext = f""",\n\n\n  "frozen":{json.dumps(frozendata, ensure_ascii=False)}\n}}"""
        text = text[0:-2] + frozentext
        f.write(text)
    try:
        from importlib import import_module
        buildbatmain = import_module("build_bat").main
        buildbatmain(VER2, Fvname)
    except Exception: pass
