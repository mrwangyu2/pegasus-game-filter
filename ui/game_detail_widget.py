"""
游戏详情组件
"""

from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QScrollArea,
                             QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QEvent
from PyQt5.QtGui import QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from core.metadata_parser import Game
from core.i18n import tr


class GameDetailWidget(QWidget):
    """游戏详情组件"""
    
    game_updated = pyqtSignal(Game)
    
    def __init__(self):
        super().__init__()
        self.current_game = None
        self._editable = False
        self._dirty = False
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 媒体预览
        self.media_group = QGroupBox(tr("media_preview"))
        media_layout = QHBoxLayout()
        
        # 封面图片
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setFixedHeight(300)
        self.cover_label.setFixedWidth(300)
        self.cover_label.setStyleSheet("border: 1px solid #ccc;")
        media_layout.addWidget(self.cover_label)
        
        # 右侧视频区域
        video_area_layout = QVBoxLayout()
        
        # 视频播放器
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedHeight(300)
        self.video_widget.hide()
        self.video_widget.installEventFilter(self)
        video_area_layout.addWidget(self.video_widget)
        
        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.error.connect(self.handle_media_error)
        
        # 播放控制改为点击视频区域
        media_layout.addLayout(video_area_layout)
        
        self.media_group.setLayout(media_layout)
        content_layout.addWidget(self.media_group)
        
        # 基本信息
        self.info_group = QGroupBox(tr("media_preview")) # 会在 retranslate_ui 中更新
        self.info_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._mark_dirty)
        
        self.sort_by_edit = QLineEdit()
        self.sort_by_edit.textChanged.connect(self._mark_dirty)
        
        self.platform_edit = QLineEdit()
        self.platform_edit.textChanged.connect(self._mark_dirty)
        
        self.developer_edit = QLineEdit()
        self.developer_edit.textChanged.connect(self._mark_dirty)
        
        # 记录标签
        self.label_title = QLabel(tr("title_label"))
        self.label_sort = QLabel(tr("sort_by_label"))
        self.label_platform = QLabel(tr("platform_label_detail"))
        self.label_developer = QLabel(tr("developer_label"))
        
        self.info_layout.addRow(self.label_title, self.title_edit)
        self.info_layout.addRow(self.label_sort, self.sort_by_edit)
        self.info_layout.addRow(self.label_platform, self.platform_edit)
        self.info_layout.addRow(self.label_developer, self.developer_edit)
        
        self.info_group.setLayout(self.info_layout)
        content_layout.addWidget(self.info_group)
        
        # 描述
        self.desc_group = QGroupBox(tr("description_label"))
        desc_layout = QVBoxLayout()
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(150)
        self.description_edit.textChanged.connect(self._mark_dirty)
        desc_layout.addWidget(self.description_edit)
        
        self.desc_group.setLayout(desc_layout)
        content_layout.addWidget(self.desc_group)
        
        # 文件信息
        self.file_group = QGroupBox(tr("file_info_label"))
        self.file_info_layout = QFormLayout()
        
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        self.label_rom = QLabel(tr("rom_file_label"))
        self.file_info_layout.addRow(self.label_rom, self.file_label)
        
        self.directory_label = QLabel()
        self.directory_label.setWordWrap(True)
        self.label_dir = QLabel(tr("dir_label"))
        self.file_info_layout.addRow(self.label_dir, self.directory_label)
        
        self.file_group.setLayout(self.file_info_layout)
        content_layout.addWidget(self.file_group)
        
        # 保存按钮
        self.save_btn = QPushButton(tr("btn_save_changes"))
        self.save_btn.clicked.connect(self.save_changes)
        self.save_btn.setEnabled(False)
        content_layout.addWidget(self.save_btn)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # 默认来源视图只读
        self.set_editable(False)
        self.retranslate_ui()

    def retranslate_ui(self):
        """刷新UI文字"""
        self.media_group.setTitle(tr("media_preview"))
        self.info_group.setTitle(tr("base_info_label"))
        
        # 使用记录的标签更新
        self.label_title.setText(tr("title_label"))
        self.label_sort.setText(tr("sort_by_label"))
        self.label_platform.setText(tr("platform_label_detail"))
        self.label_developer.setText(tr("developer_label"))
        
        self.desc_group.setTitle(tr("description_label"))
        self.file_group.setTitle(tr("file_info_label"))
        
        self.label_rom.setText(tr("rom_file_label"))
        self.label_dir.setText(tr("dir_label"))
        
        self.save_btn.setText(tr("btn_save_changes"))
        
        if not self.current_game:
            self.cover_label.setText(tr("no_game"))
        elif not self.cover_label.pixmap() or self.cover_label.pixmap().isNull():
            self.cover_label.setText(tr("no_cover"))
    
    def set_game(self, game: Game, auto_play: bool = False):
        """设置当前游戏"""
        self.current_game = game
        self.stop_video()
        
        # 加载基本信息
        self.title_edit.setText(game.game)
        self.sort_by_edit.setText(game.sort_by)
        self.platform_edit.setText(game.platform)
        self.developer_edit.setText(game.developer)
        self._mark_dirty(False)
        self.description_edit.setPlainText(game.description)
        
        # 文件信息
        self.file_label.setText(game.file)
        if game.platform_path:
            self.directory_label.setText(str(game.platform_path))
        
        # 加载封面
        self.load_cover(game)
        
        # 加载视频 (根据参数决定是否自动播放)
        if auto_play:
            self.load_video(game)
        else:
            self.video_widget.hide()
            self.media_player.stop()

    def play_current_video(self):
        """手动触发播放当前游戏的视频"""
        if self.current_game:
            self.load_video(self.current_game)
    
    def load_cover(self, game: Game):
        """加载封面图片"""
        cover_path = game.get_boxfront_path()
        
        if cover_path and game.platform_path:
            full_path = game.platform_path / cover_path
            if full_path.exists():
                pixmap = QPixmap(str(full_path))
                scaled_pixmap = pixmap.scaled(
                    self.cover_label.width(), 
                    self.cover_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.cover_label.setPixmap(scaled_pixmap)
                return
        
        self.cover_label.setText("无封面")
        self.cover_label.setPixmap(QPixmap())
    
    def load_video(self, game: Game):
        """加载视频"""
        video_path = game.get_video_path()
        
        if video_path and game.platform_path:
            full_path = game.platform_path / video_path
            if full_path.exists():
                self.playlist.clear()
                self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(full_path))))
                self.playlist.setCurrentIndex(0)
                # 重新关联播放列表，因为 stop_video 可能清空了关联
                if self.media_player.playlist() != self.playlist:
                    self.media_player.setPlaylist(self.playlist)
                self.video_widget.show()
                self.media_player.play()
                return
        
        self.video_widget.hide()
        self.media_player.stop()
    
    def handle_media_error(self):
        """处理媒体错误"""
        print(f"视频播放错误: {self.media_player.errorString()}")

    def eventFilter(self, source, event):
        """视频区域点击控制播放/暂停"""
        if source == self.video_widget and event.type() == QEvent.MouseButtonPress:
            self.toggle_video()
            return True
        return super().eventFilter(source, event)

    def toggle_video(self):
        """切换视频播放（点击视频区域）"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    
    def stop_video(self):
        """停止视频并释放文件"""
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent()) # 显式清空媒体内容，释放文件句柄
        self.playlist.clear()
    
    def save_changes(self):
        """保存修改"""
        if not self.current_game:
            return
        
        self.current_game.game = self.title_edit.text()
        self.current_game.sort_by = self.sort_by_edit.text()
        self.current_game.platform = self.platform_edit.text()
        self.current_game.developer = self.developer_edit.text()
        self.current_game.description = self.description_edit.toPlainText()
        
        self.game_updated.emit(self.current_game)
        self._mark_dirty(False)
    
    def clear(self):
        """清空显示"""
        self.current_game = None
        self.stop_video()
        
        self.title_edit.clear()
        self.sort_by_edit.clear()
        self.platform_edit.clear()
        self.developer_edit.clear()
        self.description_edit.clear()
        self.file_label.clear()
        self.directory_label.clear()
        self.cover_label.clear()
        self.cover_label.setText("无游戏")
        self._mark_dirty(False)

    def set_editable(self, editable: bool):
        """设置是否可编辑，以及保存按钮显示/可用状态"""
        self._editable = editable
        for widget in [self.title_edit, self.sort_by_edit, self.platform_edit, self.developer_edit]:
            widget.setReadOnly(not editable)
        self.description_edit.setReadOnly(not editable)
        self.save_btn.setVisible(editable)
        if not editable:
            self.save_btn.setEnabled(False)
        else:
            self.save_btn.setEnabled(self._dirty)

    def _mark_dirty(self, dirty: bool = True, *args):
        """标记内容是否被修改，控制保存按钮"""
        # textChanged 信号会传递字符串，这里统一转换为布尔
        self._dirty = bool(dirty) if self._editable else False
        if self._editable:
            self.save_btn.setEnabled(self._dirty)
        else:
            self.save_btn.setEnabled(False)
