import os
import sys
import time
import json
import shutil
import logging
import datetime
import subprocess
import urllib.error
import urllib.request
from typing import Any
from logging.handlers import RotatingFileHandler

from version import vname, IS_FROZEN, VER2

# 采用绝对路径避免开机自启时向c盘写入数据
basefile = os.path.dirname(sys.executable) if IS_FROZEN else os.path.dirname(__file__)
print(basefile)
startlog = ""
class AppisRunning(Exception):pass

# --------进程检测--------
def check_run():
    cmd = 'tasklist'
    if IS_FROZEN:
        cmd += ' /fi "imagename eq HRMLink.exe" /nh'
    else:
        return False
    result = subprocess.check_output(cmd, shell=True)
    try:
        res_ = result.decode('gbk')
    except Exception:
        res_ = result.decode('utf-8', errors='ignore')
    global startlog
    startlog += res_
    if 'HRMLink.exe' in res_:
        dete = len(res_.split('HRMLink.exe'))
        if dete > 3:
            print("程序已运行")
            raise AppisRunning
    return False

# --------日志处理--------
class CanNotSaveLogFile(Exception):
    """创建日志文件失败"""
    level = 0

class MyHandler(RotatingFileHandler):
    def doRollover(self):
        try:
            super().doRollover()
            # 在每一个日志文件前添加环境信息
            logger.info(f"运行程序 -{vname} " + " ".join(argv for argv in sys.argv if argv))
            logger.info(f"Python版本: {sys.version}; 运行位置：{sys.executable}")
        except Exception as e:
            raise CanNotSaveLogFile("日志保存失败: %s" % e)

def getlogger():
    global logger
    # 创建日志记录器
    logger = logging.getLogger('__main__')
    logger.setLevel(logging.DEBUG)
    logfile = os.path.join(basefile, 'log/loger.log')
    print(logfile)

    print(2.1)
    set_logfile()
    try:
        handler = MyHandler(
             logfile
            ,maxBytes=5*1024*1024
            ,backupCount=3
            ,encoding='utf-8'
        )
    except Exception:
        # 无法使用日志文件时使用一般的日志记录器
        handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    print(2.2)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if isinstance(handler, MyHandler):
        handler.doRollover()
    logger.info(f"程序启动,启动日志:{startlog}")
    return logger

def upmod_logger():
    global logger

    logger = logging.getLogger('__main__')

    if not os.path.exists('log'):
        os.mkdir('log')
    
    path = os.path.join(basefile, 'log/uplog.log')

    handler = logging.FileHandler(path, 'a', encoding='utf-8')
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def set_logfile():
    """设置日志文件"""
    rt = 0
    while rt < 20:
        try:
            if not os.path.exists('log'):
                os.mkdir('log')
            if os.path.exists('log/loger1.log'):
                print("正在删除旧日志文件1...")
                os.remove('log/loger1.log')
            if os.path.exists('log/loger2.log'):
                print("正在删除旧日志文件2...")
                os.remove('log/loger2.log')
            return
        except Exception as e:
            print(f"错误: {e}")
            time.sleep(5)
            rt += 1

# --------错误输出处理函数--------

errorfunc = None

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    elif isinstance(exc_type, ModuleNotFoundError):
        logger.warning("缺少模块: %s", exc_type.name)
        logger.error(
            "模块导入错误: \n",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        if errorfunc:
            errorfunc(exc_type, exc_value, False)
        pip_install_package(exc_type.name)
        sys.exit(1)

    if hasattr(exc_value, 'level'):
        lv = exc_value.level
    else:
        lv = 1
    logger.error(
        f"{"严重"if lv==1 else""}错误: \n",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    exit_ = False if lv == 0 else True
    if errorfunc:
        errorfunc(exc_type, exc_value, exit_, exit_)

def add_errorfunc(func):
    """用于添加错误处理函数
    函数必须接收参数: exc_type, exc_value
    """
    global errorfunc
    errorfunc= func

def try_except(errlogname = "", func_ = None, exit_ = True, exc_info = True):
    """用于初始化错误处理的装饰器"""
    def try_(func):
        def main(*args, **kwargs):
            try:
                if exc_info:
                    logger.info(f"{errlogname} 开始")
                anything = func(*args, **kwargs)
                logger.info(f"{errlogname} 完成")
                return anything
            except Exception as e:
                logger.error(f"{"严重" if exit_ else ""}错误: {errlogname} 失败: {e}", exc_info=exc_info)
                if func_ is not None: func_(e=f"{"严重" if exit_ else ""}错误: {errlogname} 失败: {e}")
                if exit_:
                    sys.exit(1)
        return main
    return try_

# --------配置文件操作--------

from configparser import ConfigParser

SETTINGTYPE = dict[str, Any]
config_file = os.path.join(basefile, 'config.ini')
print(config_file)

config = ConfigParser()

def init_config():
    global config
    try:
        if not os.path.exists(config_file):
            logger.warning("未找到配置文件 config.ini, 尝试创建默认配置文件")
            save_settings()
        config.read(config_file, encoding='utf-8')
        check_sections()
    except Exception as e:
        logger.error(f"无法加载配置文件: {e}", exc_info=True)

def check_sections():
    sectionlist = ['GUI', 'FloatingWindow', 'Device']
    s_ = False
    for section in sectionlist:
        if not config.has_section(section):
            config.add_section(section)
            s_ = True
    if s_: save_settings()

@try_except("修改配置")
def update_settings(**kwargs: SETTINGTYPE):
    global config
    logger.info(f"{kwargs}")
    for section in kwargs.keys():
        if not config.has_section(section):
            config.add_section(section)
        data = kwargs[section]
        for key in data.keys():
            config.set(section, key, str(data[key]))
    save_settings()

def save_settings():
    global config
    with open(config_file, 'w', encoding='utf-8') as configfile:
        config.write(configfile)

def gs(section, option, default, type_:type = None, debugn = ""):
    if type_ == bool:
        data = config.getboolean(section, option, fallback=default)
    else :
        data = config.get(section, option, fallback=default)
    logger.debug(f' [{debugn}] -获取配置项 {option} 的值: {data}')
    if data is None or data == "None":
        return default
    if type_ is None:
        return data
    else:return type_(data)

def ups(section, option: str, value, debugn = ""):
    config.set(section, option, str(value))
    logger.debug(f'[{debugn}] 更新配置项 {option} 的值: {value}')
    save_settings()

# --------下载前置--------

def pip_install_models(import_models_func: callable, pip_modelname: str):
    try:
        import_models_func()
    except ModuleNotFoundError as e:
        logger.warning(f"缺少依赖包 {e.name}")
        if IS_FROZEN:
            logger.error("编译时错误: 请确保编译时已安装所有依赖包")
            sys.exit(1)
        else:
            pip_install_package(pip_modelname)
    except Exception as e:
        logger.error(f"无法导入模块: {e}")

def pip_install_package(package_name: str):
    # 尝试下载依赖包
    python_exe = sys.executable
    logger.info(f"正在尝试下载依赖包到: {python_exe}")
    try:
        try:
            os.system(f"{python_exe} -m pip install {package_name}")
        except Exception as e:
            logger.error(f"下载依赖包 {package_name} 失败: {e}")
            logger.warning(f"尝试使用阿里云镜像源下载依赖包 {package_name}")
            os.system(f"{python_exe} -m pip install {package_name} -i https://mirrors.aliyun.com/pypi/simple/")
        logger.info(f"已安装依赖包: {package_name}")
    except Exception as e:
        logger.error(f"依赖包安装失败: {e}", exc_info=True)
        sys.exit(1)

# --------启动管理--------

import winreg as reg
APPNAME = "Zero_linofe-HRMlink"
KEYPATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def check_startbat(path):
    "检查启动脚本"
    try:
        result = subprocess.run([path, "-startup"], capture_output=True, timeout=5)
        logger.info(f"启动脚本: {result.stdout.decode('utf-8', errors='ignore')}")
        if "Success!" in result.stdout.decode('utf-8', errors='ignore'): logger.debug("启动脚本通过检查");return True
        else: logger.warning("启动脚本检查不通过");return False
    except Exception as e:
        logger.error(f"启动项检查失败: {e}", exc_info=True)
        return False

def add_to_startup():
    # 获取当前可执行文件路径
    if IS_FROZEN:
        # 如果是打包后的exe
        value = os.path.abspath(sys.executable)
    else:
        # 如果是脚本
        b_ = os.path.dirname(os.path.abspath(sys.argv[0]))
        value = os.path.join(b_, "start.bat")
        # 测试启动脚本是否正确运行
        if not check_startbat(value):
            return "脚本"

    logger.info(f"正在添加到启动项 {value}")
    
    # 打开注册表中的启动项键
    key = reg.HKEY_CURRENT_USER

    try:
        registry_key = reg.OpenKey(key, KEYPATH, 0, reg.KEY_WRITE)
        reg.SetValueEx(registry_key, APPNAME, 0, reg.REG_SZ, rf'"{value}" -start_')
        reg.CloseKey(registry_key)
        return "成功"
    except WindowsError:
        logger.error("添加到启动项失败", exc_info=True)
        return "启动项"

def remove_from_startup():
    key = reg.HKEY_CURRENT_USER

    try:
        registry_key = reg.OpenKey(key, KEYPATH, 0, reg.KEY_WRITE)
        reg.DeleteValue(registry_key, APPNAME)
        reg.CloseKey(registry_key)
        return True
    except WindowsError:
        logger.error("无法从注册表中删除启动项", exc_info=True)
        return False
    
def check_startup():
    # 检查启动项状态
    key = reg.HKEY_CURRENT_USER
    if IS_FROZEN:
        # 如果是打包后的exe
        value = os.path.abspath(sys.executable)
    else:
        # 如果是脚本
        b_ = os.path.dirname(os.path.abspath(sys.argv[0]))
        value = os.path.join(b_, "start.bat")

    try:
        with reg.OpenKey(key, KEYPATH) as registry_key:
            value_, regtype = reg.QueryValueEx(registry_key, APPNAME)
            return (value_ == rf'"{value}" -start_'), value_
    except FileNotFoundError:
        logger.warning("[启动项] 键不存在")
        return False, ""
    except WindowsError:
        logger.warning("[启动项] ", exc_info=True)
        return False, ""

# --------应用更新--------

# 处理更新模式
def handle_update_mode():
    """处理更新模式，替换旧的主程序"""
    try:
        # 获取当前可执行文件路径(upd.exe)
        current_exe = sys.executable
        logger.info(f"当前更新程序路径: {current_exe}")

        # 获取目标路径(HRMLink.exe)
        target_dir = os.path.dirname(current_exe)
        target_exe = os.path.join(target_dir, "HRMLink.exe")

        # 删除旧的主程序
        if os.path.exists(target_exe):
            logger.info("正在删除旧的主程序...")
            os.remove(target_exe)

        # 将upd.exe复制为HRMLink.exe
        logger.info("正在复制更新文件...")
        shutil.copy2(current_exe, target_exe)
        
        # 以-endup参数运行新的主程序
        logger.info("启动新的主程序...")
        os.startfile(target_exe, arguments="-endup")

        # 退出当前进程
        logger.info("更新程序即将退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"更新过程中出错: {e}")
        sys.exit(1)

# 处理更新结束模式
def handle_end_update():
    """处理更新结束，清理更新文件"""
    try:
        # 获取当前可执行文件路径(HRMLink.exe)
        current_exe = sys.executable
        logger.info(f"当前主程序路径: {current_exe}")
        
        # 获取更新文件路径(upd.exe)
        target_dir = os.path.dirname(current_exe)
        update_exe = os.path.join(target_dir, "upd.exe")
        
        # 删除更新文件
        if os.path.exists(update_exe):
            logger.info("正在清理更新文件...")
            os.remove(update_exe)
    except Exception as e:
        logger.error(f"清理更新文件时出错: {e}")

# 启动更新程序
def start_update_program():
    """启动更新程序"""
    try:
        # 获取当前可执行文件路径(HRMLink.exe)
        current_exe = sys.executable
        logger.info(f"当前主程序路径: {current_exe}")
        
        # 获取更新文件路径(upd.exe)
        target_dir = os.path.dirname(current_exe)
        update_exe = os.path.join(target_dir, "upd.exe")

        # 启动更新程序
        logger.info("正在启动更新程序...")
        os.startfile(update_exe, arguments="-updatemode")

        logger.info("更新程序已启动，请稍等...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动更新程序时出错: {e}")
        sys.exit(1)

def checkupdate() :
    logger.info("检查更新中...")
    dtime = time.time() - gs("GUI","upstime",0,float,"检查更新")
    if dtime<200:
        logger.info(f"禁用检查更新中({int(dtime)}s/200s)")
        return False, '时限禁用', '', '', ''
    else:
        ups("GUI","upstime",time.time(),"检查更新")
    try:
        url = "https://raw.gitcode.com/lin15266115/HeartBeat/raw/main/version.json"
        urlGitee = "https://gitee.com/lin_1526615/HeartRateMonitor/raw/main/version.json"
        urlGithub = "https://api.github.com/repos/lin1526615/HeartRateMonitor/contents/version.json?ref=main"
        return check_with_raw(url)
    except urllib.error.URLError as e:
        logger.warning(f"更新检查失败(gitcodeURL不可达): {e}")
    except Exception as e:
        logger.error(f"更新检查失败(未标识的错误): {e}", exc_info=True)
    finally:
        try:
            return check_with_raw(urlGitee)
        except Exception as e:
            try:
                logger.warning(f"更新检查失败(gitee): {e}", exc_info=True)
                return check_with_githubapi(urlGithub)
            except Exception as e:
                logger.error(f"更新检查失败(github): {e}", exc_info=True)
                return False, '失败', '', '', ''

def check_with_raw(url: str):
    with urllib.request.urlopen(url) as response: 
        # 读取json格式
        data = json.loads(response.read().decode('utf-8'))
        return read_data(data)

def check_with_githubapi(url: str):
    import base64
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        if data['content']:
            data_ = base64.b64decode(data['content']).decode('utf-8')
            return read_data(json.loads(data_))

def read_data(data)-> tuple[bool, str, str, str, str]:
    durl = data['frozen']['download']

    if IS_FROZEN:
        data_ = data['frozen']
        up_index = data_['index']
        updatetime = data_['updateTime']
        try:
            if datetime.datetime.now() < datetime.datetime.strptime(updatetime, '%Y-%m-%d-%H:%M:%S'):
                return False, '', '', '', ''
        except Exception as e:
            logger.error(f"更新时间检查失败: 更新时间读取失败({updatetime})")
    else:
        data_ = data
        up_index = 'https://gitcode.com/lin15266115/HeartBeat'
    VER2_VER = data_['VER2']
    vname = data_['name']
    gxjs = data_['gxjs']
    if VER2_VER > [v for v in VER2]:
        logger.info(f"发现新版本 {vname}[{'.'.join(map(str, VER2_VER))}]")
        return True, up_index, vname, gxjs, durl
    else:
        logger.info("当前已是最新版本")
    return False, '', '', '', ''