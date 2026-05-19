"""
游戏列表组件（重构版）
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QLineEdit, QLabel, QHBoxLayout, QComboBox, QApplication,
                             QShortcut, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QColor
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
        # 批量加载配置
        self.batch_size: int = 300
        self.visible_count: int = 0

        # Temporary compatibility stubs (removed in Task 8)
        self.autoplay_timer = QTimer()

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        self.setMinimumWidth(380)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # 搜索与平台筛选
        search_layout = QHBoxLayout()
        self.search_label = QLabel(tr("search_label"))
        search_layout.addWidget(self.search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("输入游戏名称、平台或开发者...")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        search_layout.addWidget(self.search_box)

        self.platform_label_ui = QLabel(tr("platform_label"))
        search_layout.addWidget(self.platform_label_ui)

        self.platform_combo = QComboBox()
        self.platform_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.platform_combo.addItem(tr("all_platforms"), "")
        self.platform_combo.currentIndexChanged.connect(self.on_platform_changed)
        search_layout.addWidget(self.platform_combo)

        layout.addLayout(search_layout)

        # 统计
        self.count_label = QLabel(tr("game_count_label", total=0, selected=0))
        layout.addWidget(self.count_label)

        # 平台与搜索快捷键
        self.shortcut_p = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcut_p.setContext(Qt.ApplicationShortcut)
        self.shortcut_p.activated.connect(self.focus_platform_combo)

        self.shortcut_f = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_f.setContext(Qt.ApplicationShortcut)
        self.shortcut_f.activated.connect(self.focus_search_box)

        self.shortcut_l = QShortcut(QKeySequence("Ctrl+L"), self)
        self.shortcut_l.setContext(Qt.ApplicationShortcut)
        self.shortcut_l.activated.connect(self.focus_game_list)

        QShortcut(QKeySequence("Alt+Up"), self, self.prev_platform)
        QShortcut(QKeySequence("Alt+Down"), self, self.next_platform)

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

        # 提示标签
        self.hint_label = QLabel(tr("hint_label"))
        self.hint_label.setStyleSheet("color: #555; font-size: 8.5pt; line-height: 140%;")
        self.hint_label.setWordWrap(True)
        self.hint_label.setTextFormat(Qt.RichText)
        self.hint_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.hint_label)

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
        self.search_label.setText(tr("search_label"))
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.platform_label_ui.setText(tr("platform_label"))
        # 下拉框需要特殊处理第一个元素
        self.platform_combo.setItemText(0, tr("all_platforms"))
        self.hint_label.setText(tr("hint_label"))
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

    def focus_platform_combo(self):
        """聚焦平台选择框并展开"""
        self.platform_combo.setFocus()
        self.platform_combo.showPopup()

    def focus_search_box(self):
        """聚焦搜索框"""
        self.search_box.setFocus()
        self.search_box.selectAll()

    def focus_game_list(self):
        """聚焦游戏列表"""
        # 强制激活窗口并设置焦点
        self.list_widget.activateWindow()
        self.list_widget.setFocus(Qt.OtherFocusReason)
        if self.list_widget.count() > 0:
            if not self.list_widget.currentItem():
                self.list_widget.setCurrentRow(0)
            else:
                # 确保当前项可见并被视觉选中
                self.list_widget.scrollToItem(self.list_widget.currentItem())

    def next_platform(self):
        """切换到下一个平台"""
        count = self.platform_combo.count()
        if count <= 1:
            return
        current = self.platform_combo.currentIndex()
        next_idx = (current + 1) % count
        self.platform_combo.setCurrentIndex(next_idx)

    def prev_platform(self):
        """切换到上一个平台"""
        count = self.platform_combo.count()
        if count <= 1:
            return
        current = self.platform_combo.currentIndex()
        prev_idx = (current - 1 + count) % count
        self.platform_combo.setCurrentIndex(prev_idx)

    def update_count_label(self):
        """更新计数标签"""
        total = len(self.filtered_games)
        selected = len(self.selected_games)
        self.count_label.setText(tr("game_count_label", total=total, selected=selected))

    def set_platforms(self, platforms: List[str]):
        """更新平台下拉列表"""
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem(tr("all_platforms"), "")
        max_text = tr("all_platforms")
        for platform in sorted(platforms):
            self.platform_combo.addItem(platform, platform)
            if len(platform) > len(max_text):
                max_text = platform
        self.platform_combo.setCurrentIndex(0)
        self.platform_combo.blockSignals(False)
        self._adjust_platform_combo_width(max_text)
        self.apply_filters()

    def _adjust_platform_combo_width(self, max_text: str):
        """根据最长平台名称调整下拉宽度"""
        fm = self.platform_combo.fontMetrics()
        width = fm.horizontalAdvance(max_text + "  ") + 24  # 文本+左右内边距
        width = max(width, 140)
        self.platform_combo.setMinimumWidth(width)
        self.platform_combo.setMinimumContentsLength(len(max_text) + 2)
        try:
            view = self.platform_combo.view()
            view.setMinimumWidth(width + 20)
        except Exception:
            pass

    def on_search_text_changed(self, text: str):
        """搜索框文本变更事件"""
        self.filter_text = text or ""
        self.apply_filters()

    def on_platform_changed(self, index: int):
        """平台下拉选择变更"""
        self.apply_filters()
        self.list_widget.setFocus()
        self.platform_changed.emit(self.get_current_platform() or "")

    def apply_filters(self):
        """应用搜索与平台筛选"""
        text = (self.filter_text or "").strip().lower()
        selected_platform = self.platform_combo.currentData()
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

    def get_current_platform(self) -> str:
        """获取当前选择的平台"""
        return self.platform_combo.currentData()

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
            if self.duplicate_checker and self.duplicate_checker(current_game):
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
            if self.duplicate_checker and self.duplicate_checker(game):
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
