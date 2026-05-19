"""
底部可折叠预览面板
"""
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QPushButton)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from core.i18n import tr


class PreviewPanel(QWidget):
    """底部可折叠游戏预览面板"""

    edit_metadata_clicked = pyqtSignal(object)
    run_game_clicked = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.current_game = None
        self._editable = False
        self._collapsed = True
        self._video_path = None
        self._init_ui()
        self.setVisible(False)

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(main_layout)

        # 折叠/展开切换栏
        self.toggle_btn = QPushButton("▲  " + tr("preview_panel"))
        self.toggle_btn.setStyleSheet("text-align: left; font-weight: bold;")
        self.toggle_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.toggle_btn)

        # 可折叠内容区
        self.content = QWidget()
        content_layout = QHBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 左侧：封面
        self.cover_label = QLabel()
        self.cover_label.setFixedSize(220, 220)
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setStyleSheet("border: 1px solid #555; background: #1a1a2e;")
        self.cover_label.setText(tr("no_game"))
        content_layout.addWidget(self.cover_label)

        # 中间：信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(8, 0, 8, 0)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr("title_label"))
        info_layout.addWidget(QLabel(tr("title_label")))
        info_layout.addWidget(self.title_edit)

        self.platform_label = QLabel()
        info_layout.addWidget(QLabel(tr("platform_label_detail")))
        info_layout.addWidget(self.platform_label)

        self.developer_label = QLabel()
        info_layout.addWidget(QLabel(tr("developer_label")))
        info_layout.addWidget(self.developer_label)

        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        info_layout.addWidget(QLabel(tr("rom_file_label")))
        info_layout.addWidget(self.file_label)

        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText(tr("description_label"))
        info_layout.addWidget(QLabel(tr("description_label")))
        info_layout.addWidget(self.desc_edit)

        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton(tr("edit_metadata"))
        self.edit_btn.clicked.connect(lambda: self.edit_metadata_clicked.emit(self.current_game))
        btn_layout.addWidget(self.edit_btn)

        self.run_btn = QPushButton(tr("run_game"))
        self.run_btn.clicked.connect(lambda: self.run_game_clicked.emit(self.current_game))
        btn_layout.addWidget(self.run_btn)

        # 播放视频按钮
        self.play_video_btn = QPushButton("▶ " + tr("play_video"))
        self.play_video_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white;
                border-radius: 4px; padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.play_video_btn.clicked.connect(self._open_video_external)
        self.play_video_btn.setEnabled(False)
        btn_layout.addWidget(self.play_video_btn)

        btn_layout.addStretch()
        info_layout.addLayout(btn_layout)

        content_layout.addWidget(info_widget, stretch=1)
        main_layout.addWidget(self.content)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.content.setVisible(not self._collapsed)
        arrow = "▲" if self._collapsed else "▼"
        self.toggle_btn.setText(f"{arrow}  {tr('preview_panel')}")

    def show_game(self, game, editable=False):
        self.current_game = game
        self._editable = editable
        self.setVisible(True)
        if self._collapsed:
            self._toggle()

        self.title_edit.setText(game.game)
        self.title_edit.setReadOnly(not editable)
        self.platform_label.setText(game.platform or "")
        self.developer_label.setText(game.developer or "")
        self.file_label.setText(game.file or "")
        self.desc_edit.setPlainText(game.description or "")
        self.desc_edit.setReadOnly(not editable)

        self._load_cover(game)
        self._check_video(game)

        self.edit_btn.setVisible(editable)

    def hide_panel(self):
        self.setVisible(False)
        self._video_path = None
        self.play_video_btn.setEnabled(False)

    def stop_video(self):
        """兼容旧接口，无操作"""
        pass

    def _load_cover(self, game):
        cover_path = game.get_boxfront_path()
        if cover_path and game.platform_path:
            full_path = game.platform_path / cover_path
            if full_path.exists():
                pixmap = QPixmap(str(full_path)).scaled(
                    220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.cover_label.setPixmap(pixmap)
                return
        self.cover_label.setText(tr("no_cover"))
        self.cover_label.setPixmap(QPixmap())

    def _check_video(self, game):
        """检测是否有可播放的视频文件"""
        self._video_path = None
        video_path = game.get_video_path()
        if video_path and game.platform_path:
            full_path = game.platform_path / video_path
            if full_path.exists():
                self._video_path = full_path
                self.play_video_btn.setEnabled(True)
                return
        self.play_video_btn.setEnabled(False)

    def _open_video_external(self):
        """使用系统默认播放器打开视频"""
        if self._video_path and self._video_path.exists():
            os.startfile(str(self._video_path))

    def retranslate_ui(self):
        arrow = "▲" if self._collapsed else "▼"
        self.toggle_btn.setText(f"{arrow}  {tr('preview_panel')}")
        self.edit_btn.setText(tr("edit_metadata"))
        self.run_btn.setText(tr("run_game"))
        self.play_video_btn.setText("▶ " + tr("play_video"))
