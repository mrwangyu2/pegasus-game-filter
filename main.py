#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天马G游戏筛选器 - 主程序入口
"""

import sys
import os
import ctypes
from pathlib import Path
from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, qInstallMessageHandler
from PyQt5.QtGui import QIcon
from PyQt5.QtWinExtras import QtWin


_original_qt_message_handler = None

def qt_message_handler(mode, context, message):
    """过滤已知无害的 libpng ICC 配置警告"""
    if "libpng warning: iCCP" in message:
        return
    if _original_qt_message_handler:
        _original_qt_message_handler(mode, context, message)
    else:
        sys.stderr.write(message + "\n")


def load_icon(icon_path):
    """使用 Windows API 加载图标并转换为 QIcon，以支持非标准 ICO 文件"""
    if not os.path.exists(icon_path):
        return QIcon()
    
    if sys.platform == 'win32':
        try:
            # IMAGE_ICON = 1, LR_LOADFROMFILE = 0x0010
            hicon = ctypes.windll.user32.LoadImageW(0, str(icon_path), 1, 0, 0, 0x0010)
            if hicon:
                pixmap = QtWin.fromHICON(hicon)
                # 记得释放句柄
                ctypes.windll.user32.DestroyIcon(hicon)
                return QIcon(pixmap)
        except Exception:
            pass
    return QIcon(str(icon_path))


def set_app_id():
    """设置 Windows 的 AppUserModelID，确保图标正常显示"""
    if sys.platform == 'win32':
        try:
            myappid = 'pegasus.game.filter.v1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass


def main():
    """主程序入口"""
    set_app_id()
    global _original_qt_message_handler
    _original_qt_message_handler = qInstallMessageHandler(qt_message_handler)
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # 强制设置 Qt 插件路径，确保 ico 插件加载
    qt_plugins_path = os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages", "PyQt5", "Qt5", "plugins")
    if os.path.exists(qt_plugins_path):
        QApplication.addLibraryPath(qt_plugins_path)
    
    app = QApplication(sys.argv)
    app.setApplicationName("天马G游戏筛选器")
    app.setOrganizationName("PegasusFilter")
    
    # 统一设置应用图标
    base_dir = Path(__file__).parent.absolute()
    icon_path = base_dir / "ui" / "icon" / "pegasus.ico"
    app_icon = load_icon(icon_path)
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
