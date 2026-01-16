"""
游戏列表组件（重构版）
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
                             QLineEdit, QLabel, QHBoxLayout, QComboBox, QProgressBar, QApplication,
                             QProgressDialog, QPushButton, QShortcut, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence, QColor
from typing import List, Set, Optional
from core.metadata_parser import Game
from core.task_system import TaskQueue, TaskType
from core.i18n import tr
from core.theme import apply_titlebar_theme


class GameListWidget(QWidget):
    """游戏列表组件"""
    
    game_selected = pyqtSignal(Game)
    game_activated = pyqtSignal(Game) # 新增激活信号（回车或双击）
    selection_changed = pyqtSignal(set)  # 发送选中的游戏集合
    platform_changed = pyqtSignal(str)   # 发送当前选择的平台名称
    
    def __init__(self):
        super().__init__()
        self.games: List[Game] = []
        self.filtered_games: List[Game] = []
        self.selected_games: Set[Game] = set()
        self.task_queue: Optional[TaskQueue] = None
        self.duplicate_checker = None  # 检查项目中是否已存在
        self.filter_text: str = ""
        # 分页配置
        self.page_size: int = 200
        self.current_page: int = 1
        self.loading_dialog: Optional[QProgressDialog] = None
        
        # 自动播放定时器
        self.autoplay_timer = QTimer()
        self.autoplay_timer.setSingleShot(True)
        self.autoplay_timer.setInterval(3000) # 5秒
        self.autoplay_timer.timeout.connect(self._on_autoplay_timeout)
        
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

        # 分页信息与按钮同一行
        pager_layout = QHBoxLayout()
        self.pagination_label = QLabel(tr("pagination_label", current=0, total_pages=0, start=0, end=0, total=0))
        self.pagination_label.setStyleSheet("color: #666; font-size: 9pt;")
        pager_layout.addWidget(self.pagination_label)
        pager_layout.addStretch()

        self.prev_page_btn = QPushButton(tr("prev_page"))
        self.prev_page_btn.clicked.connect(self.prev_page)
        self.prev_page_btn.setEnabled(False)
        pager_layout.addWidget(self.prev_page_btn)

        self.next_page_btn = QPushButton(tr("next_page"))
        self.next_page_btn.clicked.connect(self.next_page)
        self.next_page_btn.setEnabled(False)
        pager_layout.addWidget(self.next_page_btn)
        layout.addLayout(pager_layout)

        # 翻页快捷键
        QShortcut(QKeySequence(Qt.Key_PageUp), self, self.prev_page)
        QShortcut(QKeySequence(Qt.Key_PageDown), self, self.next_page)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left), self, self.prev_page)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right), self, self.next_page)

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
        self.prev_page_btn.setText(tr("prev_page"))
        self.next_page_btn.setText(tr("next_page"))
        self.hint_label.setText(tr("hint_label"))
        self.update_count_label()
        # 刷新分页标签
        total = len(self.filtered_games)
        total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 0
        start_index = 0 if total == 0 else (self.current_page - 1) * self.page_size
        end_index = min(start_index + self.page_size, total)
        self._update_pagination_label(total_pages, total, start_index, end_index)
    
    def set_games(self, games: List[Game]):
        """设置游戏列表"""
        self.games = games
        self.selected_games.clear()
        self.apply_filters(show_loading=True, message="正在加载游戏...")
    
    def set_task_queue(self, task_queue: TaskQueue):
        """设置任务队列"""
        self.task_queue = task_queue

    def set_duplicate_checker(self, checker):
        """设置重复检测回调，返回True表示已存在"""
        self.duplicate_checker = checker

    def update_list(self):
        """更新列表显示（分页渲染）"""
        total = len(self.filtered_games)
        total_pages = (total + self.page_size - 1) // self.page_size if total > 0 else 0
        if total_pages == 0:
            self.current_page = 1
        else:
            self.current_page = max(1, min(self.current_page, total_pages))

        start_index = 0 if total == 0 else (self.current_page - 1) * self.page_size
        end_index = min(start_index + self.page_size, total)

        current_game = self.get_current_game()
        self.list_widget.setUpdatesEnabled(False)
        self.list_widget.clear()

        for game in self.filtered_games[start_index:end_index]:
            item_text = f"{game.game}"
            if game.platform:
                item_text += f" [{game.platform}]"

            # 如果文件缺失，添加标记
            if game.is_file_missing:
                item_text = f"⚠ {item_text}"

            item = QListWidgetItem(item_text)

            logo_path = game.get_logo_path()
            if logo_path and logo_path.exists():
                icon = QIcon(str(logo_path))
                item.setIcon(icon)

            # 文件缺失显红
            if game.is_file_missing:
                item.setForeground(QColor("#ff4d4f"))

            if game in self.selected_games:
                bg, fg = self._get_selection_colors()
                item.setBackground(bg)
                item.setForeground(fg)

            item.setData(Qt.UserRole, game)
            self.list_widget.addItem(item)

        self.list_widget.setUpdatesEnabled(True)
        self._restore_current_item(current_game)
        self.update_count_label()
        self._update_pagination_label(total_pages, total, start_index, end_index)
        self._update_page_buttons(total_pages)

    def _restore_current_item(self, game):
        """在重新渲染后恢复当前选中项"""
        if not game:
            return
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.UserRole) == game:
                self.list_widget.setCurrentItem(item)
                break

    def _start_loading(self, message: str):
        """显示加载进度（模态弹窗）"""
        if self.loading_dialog is None:
            self.loading_dialog = QProgressDialog(message, None, 0, 0, self.window())
            self.loading_dialog.setCancelButton(None)
            self.loading_dialog.setWindowTitle("请稍候")
            self.loading_dialog.setWindowModality(Qt.ApplicationModal)
            self.loading_dialog.setMinimumDuration(0)
            self.loading_dialog.setAutoClose(False)
            self.loading_dialog.setAutoReset(False)
            self.loading_dialog.setLabelText(message)
            theme = getattr(self.window(), "current_theme", None)
            if theme:
                apply_titlebar_theme(self.loading_dialog, theme)
        else:
            self.loading_dialog.setLabelText(message)
        self.loading_dialog.show()
        QApplication.processEvents()

    def _finish_loading(self):
        """隐藏加载进度"""
        if self.loading_dialog:
            self.loading_dialog.hide()
            self.loading_dialog.deleteLater()
            self.loading_dialog = None
        QApplication.processEvents()

    def _update_pagination_label(self, total_pages: int, total: int, start_index: int, end_index: int):
        """更新分页信息"""
        if total == 0:
            self.pagination_label.setText(tr("pagination_label", current=0, total_pages=0, start=0, end=0, total=0))
            return
        current_page = self.current_page
        self.pagination_label.setText(
            tr("pagination_label", 
               current=current_page, 
               total_pages=total_pages, 
               start=start_index + 1, 
               end=end_index, 
               total=total)
        )

    def _update_page_buttons(self, total_pages: int):
        """更新翻页按钮状态"""
        has_pages = total_pages > 0
        self.prev_page_btn.setEnabled(has_pages and self.current_page > 1)
        self.next_page_btn.setEnabled(has_pages and self.current_page < total_pages)

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

    def next_page(self):
        """下一页"""
        total_pages = (len(self.filtered_games) + self.page_size - 1) // self.page_size if self.filtered_games else 0
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_list()
            # 选中第一项并聚焦
            if self.list_widget.count() > 0:
                self.list_widget.setCurrentRow(0)
            self.list_widget.setFocus()

    def prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_list()
            # 选中第一项并聚焦
            if self.list_widget.count() > 0:
                self.list_widget.setCurrentRow(0)
            self.list_widget.setFocus()

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
        self.apply_filters(show_loading=True, message=tr("refreshing_platforms"))

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
        self.apply_filters(show_loading=True, message=tr("filtering"))
    
    def on_platform_changed(self, index: int):
        """平台下拉选择变更"""
        self.apply_filters(show_loading=True, message=tr("filtering"))
        # 选择平台后将焦点移至游戏列表，方便快速浏览
        self.list_widget.setFocus()
        self.platform_changed.emit(self.get_current_platform() or "")
    
    def apply_filters(self, show_loading: bool = False, message: str = ""):
        """应用搜索与平台筛选"""
        if show_loading:
            self._start_loading(message or tr("loading_games"))
        try:
            self.current_page = 1
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
        finally:
            if show_loading:
                self._finish_loading()
    
    def on_selection_changed(self, current, previous):
        """列表选择改变事件"""
        # 停止之前的计时器
        self.autoplay_timer.stop()
        
        if current:
            game = current.data(Qt.UserRole)
            self.game_selected.emit(game)
            # 开启新的计时器
            self.autoplay_timer.start()
            
    def _on_autoplay_timeout(self):
        """计时器到时，触发自动播放"""
        current_game = self.get_current_game()
        if current_game:
            self.game_activated.emit(current_game)
    
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
        """切换当前游戏的选择状态"""
        current_game = self.get_current_game()
        if not current_game:
            return
        
        if current_game in self.selected_games:
            self.selected_games.remove(current_game)
            if self.task_queue:
                self.task_queue.remove_task(current_game)
        else:
            if self.duplicate_checker and self.duplicate_checker(current_game):
                QMessageBox.warning(self, tr("info"), tr("duplicate_warning"))
                return
            self.selected_games.add(current_game)
            if self.task_queue:
                self.task_queue.add_task(TaskType.ADD, current_game)
        
        self.update_list()
        self.selection_changed.emit(self.selected_games)
        
        # 强制更新一下列表项的选中状态显示
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            game = item.data(Qt.UserRole)
            if game == current_game:
                self.list_widget.setCurrentItem(item)
                break
    
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
