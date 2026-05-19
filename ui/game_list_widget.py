"""
游戏列表组件（重构版）
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QColor
from typing import List, Set, Optional
from core.metadata_parser import Game
from core.i18n import tr


class GameListWidget(QWidget):
    """游戏列表组件"""

    game_selected = pyqtSignal(Game)
    game_activated = pyqtSignal(Game)  # 新增激活信号（回车或双击）
    selection_changed = pyqtSignal(set)  # 发送选中的游戏集合
    platform_changed = pyqtSignal(str)   # 发送当前选择的平台名称

    def __init__(self):
        super().__init__()
        self.games: List[Game] = []
        self.filtered_games: List[Game] = []
        self.selected_games: Set[Game] = set()
        self.duplicate_checker = None  # 检查项目中是否已存在（源面板用）
        self.existing_checker = None   # 检查目标中是否已存在（集合面板用）
        self.filter_text: str = ""
        self.platform_filter: str = ""  # 由面板设置，不内置 UI
        # 批量加载配置
        self.batch_size: int = 300
        self.visible_count: int = 0

        self.autoplay_timer = QTimer()

        self.init_ui()

    def init_ui(self):
        """初始化UI（搜索/平台过滤由面板层提供）"""
        self.setMinimumWidth(380)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 列表
        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.currentItemChanged.connect(self.on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.list_widget.setSpacing(2)
        self.list_widget.installEventFilter(self)
        self.list_widget.setFocusPolicy(Qt.StrongFocus)

        # 让容器聚焦时自动把焦点传给列表
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.list_widget)
        layout.addWidget(self.list_widget)

    def _get_selection_colors(self):
        """根据当前主题返回选中项的背景和前景颜色"""
        theme = getattr(self.window(), "current_theme", "light") if self.window() else "light"
        if theme == "dark":
            return QColor("#2f3b4f"), QColor("#e0e0e0")
        if theme == "blue":
            return QColor("#1d2a44"), QColor("#e2e8f0")
        if theme == "sepia":
            return QColor("#efe5d6"), QColor("#3b3024")
        # 默认 light
        return QColor("#e6f3ff"), QColor("#0f172a")

    def retranslate_ui(self):
        """刷新UI文字"""
        self.update_count_label()

    def set_games(self, games: List[Game]):
        """设置游戏列表"""
        self.games = games
        self.selected_games.clear()
        self.apply_filters()

    def set_duplicate_checker(self, checker):
        """设置重复检测回调，返回True表示已存在"""
        self.duplicate_checker = checker

    def set_existing_checker(self, checker):
        """设置已存在检测回调（返回 True 表示目标中已存在）"""
        self.existing_checker = checker

    def set_task_queue(self, task_queue):
        """[deprecated] No-op stub, task queue removed. Remove after MainWindow rewrite."""
        pass

    def update_list(self):
        """更新列表显示（批量渲染，触底追加）"""
        total = len(self.filtered_games)
        load_count = min(self.batch_size, total)
        self.visible_count = load_count

        current_game = self.get_current_game()
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()

        for game in self.filtered_games[:load_count]:
            self._render_game_item(game)

        self.list_widget.setUpdatesEnabled(True)
        self._restore_current_item(current_game)
        self.update_count_label()

        # 连接到滚动条以支持触底加载
        scrollbar = self.list_widget.verticalScrollBar()
        try:
            scrollbar.valueChanged.disconnect(self._on_scroll)
        except TypeError:
            pass
        scrollbar.valueChanged.connect(self._on_scroll)

    def _restore_current_item(self, game):
        """在重新渲染后恢复当前选中项"""
        if not game:
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == game:
                self.list_widget.setCurrentItem(item)
                break

    def _on_scroll(self, value):
        """滚动条变化事件，触底时加载更多"""
        scrollbar = self.list_widget.verticalScrollBar()
        if scrollbar.maximum() == 0:
            return
        ratio = value / scrollbar.maximum()
        if ratio > 0.75 and self.visible_count < len(self.filtered_games):
            self._load_more()

    def _load_more(self):
        """加载下一批游戏"""
        old_count = self.visible_count
        new_count = min(old_count + self.batch_size, len(self.filtered_games))
        if new_count <= old_count:
            return

        current_game = self.get_current_game()
        self.list_widget.setUpdatesEnabled(False)

        for game in self.filtered_games[old_count:new_count]:
            self._render_game_item(game)

        self.visible_count = new_count
        self.list_widget.setUpdatesEnabled(True)
        self._restore_current_item(current_game)
        self.update_count_label()

    def _render_game_item(self, game):
        """渲染单个游戏列表项"""
        item_text = game.game
        if game.platform:
            item_text += f" [{game.platform}]"
        if game.is_file_missing:
            item_text = f"⚠ {item_text}"

        item = QListWidgetItem(item_text)

        logo_path = game.get_logo_path()
        if logo_path and logo_path.exists():
            item.setIcon(QIcon(str(logo_path)))

        if game.is_file_missing:
            item.setForeground(QColor("#ff4d4f"))

        if game in self.selected_games:
            bg, fg = self._get_selection_colors()
            item.setBackground(bg)
            item.setForeground(fg)

        item.setData(Qt.UserRole, game)
        self.list_widget.addItem(item)

    def set_platform_filter(self, platform: str):
        """由面板调用来设置平台过滤"""
        self.platform_filter = platform

    def update_count_label(self):
        """计数已移至面板层，保留空方法以兼容旧调用"""
        pass

    def apply_filters(self):
        """应用搜索与平台筛选（筛选条件由面板设置）"""
        text = (self.filter_text or "").strip().lower()
        selected_platform = self.platform_filter or ""
        filtered = []
        for game in self.games:
            platform_name = (game.platform or "")
            if selected_platform and platform_name != selected_platform:
                continue
            if text:
                developer = (game.developer or "")
                if (text not in game.game.lower() and
                    text not in platform_name.lower() and
                    text not in developer.lower()):
                    continue
            filtered.append(game)
        self.filtered_games = filtered
        self.update_list()

    def on_selection_changed(self, current, previous):
        """列表选择改变事件"""
        if current:
            game = current.data(Qt.UserRole)
            self.game_selected.emit(game)

    def get_current_game(self) -> Game:
        """获取当前选中的游戏"""
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return None

    def on_item_double_clicked(self, item: QListWidgetItem):
        """双击列表项：切换选择并播放视频"""
        if not item:
            return
        game = item.data(Qt.UserRole)
        self.list_widget.setCurrentItem(item)
        self.toggle_selection()
        self.game_activated.emit(game)

    def toggle_selection(self):
        """切换当前游戏的选择状态（发送信号让面板处理）"""
        current_game = self.get_current_game()
        if not current_game:
            return

        if current_game in self.selected_games:
            self.selected_games.remove(current_game)
        else:
            checker = self.duplicate_checker or self.existing_checker
            if checker and checker(current_game):
                QMessageBox.warning(self, tr("info"), tr("duplicate_warning"))
                return
            self.selected_games.add(current_game)

        self.update_list()
        self.selection_changed.emit(self.selected_games)

    def get_selected_games(self) -> Set[Game]:
        """获取所有选中的游戏"""
        return self.selected_games

    def clear_selection(self):
        """清空选择"""
        self.selected_games.clear()
        self.update_list()
        self.selection_changed.emit(self.selected_games)

    def select_all(self):
        """全选当前列表中的游戏"""
        for game in self.filtered_games:
            # 如果设置了重复检测（来源视图），则跳过已存在的游戏
            checker = self.duplicate_checker or self.existing_checker
            if checker and checker(game):
                continue
            self.selected_games.add(game)

        self.update_list()
        self.selection_changed.emit(self.selected_games)

    def _move_selection(self, delta: int):
        """按偏移移动当前选中项"""
        count = self.list_widget.count()
        if count == 0:
            return
        current_row = self.list_widget.currentRow()
        if current_row < 0:
            current_row = 0
        new_row = max(0, min(count - 1, current_row + delta))
        if new_row != current_row:
            self.list_widget.setCurrentRow(new_row)
        self.list_widget.setFocus(Qt.OtherFocusReason)

    def eventFilter(self, source, event):
        """事件过滤器"""
        if source == self.list_widget and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                self.toggle_selection()
                return True
            elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                current_game = self.get_current_game()
                if current_game:
                    self.game_activated.emit(current_game)
                return True
            elif event.key() == Qt.Key_J:
                self._move_selection(1)
                return True
            elif event.key() == Qt.Key_K:
                self._move_selection(-1)
                return True
        return super().eventFilter(source, event)
