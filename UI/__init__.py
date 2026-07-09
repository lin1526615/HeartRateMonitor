import sys
import json
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QWidget,
    QMessageBox, QGroupBox,
    QSystemTrayIcon, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

import threading

from .DevCtrl import *
from .basicwidgets import *
from .heartratepng import *
from .about import AboutWindow
from system_utils import check_run, AppisRunning, logger, try_except, ups, gs, checkupdate, add_to_startup, remove_from_startup, check_startup
from version import __version__, IS_FROZEN

from .Floatingwin_old import *

# 主窗口类
class MainWindow(QMainWindow):
    updata_window_show_ = pyqtSignal(str, str, str, str)
    errorwinopen = pyqtSignal(str, bool, bool)
    iserror = False
    scupdatetimeout = 0 # 测试时发现将窗口放在屏幕边缘时，屏幕切换事件会触发多次，导致窗口大小调整过于频繁，所以设置一个时间间隔

    @try_except("主窗口初始化")
    def __init__(self):
        super().__init__()
        self.version = __version__
        self.cupd = 0
        self.cupdtime = 0.0

        self.errorwinopen.connect(self.errorwin)

        self.setup_ui()
        self.setup_connections()
        
        self.updata_window_show_.connect(self.updata_window_show)

        # 启动后台线程检查更新
        if self.settings_ui._get_set("update_check", False, bool):
            self.start_update_check()

        try:
            check_run()
        except AppisRunning as e:
            self.verylarge_error("程序已经在运行了!!!")
            import sys
            sys.exit(1)
        
        self.settings_ui.check_startup()

    def auto_FixedSize(self):
        # 获取逻辑DPI
        sc = self.screen()
        x_ = sc.physicalDotsPerInchX()
        y_ = sc.physicalDotsPerInchY()
        # 获取屏幕大小信息
        h = sc.availableGeometry().size().height()
        w = sc.availableGeometry().size().width()
        print(f"窗口所在屏幕: {sc.name()}; DPI: {x_}x{y_}; 屏幕分辨率: {w}x{h}")

        MIN_FONT_SIZE = 12

        mfx_ = MIN_FONT_SIZE * 8 / min(x_, y_)
        bz = 1.0

        # 如果缩放后字体大小小于8px，则期望设置为MIN_FONT_SIZE计算出的缩放比值
        if mfx_ > 1.0:
            bz = mfx_

        # 计算窗口大小
        X_outsc = int(x_ / 96 * 700) * bz
        Y_outsc = int(y_ / 96 * 500) * bz

        # 判断是否超出屏幕
        bizhix  = 1.0
        bizhiy  = 1.0
        if w < X_outsc or h < Y_outsc:
            bizhix = w / X_outsc
            bizhiy = h / Y_outsc

        # 完成缩放
        bz = min(bizhix, bizhiy)
        print(f"缩放比例: {bz}(x {bizhix}, y {bizhiy}, {mfx_})")
        swdpi = (int(X_outsc * bz), int(Y_outsc * bz))
        fs = f"{int(y_ / 8 * mfx_ if mfx_ > 1 else y_ / 8)}"
        if not hasattr(self, "sizewithdpi"):
            self.sizewithdpi = swdpi
            self.setFixedSize(*swdpi)
            logger.info(f"调整窗口大小: bz:{bz}, 逻辑DPI: {x_}x{y_}, 屏幕大小: {w}x{h}, 窗口大小: {self.sizewithdpi}")
            # 应用字体大小
            self.setStyleSheet("font-size: " + fs + "px;")
        elif self.sizewithdpi != swdpi:
            self.sizewithdpi = swdpi
            self.setFixedSize(*swdpi)
            logger.info(f"调整窗口大小: x{bz}, 逻辑DPI: {x_}x{y_}, 屏幕大小: {w}x{h}, 窗口大小: {self.sizewithdpi}")
            self.setStyleSheet("font-size: " + fs + "px;")

    def moveEvent(self, a0):
        super().moveEvent(a0)
        scn = self.screen().name()
        if self.scupdatetimeout <= time.time() and (not hasattr(self, 'scn') or self.scn != scn):
            # 测试时发现将窗口放在屏幕边缘时，屏幕切换事件会触发多次，导致窗口大小调整过于频繁，所以设置一个时间间隔
            self.scupdatetimeout = time.time() + 0.2
            logger.debug(f"[GUI] 屏幕切换: {scn}")
            self.scn = scn
            self.auto_FixedSize()
    def setup_ui(self):

        self.auto_FixedSize()
        self.setWindowTitle(f"心率监测设置 -[{self.version}]")

        # 状态栏
        self.status_label = QLabel("准备就绪")
        self.status_label.setAlignment(Qt.AlignCenter)


        # 主布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        setting_layout = QHBoxLayout()
        main_layout.addLayout(setting_layout, stretch=2)

        # 添加各个模块
        self.device_ui = DeviceConnectionUI(self.status_label)
        self.float_ui = FloatingWindowSettingUI()
        self.settings_ui = AppSettingsUI()

        self.setWindowIcon(get_icon())

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.float_ui, 12)
        right_layout.addWidget(self.settings_ui, 5)

        setting_layout.addLayout(self.device_ui, stretch=2)
        setting_layout.addLayout(right_layout, stretch=1)

        main_layout.addWidget(self.status_label)

        self.about_window = AboutWindow()
        self.about_window.errorwinopen.connect(self.errorwin)

    def setup_connections(self):
        # 连接各模块之间的信号和槽
        self.device_ui.heart_rate_updated.connect(self.float_ui.update_heart_rate)
        self.device_ui.status_changed.connect(self.status_label.setText)
        self.device_ui.upd_lastST.connect(self.settings_ui.change_devname)
        self.device_ui.set_act_Devstatus.connect(self.settings_ui.dev_status)
        self.settings_ui.quit_application.connect(self.check_device_status_before_close)
        self.settings_ui.show_settings.connect(self.show_window)
        self.settings_ui.updsig.connect(self.open_about_window)
        def act_HR_clicked():
            if self.settings_ui.devstautus == "连接":
                self.device_ui.connect_device()
            else:
                self.device_ui.disconnect_device()
        self.settings_ui.act_HR_clicked.connect(act_HR_clicked)
        self.screen().physicalDotsPerInchChanged.connect(self.auto_FixedSize)
        self.screen().availableGeometryChanged.connect(self.auto_FixedSize)

    def show_window(self):
        """显示设置窗口"""
        self.show()
        self.activateWindow()

    def closeEvent(self, a0):
        """窗口关闭事件"""
        if self.settings_ui._get_set("use_bg", False, bool):
            # 如果允许后台运行，则隐藏窗口
            self.hide()
            a0.ignore()
        else:
            self.check_device_status_before_close(a0)
    # 检查设备连接状态后执行退出逻辑
    def check_device_status_before_close(self, event = None):
        if event:
            def e_accept():event.accept()
            def e_ignore():event.ignore()
        else:
            e_accept = e_ignore = lambda: None

        # 否则正常退出
        if self.device_ui.ble_monitor.client and self.device_ui.ble_monitor.client.is_connected:
            reply = QMessageBox.question(
                self, '确认',
                "当前已连接设备，确定要退出吗?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.close_application()
                e_accept()
            else:
                e_ignore()
        else:
            self.close_application()
            e_accept()

    def errorwin(self, error_message: str, exit_ = True, setiserror = True):
        if not self.iserror:
            self.iserror = setiserror
            QMessageBox.critical(self, f"{"严重"if exit_ else""}错误", error_message, QMessageBox.Ok)
        if exit_:
            self.close_application()

    def verylarge_error(self, error_message: str, exit_ = True, setiserror = True):
        self.errorwinopen.emit(error_message, exit_, setiserror)

    def close_application(self):
        """执行退出程序的操作"""
        if self.settings_ui.tray_icon:
            self.settings_ui.tray_icon.hide()
        self.float_ui.floating_window.close()
        QApplication.quit()
        sys.exit(0)

    def start_update_check(self):
        """启动后台线程进行自动更新检查。

        如果发现新版本，会在主线程中弹出“关于”对话框并提示用户。"""
        def update_check_thread():
            self.status_label.setText("正在检查更新...")
            # 检查更新
            update_available, index, vname, gxjs, down_url = checkupdate()
            if update_available:
                # 使用信号机制将结果显示到主线程
                self.updata_window_show_.emit(index, vname, gxjs, down_url)
            else:
                if index == "":
                    self.status_label.setText("当前已是最新版本")
                elif index == "时限禁用":
                    print(f"禁用更新中 {self.cupd} {self.cupdtime}")
                    self.status_label.setText("禁用更新中...")
                else:
                    self.status_label.setText("更新检查失败")

        # 创建并启动线程
        threading.Thread(target=update_check_thread, daemon=True).start()

    def open_about_window(self):
        """手动打开关于窗口。"""
        self.about_window.show()

    def updata_window_show(self, index, vname, gxjs, down_url):
        # 打开关于窗口并填充下载地址
        if IS_FROZEN:
            self.about_window.status_label.setText(f"发现新版本 v{vname}[{index}]")
            self.about_window.set_url(down_url)
            self.about_window.show()
        else:
            self.about_window.status_label.setText(f"发现新版本 v{vname}[{index}]")
            # 显示提示和下载界面
            self.about_window.hasupdatapyqtSignal.emit(index, vname, gxjs)

# 应用设置UI类
class AppSettingsUI(QGroupBox):
    quit_application = pyqtSignal()
    show_settings = pyqtSignal()
    updsig = pyqtSignal()
    act_HR_clicked = pyqtSignal()

    @try_except("设置UI初始化")
    def __init__(self):
        super().__init__()
        self.devstautus = "连接"
        self.setup_ui()
        self.setup_tray_icon()
    
    def check_startup(self):
        Csup1, Csup2 = check_startup()
        print(Csup1, end=", ")
        print(Csup2)
        if Csup2 != "":
            logger.debug("[GUI] 检查到启动项")
            if Csup1: 
                self._up_set('startup', True)
                self.set_starup.setChecked(True)
            else:
                re = QMessageBox.warning(self, "提示", f"启动项被其它应用程序占用,是否覆盖?\n相关启动项位置: {Csup2}", QMessageBox.Yes | QMessageBox.No)
                if re == QMessageBox.Yes:
                    add_to_startup()
                    self._up_set('startup', True)
                    self.set_starup.setChecked(True)
                else:
                    self._up_set('startup', False)
                    self.set_starup.setChecked(False)
        else:
            logger.debug("[GUI] 未检查到启动项")
            self._up_set('startup', False)
            self.set_starup.setChecked(False)

    def setup_ui(self):
        self.app_icon = get_icon()
        self.setTitle("软件设置")
        settings_layout = QVBoxLayout()
        
        CheackBox_(
             "允许后台运行"
            ,settings_layout
            ,self._get_set("use_bg", False, bool)
            ,self.toggle_use_bg
        )

        self.set_starup = CheackBox_(
             "开机自启动"
             ,settings_layout
             ,self._get_set("startup", False, bool)
             ,self.toggle_startup
        )

        CheackBox_(
             "启动时检查更新"
            ,settings_layout
            ,self._get_set("update_check", False, bool)
            ,lambda state: self._up_set("update_check", state==Qt.Checked)
        )

        self.check_update_btn = QPushButton("关于")
        # 点击信号交给主窗口处理，通过 updsig 传递
        self.check_update_btn.clicked.connect(self.updsig.emit)
        
        settings_layout.addWidget(self.check_update_btn)

        self.setLayout(settings_layout)

    def setup_tray_icon(self):
        """设置系统托盘图标"""

        if QSystemTrayIcon.isSystemTrayAvailable():

            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(get_icon())
            self.tray_icon.setToolTip("HRMLink")

            self.trme = tray_menu = QMenu()

            # 添加菜单项
            show_settings_action = tray_menu.addAction("打开设置")
            show_settings_action.triggered.connect(self.show_settings.emit)

            tray_menu.addSeparator()

            quit_action = tray_menu.addAction("退出程序")
            quit_action.triggered.connect(self.quit_application.emit)

            self.tray_icon.setContextMenu(tray_menu)
            print(51)
            self.tray_icon.show()
            print(52)
            self.tray_icon.activated.connect(self.on_tray_icon_activated)

            dev = gs("Device","last_selected_device",None,json.loads,"-获取自动连接设备名称")
            self.devname = dev["name"] if dev is not None else None
            if dev is not None:
                self.act_HR = tray_menu.addAction(f"连接 {dev["name"]}")
                self.act_HR.triggered.connect(self.act_HR_clicked.emit)

    def on_tray_icon_activated(self, reason):
        """托盘图标点击事件"""
        if reason == 1:  # 右键单击
            # 显示托盘菜
            self.tray_icon.contextMenu()
        elif reason == 3: # 左键单击
            self.tray_icon.contextMenu().popup(self.tray_icon.geometry().topLeft()-QPoint(0,self.trme.height()))
        elif reason == QSystemTrayIcon.DoubleClick:
            self.show_settings.emit()
        print(reason)

    def toggle_use_bg(self, state):
        """切换允许后台运行"""
        if state == Qt.Checked:
            self._up_set('use_bg', True)
        else:
            self._up_set('use_bg', False)
    
    def toggle_startup(self, state):
        """切换开机启动"""
        if state == Qt.Checked:
            output = add_to_startup()
            if output == "成功":
                self._up_set('startup', True)
            elif output == "脚本":
                QMessageBox.information(self, "提示", "测试启动脚本 start.bat 不通过, 请用文本编辑器打开并修改 PYTHONPATH 项为python目录", QMessageBox.Ok)
                self.set_starup.setChecked(False)
            elif output == "启动项":
                QMessageBox.information(self, "错误", "添加启动项失败", QMessageBox.Ok)
                self.set_starup.setChecked(False)
        else:
            remove_from_startup()
            self._up_set('startup', False)

    def dev_status(self, status):
        self.devstautus = status
        self.change_devname()

    def change_devname(self, devname=None):
        devname = devname or self.devname
        self.devname = devname
        if devname is None:
            return
        if not hasattr(self, "act_HR"):
            self.act_HR = self.trme.addAction(f"{self.devstautus} {devname}")
            self.act_HR.triggered.connect(self.act_HR_clicked.emit)
        else:
            self.act_HR.setText(f"{self.devstautus} {devname}")

    def _up_set(self, option: str, value):
        ups('GUI', option, value, debugn="GUI")

    def _get_set(self, option: str, default, type_ = None):
        return gs('GUI', option, default, type_ , debugn="GUI")
