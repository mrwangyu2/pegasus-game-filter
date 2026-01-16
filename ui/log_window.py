"""
任务执行日志窗口
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton,
                             QHBoxLayout, QLabel, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QTextCursor, QColor, QIcon
from pathlib import Path
from core.i18n import tr
from core.theme import load_icon


class TaskExecutor(QThread):
    """任务执行线程"""
    
    finished = pyqtSignal(dict)
    
    def __init__(self, game_manager):
        super().__init__()
        self.game_manager = game_manager
    
    def run(self):
        """执行任务"""
        results = self.game_manager.execute_tasks()
        self.finished.emit(results)


class LogWindow(QDialog):
    """日志窗口"""
    
    log_signal = pyqtSignal(str, str)  # 用于线程间通信的信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.log_signal.connect(self._do_log)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("log_title"))
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setGeometry(200, 200, 800, 600)
        self.setModal(True)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 状态标签
        self.status_label = QLabel(tr("log_starting"))
        layout.addWidget(self.status_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        layout.addWidget(self.progress_bar)
        
        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, Monaco, monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.log_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        self.close_text = tr("btn_cancel")
        self.close_btn = QPushButton(self.close_text)
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def set_close_text(self, text: str):
        """设置关闭按钮文案"""
        self.close_text = text
        self.close_btn.setText(text)
    
    def log(self, message: str, level: str = "info"):
        """发送日志信号"""
        self.log_signal.emit(message, level)
    
    def _do_log(self, message: str, level: str = "info"):
        """实际执行日志添加（由主线程调用）"""
        # 根据日志级别设置颜色
        color_map = {
            "info": "#d4d4d4",      # 白色
            "success": "#4ec9b0",   # 青色
            "error": "#f48771",     # 红色
            "warning": "#dcdcaa",   # 黄色
        }
        
        color = color_map.get(level, "#d4d4d4")
        
        # 添加带颜色的文本
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # 插入文本
        cursor.insertHtml(f'<span style="color: {color};">{message}</span><br>')
        
        # 滚动到底部
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()
    
    def start_execution(self, game_manager):
        """开始执行任务"""
        self.log("=" * 60, "info")
        self.log(tr("log_starting"), "info")
        self.log("=" * 60, "info")
        
        # 创建执行线程
        self.executor = TaskExecutor(game_manager)
        self.executor.finished.connect(self.on_execution_finished)
        
        # 设置日志回调
        game_manager.task_queue.set_log_callback(self.log)
        
        # 启动线程
        self.executor.start()
    
    def on_execution_finished(self, results: dict):
        """任务执行完成"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        
        self.log("=" * 60, "info")
        self.log(tr("log_finished"), "success")
        # 这里为了保持灵活性，不强制翻译内部的任务详情，因为 task_queue 可能会产生复杂的细节
        self.log("=" * 60, "info")
        
        self.status_label.setText(tr("log_finished"))
        self.close_btn.setEnabled(True)
        self.close_btn.setText(self.close_text)

