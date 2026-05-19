"""
游戏列表组件（复选框模式）
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QColor
from typing import List, Set
from core.metadata_parser import Game
from core.i18n import tr


class GameListWidget(QWidget):
    """游戏列表组件 — 复选框选择 + 单击预览"""

    game_selected = pyqtSignal(Game)
    game_activated = pyqtSignal(Game)
    selection_changed = pyqtSignal(set)

    def __init__(self):
        super().__init__()
        self.games: List[Game] = []
        self.filtered_games: List[Game] = []
        self.selected_games: Set[Game] = set()
        self.duplicate_checker = None
        self.existing_checker = None
        self.filter_text: str = ""
        self.platform_filter: str = ""
        self.batch_size: int = 300
        self.visible_count: int = 0
        self._updating_checks = False  # 防止 itemChanged 递归

        self.autoplay_timer = QTimer()
        self.init_ui()

    def init_ui(self):
        self.setMinimumWidth(380)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.currentItemChanged.connect(self._on_current_changed)
        self.list_widget.itemDoubleClicked.connect(self._on_double_clicked)
        self.list_widget.itemChanged.connect(self._on_item_check_changed)
        self.list_widget.setSpacing(2)
        self.list_widget.installEventFilter(self)
        self.list_widget.setFocusPolicy(Qt.StrongFocus)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.list_widget)
        layout.addWidget(self.list_widget)

    def retranslate_ui(self):
        pass

    def set_games(self, games: List[Game]):
        self.games = games
        self.selected_games.clear()
        self.apply_filters()

    def set_duplicate_checker(self, checker):
        self.duplicate_checker = checker

    def set_existing_checker(self, checker):
        self.existing_checker = checker

    def set_platform_filter(self, platform: str):
        self.platform_filter = platform

    def set_task_queue(self, task_queue):
        pass

    # ─── 渲染 ───

    def update_list(self):
        total = len(self.filtered_games)
        load_count = min(self.batch_size, total)
        self.visible_count = load_count

        current_game = self.get_current_game()
        self.list_widget.setUpdatesEnabled(False)
        self._updating_checks = True
        self.list_widget.clear()

        for game in self.filtered_games[:load_count]:
            self._render_game_item(game)

        self._updating_checks = False
        self.list_widget.setUpdatesEnabled(True)
        self._restore_current_item(current_game)

        scrollbar = self.list_widget.verticalScrollBar()
        try:
            scrollbar.valueChanged.disconnect(self._on_scroll)
        except TypeError:
            pass
        scrollbar.valueChanged.connect(self._on_scroll)

    def _restore_current_item(self, game):
        if not game:
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == game:
                self.list_widget.setCurrentItem(item)
                break

    def _on_scroll(self, value):
        scrollbar = self.list_widget.verticalScrollBar()
        if scrollbar.maximum() == 0:
            return
        if value / scrollbar.maximum() > 0.75 and self.visible_count < len(self.filtered_games):
            self._load_more()

    def _load_more(self):
        old_count = self.visible_count
        new_count = min(old_count + self.batch_size, len(self.filtered_games))
        if new_count <= old_count:
            return

        current_game = self.get_current_game()
        self.list_widget.setUpdatesEnabled(False)
        self._updating_checks = True

        for game in self.filtered_games[old_count:new_count]:
            self._render_game_item(game)

        self.visible_count = new_count
        self._updating_checks = False
        self.list_widget.setUpdatesEnabled(True)
        self._restore_current_item(current_game)

    def _render_game_item(self, game):
        text = game.game
        if game.platform:
            text += f"  [{game.platform}]"
        if game.is_file_missing:
            text = f"⚠ {text}"

        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if game in self.selected_games else Qt.Unchecked)
        item.setData(Qt.UserRole, game)

        logo_path = game.get_logo_path()
        if logo_path and logo_path.exists():
            item.setIcon(QIcon(str(logo_path)))

        if game.is_file_missing:
            item.setForeground(QColor("#ff4d4f"))

        # 已存在于目标中的游戏置灰
        checker = self.duplicate_checker or self.existing_checker
        if checker and checker(game):
            item.setForeground(QColor("#999999"))
            f = item.font()
            f.setItalic(True)
            item.setFont(f)

        self.list_widget.addItem(item)

    # ─── 筛选 ───

    def apply_filters(self):
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

    # ─── 交互 ───

    def _on_current_changed(self, current, previous):
        """光标移动 → 预览游戏"""
        if current:
            game = current.data(Qt.UserRole)
            self.game_selected.emit(game)

    def _on_item_check_changed(self, item):
        """复选框变更 → 更新选中集合"""
        if self._updating_checks:
            return
        game = item.data(Qt.UserRole)
        if not game:
            return
        if item.checkState() == Qt.Checked:
            checker = self.duplicate_checker or self.existing_checker
            if checker and checker(game):
                QMessageBox.warning(self, tr("info"), tr("duplicate_warning"))
                self._updating_checks = True
                item.setCheckState(Qt.Unchecked)
                self._updating_checks = False
                return
            self.selected_games.add(game)
        else:
            self.selected_games.discard(game)
        self.selection_changed.emit(self.selected_games)

    def _on_double_clicked(self, item):
        """双击 → 切换复选框 + 触发激活"""
        if not item:
            return
        game = item.data(Qt.UserRole)
        new_state = Qt.Unchecked if game in self.selected_games else Qt.Checked
        self._updating_checks = True
        item.setCheckState(new_state)
        self._updating_checks = False
        # 手动触发 check change 逻辑
        self._on_item_check_changed(item)
        self.game_activated.emit(game)

    def get_current_game(self) -> Game:
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return None

    def get_selected_games(self) -> Set[Game]:
        return self.selected_games

    def clear_selection(self):
        self.selected_games.clear()
        self._updating_checks = True
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)
        self._updating_checks = False
        self.selection_changed.emit(self.selected_games)

    def select_all(self):
        for game in self.filtered_games:
            checker = self.duplicate_checker or self.existing_checker
            if checker and checker(game):
                continue
            self.selected_games.add(game)
        self._updating_checks = True
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            game = item.data(Qt.UserRole)
            if game in self.selected_games:
                item.setCheckState(Qt.Checked)
        self._updating_checks = False
        self.selection_changed.emit(self.selected_games)

    def _move_cursor(self, delta: int):
        count = self.list_widget.count()
        if count == 0:
            return
        row = self.list_widget.currentRow()
        if row < 0:
            row = 0
        new_row = max(0, min(count - 1, row + delta))
        if new_row != row:
            self.list_widget.setCurrentRow(new_row)
        self.list_widget.setFocus(Qt.OtherFocusReason)

    def eventFilter(self, source, event):
        if source == self.list_widget and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                # Space → 切换复选框
                item = self.list_widget.currentItem()
                if item:
                    new_state = Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked
                    self._updating_checks = True
                    item.setCheckState(new_state)
                    self._updating_checks = False
                    self._on_item_check_changed(item)
                return True
            elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
                # Enter → 触发激活（视频/运行）
                game = self.get_current_game()
                if game:
                    self.game_activated.emit(game)
                return True
            elif event.key() == Qt.Key_J:
                self._move_cursor(1)
                return True
            elif event.key() == Qt.Key_K:
                self._move_cursor(-1)
                return True
        return super().eventFilter(source, event)
