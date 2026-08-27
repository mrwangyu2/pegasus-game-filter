"""
中间操作区组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt
from core.i18n import tr


class OperateBar(QWidget):
    """中间操作区：复制和删除按钮"""

    copy_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(80)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        self.setLayout(layout)

        layout.addStretch()

        self.copy_btn = QPushButton("→\n" + tr("copy_selection"))
        self.copy_btn.setFixedSize(60, 60)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #4CAF50; color: white;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.copy_btn.clicked.connect(self.copy_clicked)
        layout.addWidget(self.copy_btn, alignment=Qt.AlignCenter)

        self.delete_btn = QPushButton("←\n" + tr("delete_selection"))
        self.delete_btn.setFixedSize(60, 60)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #f44336; color: white;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.delete_btn.clicked.connect(self.delete_clicked)
        layout.addWidget(self.delete_btn, alignment=Qt.AlignCenter)

        layout.addStretch()

    def set_copy_enabled(self, enabled: bool):
        self.copy_btn.setEnabled(enabled)

    def set_delete_enabled(self, enabled: bool):
        self.delete_btn.setEnabled(enabled)

    def retranslate_ui(self):
        self.copy_btn.setText("→\n" + tr("copy_selection"))
        self.delete_btn.setText("←\n" + tr("delete_selection"))
