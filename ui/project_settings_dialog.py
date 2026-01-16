"""
项目设置对话框
"""

from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QPushButton, QHBoxLayout, QFileDialog,
                             QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from core.project import Project
from core.i18n import tr
from core.theme import load_icon


class ProjectSettingsDialog(QDialog):
    """项目设置对话框"""
    
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("menu_project_settings"))
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 项目名称
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.project.name)
        form_layout.addRow(tr("dialog_project_name"), self.name_edit)
        
        # 项目ROM目录
        roms_layout = QHBoxLayout()
        self.roms_path_edit = QLineEdit()
        self.roms_path_edit.setText(str(self.project.roms_path) if self.project.roms_path else "")
        self.roms_path_edit.setReadOnly(True)
        roms_layout.addWidget(self.roms_path_edit)
        
        browse_roms_btn = QPushButton(tr("btn_browse"))
        browse_roms_btn.clicked.connect(self.browse_roms_path)
        roms_layout.addWidget(browse_roms_btn)
        
        form_layout.addRow(tr("dialog_select_project"), roms_layout)
        
        # 来源ROM目录
        source_layout = QHBoxLayout()
        self.source_path_edit = QLineEdit()
        self.source_path_edit.setText(str(self.project.source_path) if self.project.source_path else "")
        self.source_path_edit.setReadOnly(True)
        source_layout.addWidget(self.source_path_edit)
        
        browse_source_btn = QPushButton(tr("btn_browse"))
        browse_source_btn.clicked.connect(self.browse_source_path)
        source_layout.addWidget(browse_source_btn)
        
        form_layout.addRow(tr("dialog_select_source"), source_layout)

        # Pegasus G 应用目录（可选）
        pegasus_layout = QHBoxLayout()
        self.pegasus_path_edit = QLineEdit()
        self.pegasus_path_edit.setText(str(self.project.pegasus_path) if getattr(self.project, "pegasus_path", None) else "")
        self.pegasus_path_edit.setReadOnly(True)
        pegasus_layout.addWidget(self.pegasus_path_edit)

        browse_pegasus_btn = QPushButton(tr("btn_browse"))
        browse_pegasus_btn.clicked.connect(self.browse_pegasus_path)
        pegasus_layout.addWidget(browse_pegasus_btn)

        form_layout.addRow("Pegasus G (可选)", pegasus_layout)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # 按钮
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton(tr("btn_save"))
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton(tr("btn_cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def browse_roms_path(self):
        """浏览项目ROM目录"""
        path = QFileDialog.getExistingDirectory(self, tr("dialog_select_project"))
        if path:
            self.roms_path_edit.setText(path)
    
    def browse_source_path(self):
        """浏览来源ROM目录"""
        path = QFileDialog.getExistingDirectory(self, tr("dialog_select_source"))
        if path:
            self.source_path_edit.setText(path)

    def browse_pegasus_path(self):
        """浏览 Pegasus G 目录（可选）"""
        path = QFileDialog.getExistingDirectory(self, "选择 Pegasus G 目录")
        if path:
            self.pegasus_path_edit.setText(path)
    
    def save_settings(self):
        """保存设置"""
        # 验证输入
        name = self.name_edit.text().strip()
        roms_path = self.roms_path_edit.text().strip()
        source_path = self.source_path_edit.text().strip()
        pegasus_path = self.pegasus_path_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("msg_enter_name"))
            return
        
        if not roms_path:
            QMessageBox.warning(self, tr("warning"), tr("msg_select_roms"))
            return
        
        if not source_path:
            QMessageBox.warning(self, tr("warning"), tr("msg_select_source"))
            return
        
        # 更新项目信息
        self.project.name = name
        self.project.roms_path = Path(roms_path)
        self.project.source_path = Path(source_path)
        self.project.pegasus_path = Path(pegasus_path) if pegasus_path else None
        
        # 保存项目文件
        if self.project.project_file:
            if self.project.save(self.project.project_file):
                QMessageBox.information(self, tr("success"), tr("msg_save_success"))
                self.accept()
            else:
                QMessageBox.critical(self, tr("error"), tr("msg_save_failed"))
        else:
            self.accept()
