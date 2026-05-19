"""
底部可折叠预览面板（内嵌视频播放）
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QPushButton)
from PyQt5.QtCore import pyqtSignal, Qt, QUrl, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
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
        self._init_ui()
        self.setVisible(False)

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(4, 4, 4, 4)
        self.setLayout(main_layout)

        self.toggle_btn = QPushButton("▲  " + tr("preview_panel"))
        self.toggle_btn.setStyleSheet("text-align: left; font-weight: bold;")
        self.toggle_btn.clicked.connect(self._toggle)
        main_layout.addWidget(self.toggle_btn)

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
        btn_layout.addStretch()
        info_layout.addLayout(btn_layout)

        content_layout.addWidget(info_widget, stretch=1)

        # 右侧：视频（无 VideoSurface 标志，避免 DirectShow 渲染器初始化）
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(320, 220)
        self.video_widget.hide()
        self.video_widget.installEventFilter(self)
        content_layout.addWidget(self.video_widget)

        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self._video_ok = True
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.error.connect(self._on_media_error)

        main_layout.addWidget(self.content)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.content.setVisible(not self._collapsed)
        arrow = "▲" if self._collapsed else "▼"
        self.toggle_btn.setText(f"{arrow}  {tr('preview_panel')}")

    def _on_media_error(self, error):
        if error != QMediaPlayer.NoError:
            self._video_ok = False
            self.video_widget.hide()

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
        self._load_video(game)

        self.edit_btn.setVisible(editable)

    def hide_panel(self):
        self.setVisible(False)
        self.stop_video()

    def stop_video(self):
        try:
            if self.media_player:
                self.media_player.stop()
                self.media_player.setMedia(QMediaContent())
            if self.playlist:
                self.playlist.clear()
        except Exception:
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

    def _load_video(self, game):
        video_path = game.get_video_path()
        if video_path and game.platform_path:
            full_path = game.platform_path / video_path
            if full_path.exists():
                try:
                    self.playlist.clear()
                    self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(full_path))))
                    self.playlist.setCurrentIndex(0)
                    self.video_widget.show()
                    self.media_player.play()
                    return
                except Exception:
                    pass
        self.video_widget.hide()
        try:
            self.media_player.stop()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        if obj == self.video_widget and event.type() == QEvent.MouseButtonPress:
            if self.media_player and self._video_ok:
                try:
                    if self.media_player.state() == QMediaPlayer.PlayingState:
                        self.media_player.pause()
                    else:
                        self.media_player.play()
                except Exception:
                    self._video_ok = False
                    self.video_widget.hide()
            return True
        return super().eventFilter(obj, event)

    def retranslate_ui(self):
        arrow = "▲" if self._collapsed else "▼"
        self.toggle_btn.setText(f"{arrow}  {tr('preview_panel')}")
        self.edit_btn.setText(tr("edit_metadata"))
        self.run_btn.setText(tr("run_game"))
