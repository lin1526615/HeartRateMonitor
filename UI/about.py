import time
import webbrowser
from urllib import request
from urllib.error import HTTPError
from PyQt5.QtWidgets import (QDialog, QProgressBar, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QTextBrowser)
from PyQt5.QtCore import QThread, pyqtSignal

from system_utils import logger, start_update_program, try_except, checkupdate
from version import IS_FROZEN

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    error_signal = pyqtSignal(str)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self._is_running = True

    def run(self):
        try:
            # 打开URL连接
            with request.urlopen(self.url) as response:
                # 获取文件总大小
                total_size = int(response.getheader('Content-Length', 0))
                downloaded_size = 0

                # 以二进制写入模式打开本地文件
                with open(self.save_path, 'wb') as f:
                    # 每次读取8KB
                    chunk_size = 8192
                    while self._is_running:
                        print(time.time())
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break

                        # 写入文件并更新下载大小
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # 计算并发送进度百分比
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress_signal.emit(progress)

                if self._is_running:
                    self.finished_signal.emit(True)
                else:
                    self.finished_signal.emit(False)

        except HTTPError as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
            logger.error(f"下载文件时出错: {str(e)}")

        except Exception as e:
            self.error_signal.emit(str(e))
            self.finished_signal.emit(False)
            logger.error(f"下载失败: {e}", exc_info=True)

    def stop(self):
        self._is_running = False
        self.wait()

class AboutWindow(QDialog):
    """‘关于’对话框，同时包含更新检查和下载功能。"""

    # 版本下载相关
    url = ""
    gitcodeurl = None
    githuburl = "https://github.com/lin1526615/HeartRateMonitor"
    hasupdatapyqtSignal = pyqtSignal(str, str, str, str)  # index, vname, gxjs, down_url
    cupd = 0
    cupdtime = 0

    @try_except("关于窗口初始化")
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(600, 500)

        self.hasupdatapyqtSignal.connect(self._show_update_message)

        # 信息区域：包含版权、许可和 Github 链接（HTML 可点击）
        self.info_box = QTextBrowser()
        self.info_box.setReadOnly(True)
        # 构造 HTML 内容
        lic_url = "https://opensource.org/licenses/GPL-3.0"
        html = (
            "<h1>HRMLink</h1>"
            "<h3>Copyright &copy; 2025-2026 Zero_linofe</h3>"
            f"<p>License: <a href='{lic_url}'>GPL v3</a></p>"
            f"<p>GitHub: <a href='{self.githuburl}'>{self.githuburl}</a></p>"
            f"<p>GitCode: <a href='https://gitcode.com/lin15266115/HeartBeat'>https://gitcode.com/lin15266115/HeartBeat</a></p>"
            f"<p>Gitee: <a href='https://gitee.com/lin_1526615/HeartRateMonitor'>https://gitee.com/lin_1526615/HeartRateMonitor</a></p>"
            "<h2>三方开源许可声明:</h2>"
            "<hr>"
            "<h3>Bleak</h3>"
            "<a href='https://github.com/hbldh/bleak/blob/master/LICENSE'>Bleak License</a>"
            "<p>MIT License</p>"
            "<p>Copyright (c) 2020, Henrik Blidh</p>"
            "<p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the \"Software\"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</p>"
            "<p>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</p>"
            "<p>THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p>"
            "<hr>"
            "<h3>PyQt5</h3>"
            "<a href='https://www.riverbankcomputing.com/static/Docs/PyQt5/introduction.html#license'>PyQt5 License</a>"
            "<p>PyQt5 is dual licensed on all platforms under the Riverbank Commercial License and the GPL v3. Your PyQt5 license must be compatible with your Qt license. If you use the GPL version then your own code must also use a compatible license.</p>"
            "<p>PyQt5, unlike Qt, is not available under the LGPL.</p>"
            "<p>You can purchase a commercial PyQt5 license <a href='https://www.riverbankcomputing.com/commercial/buy'>here</a>.</p>"
            "<hr>"
            "<h3>Qt5</h3>"
            "<a href='https://doc.qt.io/qt-5/lgpl.html'>Qt License</a>"
            "<p>Qt is available under the GNU Lesser General Public License version 3.</p>"
            "<p>The Qt Toolkit is Copyright (C) 2018 The Qt Company Ltd. and other contributors.</p>"
            "<p>Contact: <a href='https://www.qt.io/licensing/'>https://www.qt.io/licensing/</a></p>"
            "<hr>"
            "<h3>qasync</h3>"
            "<a href='https://github.com/CabbageDevelopment/qasync/blob/master/LICENSE'>qasync License</a>"
            """<p>Copyright (c) 2019, Sam McCormack</p>
            <p>Copyright (c) 2018, Gerard Marull-Paretas</p>
            <p>Copyright (c) 2014-2018, Mark Harviston, Arve Knudsen</p>
            <p>All rights reserved.</p>

            <p>Redistribution and use in source and binary forms, with or without
            modification, are permitted provided that the following conditions are met:</p>

            <p>1. Redistributions of source code must retain the above copyright notice, this
            list of conditions and the following disclaimer.</p>

            <p>2. Redistributions in binary form must reproduce the above copyright notice,
            this list of conditions and the following disclaimer in the documentation
            and/or other materials provided with the distribution.</p>

            THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
            AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
            IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
            DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
            FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
            DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
            SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
            CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
            OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
            OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.</p>"""
        )
        self.info_box.setHtml(html)
        self.info_box.setOpenExternalLinks(True)

        # 更新状态显示
        self.status_label = QLabel("准备")
        self.url_label = QLabel("")
        self.progress_bar = QProgressBar()

        # 检查更新按钮
        self.check_btn = QPushButton("检查更新")
        self.check_btn.clicked.connect(self.check_updates)

        # 下载相关控件
        downloadlay = QHBoxLayout()
        self.download_btn = QPushButton("Gitcode源下载")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        downloadlay.addWidget(self.download_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        downloadlay.addWidget(self.cancel_btn)
        self.cancel_btn.clicked.connect(self.cancel_download)

        # 布局设置
        layout = QVBoxLayout()
        layout.addWidget(self.info_box)
        layout.addWidget(self.check_btn)
        layout.addWidget(self.url_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addLayout(downloadlay)
        self.setLayout(layout)

        # 下载线程占位
        self.download_thread = None

    def set_url(self, url, gitcodeurl = None):
        self.url = url
        self.url_label.setText(f"下载地址: {url}")
        self.download_btn.setEnabled(True)

    def start_download(self):
        if not self.url:
            self.status_label.setText("错误: 没有设置下载URL")
            return

        logger.info("开始下载文件")

        save_path = "upd.exe"

        self.download_thread = DownloadThread(self.url, save_path)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_finished)
        self.download_thread.error_signal.connect(self.show_error)
        self.download_thread.start()

        # 更新UI状态
        self.status_label.setText("下载中...")
        self.download_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)

    def update_progress(self, progress):
        self.progress_bar.setValue(progress)

    def download_finished(self, success):
        if success:
            self.status_label.setText("下载完成!")
            self.download_btn.setText("重启以应用更新")
            self.download_btn.clicked.connect(start_update_program)
            self.cancel_btn.setText("关闭")
            self.cancel_btn.clicked.connect(self.close)
        else:
            self.status_label.setText("下载已取消或失败")
            self.download_btn.setText("重新下载")
        
        self.download_btn.setEnabled(True)
        if self.download_thread:
            self.download_thread.quit()
            self.download_thread.wait()
            self.download_thread = None

    def show_error(self, error_msg):
        self.status_label.setText(f"错误: {error_msg}")
        self.download_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def cancel_download(self):
        if self.download_thread and self.download_thread.isRunning():
            self.status_label.setText("正在取消下载...")
            self.cancel_btn.setEnabled(False)
            self.download_thread.stop()

    def closeEvent(self, event):
        # 窗口关闭时停止下载线程
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.stop()
            self.download_thread.wait()
        event.accept()

    def toGitCode(self):
        if self.gitcodeurl:
            webbrowser.open(self.gitcodeurl)

    def toGitHub(self):
        webbrowser.open(self.githuburl)

    # --------- update check helpers ---------
    def check_updates(self):
        """在当前对话框内执行一次更新检查。"""
        # 这个方法在工作线程中调用 checkupdate() 并将结果回传给主线程处理
        self.status_label.setText("正在检查更新...")
        self.url_label.clear()
        import threading
        from PyQt5.QtCore import QTimer

        def _worker():
            try:
                update_available, index, vname, gxjs, down_url = checkupdate()
            except Exception as e:
                logger.error(f"检查更新出错: {e}", exc_info=True)
                self.status_label.setText("更新检查失败")
                return

            if update_available:
                if IS_FROZEN:
                    logger.info(f"发现新版本 v{vname}[{index}]")
                    self.status_label.setText(f"发现新版本 v{vname}[{index}]")
                    self.set_url(down_url, down_url)
                else:
                    logger.info(f"发现新版本 v{vname}[{index}]")
                    self.status_label.setText(f"发现新版本 v{vname}[{index}]")
                    # 显示提示和下载界面
                    self.hasupdatapyqtSignal.emit(index, vname, gxjs, down_url)
            else:
                # 无更新情况根据返回的 index 字段判断
                if index == "":
                    self.status_label.setText("当前已是最新版本")
                    self.url_label.clear()
                elif index == "时限禁用":
                    print(f"{self.cupd} {self.cupdtime}")
                    if time.time() - self.cupdtime > 15:
                        self.cupd = 0
                    self.cupdtime = time.time()
                    self.cupd += 1
                    if self.cupd <= 3:
                        self.status_label.setText("刚刚已经检查过更新了")
                    elif self.cupd <= 20:
                        self.status_label.setText("刚刚已经检查过更新了喵~")
                    else:
                        self.status_label.setText("不要再点了喵~~")
                else:
                    self.status_label.setText("更新检查失败")

        threading.Thread(target=_worker, daemon=True).start()

    def _show_update_message(self, index, vname, gxjs, down_url):
        """在主线程中弹出提示并根据用户选择启动下载。"""
        msg = QLabel  # silence lint
        from PyQt5.QtWidgets import QMessageBox

        msgbox = QMessageBox(self)
        msgbox.setWindowTitle('提示')
        msgbox.setText(f'版本-{vname} 已更新:\n {gxjs}')
        msgbox.addButton("查看新版本", QMessageBox.YesRole)
        btn_no = msgbox.addButton("取消", QMessageBox.NoRole)
        msgbox.setDefaultButton(btn_no)
        reply = msgbox.exec()
        if reply == 0:
            # 用户要查看新版本，打开gitcode链接
            webbrowser.open(index)

