"""
元数据编辑对话框
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
                             QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from pathlib import Path
from core.i18n import tr
from core.theme import load_icon



class MetadataEditDialog(QDialog):
    """编辑/查阅 metadata.pegasus.txt 内容的对话框"""
    
    def __init__(self, platform_name: str, content_text: str, parent=None, editable: bool = True):
        super().__init__(parent)
        self.platform_name = platform_name
        self.content_text = content_text
        self.editable = editable
        self.init_ui()

        
    def init_ui(self):
        title_key = "edit_metadata" if self.editable else "view_metadata"
        self.setWindowTitle(f"{tr(title_key)} - {self.platform_name}")
        
        # 确保图标路径正确且为绝对路径
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))

        self.setMinimumSize(600, 400)


        
        layout = QVBoxLayout(self)
        
        if self.editable:
            desc_text = f"正在编辑 {self.platform_name} 的平台配置 (Header):"
        else:
            desc_text = f"查阅 {self.platform_name} 的 metadata.pegasus.txt 全部内容："
        layout.addWidget(QLabel(desc_text))
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.content_text)
        if self.editable:
            self.text_edit.setPlaceholderText("在此输入平台配置，例如 collection: My Games ...")
        else:
            self.text_edit.setPlaceholderText("")
        self.text_edit.setReadOnly(not self.editable)
        layout.addWidget(self.text_edit)

        
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton(tr("btn_save"))
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setStyleSheet("font-weight: bold;")
        self.save_btn.setVisible(self.editable)
        
        close_key = "btn_close" if not self.editable else "btn_cancel"
        self.close_btn = QPushButton(tr(close_key))
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        if self.editable:
            btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)
        
    def get_header(self) -> str:
        return self.text_edit.toPlainText().strip()

