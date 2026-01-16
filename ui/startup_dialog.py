"""
启动时的项目选择对话框
"""

from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon



from core.i18n import tr
from core.theme import load_icon



class StartupDialog(QDialog):
    """启动对话框"""
    
    def __init__(self, recent_projects, parent=None):
        super().__init__(parent)
        self.recent_projects = recent_projects
        self.selected_path = None
        self.action = None # 'new', 'open', 'recent'
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle(tr("welcome_title"))
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setFixedSize(500, 400)



        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel(tr("app_title"))
        title_label.setStyleSheet("font-size: 18pt; font-weight: bold; color: #2196F3;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        desc_label = QLabel(tr("welcome_desc"))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: gray; margin-bottom: 20px;")
        layout.addWidget(desc_label)
        
        # 最近项目
        layout.addWidget(QLabel(tr("recent_projects")))
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("QListWidget { border: 1px solid #ddd; border-radius: 4px; padding: 5px; }")
        
        if not self.recent_projects:
            item = QListWidgetItem(tr("no_recent_projects"))
            item.setFlags(Qt.NoItemFlags)
            self.recent_list.addItem(item)
        else:
            for path_str in self.recent_projects:
                path = Path(path_str)
                item = QListWidgetItem(path.name)
                item.setToolTip(path_str)
                item.setData(Qt.UserRole, path_str)
                self.recent_list.addItem(item)
        
        self.recent_list.itemDoubleClicked.connect(self.on_recent_double_clicked)
        layout.addWidget(self.recent_list)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.new_btn = QPushButton(tr("btn_new_project"))
        self.new_btn.setFixedHeight(40)
        self.new_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; border-radius: 4px;")
        self.new_btn.clicked.connect(self.on_new_clicked)
        btn_layout.addWidget(self.new_btn)
        
        self.open_btn = QPushButton(tr("btn_open_project"))
        self.open_btn.setFixedHeight(40)
        self.open_btn.clicked.connect(self.on_open_clicked)
        btn_layout.addWidget(self.open_btn)
        
        layout.addLayout(btn_layout)

        # 默认聚焦到最近项目列表的第一项
        if self.recent_projects:
            self.recent_list.setCurrentRow(0)
            self.recent_list.setFocus()
    
    def keyPressEvent(self, event):
        """处理回车键打开选中的最近项目"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            current_item = self.recent_list.currentItem()
            if current_item and current_item.data(Qt.UserRole):
                self.on_recent_double_clicked(current_item)
                return
        super().keyPressEvent(event)

    
    def on_recent_double_clicked(self, item):
        path_str = item.data(Qt.UserRole)
        if path_str:
            self.selected_path = path_str
            self.action = 'recent'
            self.accept()
    
    def on_new_clicked(self):
        self.action = 'new'
        self.accept()
    
    def on_open_clicked(self):
        self.action = 'open'
        self.accept()
