"""
双栏布局容器
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal
from ui.source_panel import SourcePanel
from ui.collection_panel import CollectionPanel
from ui.operate_bar import OperateBar
from ui.preview_panel import PreviewPanel


class DualPanelLayout(QWidget):
    """双栏文件管理器式布局"""

    copy_requested = pyqtSignal(list)
    delete_requested = pyqtSignal(list)
    game_selected = pyqtSignal(object)
    game_activated = pyqtSignal(object)
    edit_metadata_requested = pyqtSignal(object)
    run_game_requested = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # 上半部分：双栏 + 操作区
        self.splitter = QSplitter(Qt.Horizontal)

        self.source_panel = SourcePanel()
        self.splitter.addWidget(self.source_panel)

        self.operate_bar = OperateBar()
        self.splitter.addWidget(self.operate_bar)

        self.collection_panel = CollectionPanel()
        self.splitter.addWidget(self.collection_panel)

        self.splitter.setStretchFactor(0, 5)  # 来源
        self.splitter.setStretchFactor(1, 0)  # 操作区 (固定宽度)
        self.splitter.setStretchFactor(2, 5)  # 收藏

        layout.addWidget(self.splitter, stretch=1)

        # 下半部分：预览面板
        self.preview_panel = PreviewPanel()
        layout.addWidget(self.preview_panel)

    def _connect_signals(self):
        # 来源面板 → 布局信号
        self.source_panel.game_selected.connect(self._on_source_game_selected)
        self.source_panel.game_activated.connect(self._on_game_activated)
        self.source_panel.selection_changed.connect(self._on_source_selection_changed)

        # 收藏面板 → 布局信号
        self.collection_panel.game_selected.connect(self._on_collection_game_selected)
        self.collection_panel.game_activated.connect(self._on_game_activated)
        self.collection_panel.selection_changed.connect(self._on_collection_selection_changed)
        self.collection_panel.delete_requested.connect(self.delete_requested)

        # 操作区按钮
        self.operate_bar.copy_clicked.connect(self._on_copy)
        self.operate_bar.delete_clicked.connect(self._on_delete)

        # 预览面板
        self.preview_panel.edit_metadata_clicked.connect(self.edit_metadata_requested)
        self.preview_panel.run_game_clicked.connect(self.run_game_requested)

        # 初始禁用
        self.operate_bar.set_copy_enabled(False)
        self.operate_bar.set_delete_enabled(False)

    def _on_source_game_selected(self, game):
        self.game_selected.emit(game)
        self.preview_panel.show_game(game, editable=False)

    def _on_collection_game_selected(self, game):
        self.game_selected.emit(game)
        self.preview_panel.show_game(game, editable=True)

    def _on_game_activated(self, game):
        self.game_activated.emit(game)

    def _on_source_selection_changed(self, games):
        self.operate_bar.set_copy_enabled(len(games) > 0)

    def _on_collection_selection_changed(self, games):
        self.operate_bar.set_delete_enabled(len(games) > 0)

    def _on_copy(self):
        games = self.source_panel.get_selected_games()
        if games:
            self.copy_requested.emit(games)

    def _on_delete(self):
        games = self.collection_panel.get_selected_games()
        if games:
            self.delete_requested.emit(games)

    def load_source(self, games, platforms, existing_checker):
        """加载来源面板数据"""
        self.source_panel.set_games(games)
        self.source_panel.set_platforms(platforms)
        self.source_panel.set_existing_checker(existing_checker)

    def load_collection(self, games, platforms, modified_marker=None):
        """加载收藏面板数据"""
        self.collection_panel.set_games(games)
        self.collection_panel.set_platforms(platforms)
        if modified_marker:
            self.collection_panel.set_modified_marker(modified_marker)

    def refresh_collection(self, games, platforms):
        """刷新收藏面板"""
        self.load_collection(games, platforms)

    def stop_preview(self):
        self.preview_panel.stop_video()
        self.preview_panel.hide_panel()

    def retranslate_ui(self):
        self.source_panel.retranslate_ui()
        self.collection_panel.retranslate_ui()
        self.operate_bar.retranslate_ui()
        self.preview_panel.retranslate_ui()
