本项目是一个基于 Python 的蓝牙心率监测工具，支持通过 BLE 设备获取心率数据，并提供浮动窗口显示等功能。欢迎提出建议或参与改进！

### 效果展示：

[![视频](https://i1.hdslb.com/bfs/archive/3b60eb45c7b24938e62cdd3f3bc28e56ff5d8e2c.jpg@308w_174h)bilibili视频](https://www.bilibili.com/video/BV1VsEbzeE1N)

### 项目仓库：

[` github `](https://github.com/lin1526615/HeartRateMonitor)
[` gitee `](https://gitee.com/lin_1526615/HeartRateMonitor)
[` gitcode `](https://gitcode.com/lin15266115/HeartBeat)

## 其它下载链接：
[度盘(包含更多测试版本)](https://pan.baidu.com/s/1xJL4eNqg-PcjLqH8iAD4_g?pwd=ukpy)

## 运行程序

**方法1**: (推荐)使用代码运行 -<u>**下载zip** 解压后根据python环境修改 [`start.bat`](start.bat) 后再双击 [`start.bat`](start.bat) 即可运行</u>
- 优点: 随时可以检查代码中有没有烂活, 可以随时依据自己的需求改代码
- 缺点: 运行环境需要自己配置

**方法2**: (推荐)使用exe程序运行 -<u>下载已经编译好的程序, 点击 *`HRMLink.exe`* 运行</u>
- 优点: 门槛较低, 单文件双击即可运行
- 缺点: 相对其它方法不太透明, 使用pyinstaller编译的exe程序可能较大

**方法3**: 自行编译运行 -<u>安装`pyinstaller`后使用[`build.bat`](Build_file/build.bat)编译后运行</u> 
- 优点: 可以自行编译最新开发版, ~~不用担心作者偷偷在编译的程序中整烂活~~
- 缺点: 和方法2获得的程序基本一致, 门槛较高, 可能因不同系统环境导致一些问题

**方法4**: (不推荐)自行编译运行2 -<u>安装nuitka后使用[`build2.bat`](Build_file/build2.bat)编译后运行</u>
- 优点: 比较方法3, 编译包体较小, 运行速度较快
- 缺点: 此方法编译的包可能无法运行或功能缺失, 作者不一定会为此更新

如果 `方法1` 直接运行出现安装依赖相关错误，可以通过命令行手动安装依赖库：

> 推荐使用python3.12运行程序

```python
    pip install pyqt5
    pip install qasync
    pip install bleak
```

## Q&A

#### Q: 我的设备支持蓝牙且已经打开蓝牙, 运行程序时却扫描不到任何设备:

- **A:** 请检查手环是否开启心跳广播, 如果开启后仍然找不到, 可以尝试在点进系统的蓝牙设置页面后, 再尝试点击本程序设备处的刷新按钮

#### Q: 我要如何卸载HRMLink.exe?

- **A:** 由于目前本程序不会往除exe文件所在目录以外的任何地方写入非临时性的文件(大概), 所以卸载程序时, 只需 `关闭开机自启` 后:
  - 如果您从来没有手动往 `HRMlink.exe` 文件所在目录放入任何其它文件, 那么直接删除 `HRMlink.exe` 所在的文件夹即可
  - 或者只删除文件夹中的 `HRMlink.exe` 文件、`config.ini` 文件 和 `log` 文件夹(这些是程序本体和程序运行过程中产生的一些文件，这些文件包含您的个人设置和运行日志)

#### 暂时还没有更多......
