"""
关于对话框
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                             QHBoxLayout)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon
from pathlib import Path
from core.theme import load_icon


class AboutDialog(QDialog):
    """关于对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("关于")
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setFixedSize(500, 450)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 图标
        icon_label = QLabel()
        icon_pixmap = QPixmap(str(Path(__file__).parent / "icon" / "pegasus.ico"))
        if not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        layout.addSpacing(10)
        
        # 标题
        title_label = QLabel("天马G游戏筛选器")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # 开发时间
        dev_time_label = QLabel("开发时间: 2026年1月")
        dev_time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_time_label)
        
        layout.addSpacing(20)
        
        # 功能介绍
        features_label = QLabel(
            "<b>主要功能：</b><br><br>"
            "• 从天马G目录中筛选和管理游戏<br>"
            "• 支持多平台游戏管理（GBA、GB、GBC等）<br>"
            "• 游戏元数据编辑功能<br>"
            "• 批量添加和删除游戏<br>"
            "• 任务队列管理系统<br>"
            "• 媒体预览（封面、logo、视频）<br>"
            "• 快捷键操作支持<br>"
        )
        features_label.setWordWrap(True)
        layout.addWidget(features_label)
        
        layout.addSpacing(20)
        
        # 开发者信息
        dev_info = QLabel(
            "<b>开发者信息：</b><br><br>"
            "开发者: 王宇<br>"
            "邮箱: wangyuxxx@163.com"
        )
        dev_info.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_info)
        
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
