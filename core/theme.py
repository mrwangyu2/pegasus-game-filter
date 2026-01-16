"""
应用主题样式（明亮/暗黑等）。
"""
import sys
import os
import ctypes
from ctypes import byref, c_int, windll
from textwrap import dedent
from PyQt5.QtGui import QIcon
from PyQt5.QtWinExtras import QtWin


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


LIGHT_STYLES = dedent(



    """
    QWidget { background: #f7f7f7; color: #222; }
    QMainWindow { background: #f7f7f7; }
    QToolBar, QMenuBar { background: #ffffff; border: 0; }
    QStatusBar { background: #ffffff; color: #444; }
    QPushButton { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 4px; padding: 6px 10px; }
    QPushButton:disabled { color: #999; }
    QPushButton:hover { border-color: #a0a0a0; }
    QListWidget { background: #ffffff; }
    QListWidget::item:selected { background: #e6f3ff; color: #0f172a; }
    QListWidget::item:selected:active { background: #d8ebff; color: #0f172a; }
    QLineEdit, QComboBox, QTextEdit { background: #ffffff; border: 1px solid #d0d0d0; border-radius: 4px; }
    QLabel { color: #222; }

    QSplitter::handle { background: #d0d0d0; }
    QProgressBar { border: 1px solid #d0d0d0; border-radius: 4px; text-align: center; }
    QProgressBar::chunk { background-color: #4CAF50; }
    QMenu { background: #ffffff; border: 1px solid #d0d0d0; }
    QMenu::item:selected { background: #e6f3ff; }
    """
)

DARK_STYLES = dedent(
    """
    QWidget { background: #1e1e1e; color: #e0e0e0; }
    QMainWindow { background: #1e1e1e; }
    QToolBar, QMenuBar { background: #262626; border: 0; }
    QStatusBar { background: #262626; color: #c0c0c0; }
    QPushButton { background: #2e2e2e; border: 1px solid #3a3a3a; border-radius: 4px; padding: 6px 10px; color: #e0e0e0; }
    QPushButton:disabled { color: #777; }
    QPushButton:hover { border-color: #5a5a5a; }
    QListWidget { background: #262626; }
    QListWidget::item:selected { background: #2f3b4f; color: #e0e0e0; }
    QListWidget::item:selected:active { background: #37475f; color: #e0e0e0; }
    QLineEdit, QComboBox, QTextEdit { background: #262626; border: 1px solid #3a3a3a; border-radius: 4px; color: #e0e0e0; }
    QLabel { color: #e0e0e0; }

    QSplitter::handle { background: #3a3a3a; }
    QProgressBar { border: 1px solid #3a3a3a; border-radius: 4px; text-align: center; background: #262626; }
    QProgressBar::chunk { background-color: #4CAF50; }
    QMenu { background: #262626; border: 1px solid #3a3a3a; }
    QMenu::item:selected { background: #3a3a3a; }
    """
)

BLUE_STYLES = dedent(
    """
    QWidget { background: #0f172a; color: #e2e8f0; }
    QMainWindow { background: #0f172a; }
    QToolBar, QMenuBar { background: #111827; border: 0; }
    QStatusBar { background: #111827; color: #cbd5e1; }
    QPushButton { background: #1e293b; border: 1px solid #334155; border-radius: 4px; padding: 6px 10px; color: #e2e8f0; }
    QPushButton:disabled { color: #64748b; }
    QPushButton:hover { border-color: #475569; }
    QListWidget { background: #111827; }
    QListWidget::item:selected { background: #1d2a44; color: #e2e8f0; }
    QListWidget::item:selected:active { background: #22304d; color: #e2e8f0; }
    QLineEdit, QComboBox, QTextEdit { background: #111827; border: 1px solid #334155; border-radius: 4px; color: #e2e8f0; }
    QLabel { color: #e2e8f0; }

    QSplitter::handle { background: #1e293b; }
    QProgressBar { border: 1px solid #334155; border-radius: 4px; text-align: center; background: #111827; }
    QProgressBar::chunk { background-color: #22d3ee; }
    QMenu { background: #111827; border: 1px solid #334155; }
    QMenu::item:selected { background: #1e293b; }
    """
)

SEPIA_STYLES = dedent(
    """
    QWidget { background: #f5f0e6; color: #3b3024; }
    QMainWindow { background: #f5f0e6; }
    QToolBar, QMenuBar { background: #f9f3ea; border: 0; }
    QStatusBar { background: #f9f3ea; color: #5a4b3a; }
    QPushButton { background: #fdf8f0; border: 1px solid #d6c7b2; border-radius: 4px; padding: 6px 10px; color: #3b3024; }
    QPushButton:disabled { color: #a08e77; }
    QPushButton:hover { border-color: #c2b197; }
    QListWidget { background: #fbf6ee; }
    QListWidget::item:selected { background: #efe5d6; color: #3b3024; }
    QListWidget::item:selected:active { background: #e6dac7; color: #3b3024; }
    QLineEdit, QComboBox, QTextEdit { background: #fbf6ee; border: 1px solid #d6c7b2; border-radius: 4px; color: #3b3024; }
    QLabel { color: #3b3024; }

    QSplitter::handle { background: #d6c7b2; }
    QProgressBar { border: 1px solid #d6c7b2; border-radius: 4px; text-align: center; background: #fbf6ee; }
    QProgressBar::chunk { background-color: #d99559; }
    QMenu { background: #fbf6ee; border: 1px solid #d6c7b2; }
    QMenu::item:selected { background: #efe5d6; }
    """
)


def build_stylesheet(theme: str) -> str:
    """返回指定主题的样式表字符串。"""
    if theme == "dark":
        return DARK_STYLES
    if theme == "blue":
        return BLUE_STYLES
    if theme == "sepia":
        return SEPIA_STYLES
    return LIGHT_STYLES


def available_themes():
    return ["light", "dark", "blue", "sepia"]


def _set_win_dark_titlebar(hwnd: int, enable: bool) -> None:
    """在 Windows 10+ 启用/关闭暗色标题栏（不影响功能，失败则忽略）。"""
    # 仅在 Win10 1809 (build 17763) 及以上可用
    try:
        if sys.platform != "win32":
            return
        if sys.getwindowsversion().build < 17763:
            return

        # 优先使用属性 20，若失败尝试属性 19（早期版本）
        value = c_int(1 if enable else 0)
        for attr in (20, 19):
            res = windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, byref(value), 4)
            if res == 0:
                return
    except Exception:
        # 如果调用失败则静默忽略，不影响程序主逻辑
        return


def apply_titlebar_theme(widget, theme: str) -> None:
    """根据主题切换 Windows 标题栏颜色（仅 Win10+ 生效）。"""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(widget.winId())
    except Exception:
        return
    darkish = theme in ("dark", "blue")
    _set_win_dark_titlebar(hwnd, darkish)


