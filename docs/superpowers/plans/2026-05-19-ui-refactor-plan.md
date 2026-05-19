# UI Refactor: 双栏文件管理器 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Pegasus Game Filter 从"单栏视图切换 + 任务队列"模式重构为"双栏文件管理器 + 即时操作"模式。

**Architecture:** 左侧 SourcePanel 展示来源 ROM，右侧 CollectionPanel 展示收藏 ROM，中间 OperateBar 提供复制/删除按钮，底部 PreviewPanel 展示游戏详情。所有操作即时生效，不再有任务队列或视图切换。

**Tech Stack:** Python 3.14, PyQt5 5.15.9, PyQt-Fluent-Widgets 1.11.2

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `core/game_manager.py` | 修改 | 新增 `add_game()` / `remove_game()` 直接操作方法 |
| `ui/game_list_widget.py` | 修改 | 去掉分页，改为批量加载+触底追加，去掉 task_queue 依赖 |
| `ui/game_detail_widget.py` | 修改 | 适配底部预览面板布局（水平排列封面和视频） |
| `ui/operate_bar.py` | 新建 | 中间操作区：复制按钮、删除按钮 |
| `ui/source_panel.py` | 新建 | 来源面板：封装 GameListWidget + 搜索 + 平台过滤 |
| `ui/collection_panel.py` | 新建 | 收藏面板：封装 GameListWidget + 搜索 + 平台过滤 + 删除 |
| `ui/preview_panel.py` | 新建 | 底部可折叠预览面板 |
| `ui/dual_panel_layout.py` | 新建 | 双栏布局容器（QSplitter + OperateBar + PreviewPanel） |
| `ui/main_window.py` | 重写 | 大幅精简，移除视图切换/任务队列/工具栏，使用 DualPanelLayout |
| `ui/log_window.py` | 删除 | 任务执行日志不再需要 |
| `core/__init__.py` | 修改 | 更新导出（移除 TaskQueue 相关） |
| `core/i18n.py` | 修改 | 新增/更新翻译字符串 |

---

### Task 1: GameManager 新增直接操作方法

**Files:**
- Modify: `core/game_manager.py`

- [ ] **Step 1: 在 GameManager 中新增 `add_game(source_game)` 方法**

在 `core/game_manager.py` 的 `GameManager` 类中新增方法：

```python
def add_game(self, source_game: Game, progress_callback=None) -> bool:
    """直接添加一个游戏到收藏集，执行完整的文件复制流程"""
    platform = source_game.platform
    platform_path = self.roms_root / platform
    platform_path.mkdir(parents=True, exist_ok=True)

    # 创建 media 目录
    media_dir_name = Path(source_game.file).stem or source_game.game
    media_dir = platform_path / "media" / media_dir_name
    media_dir.mkdir(parents=True, exist_ok=True)

    # 复制游戏文件
    source_file = source_game.platform_path / source_game.file
    dest_file = platform_path / source_game.file
    if source_file.exists():
        shutil.copy2(source_file, dest_file)

    # 复制 logo
    logo_path = source_game.get_logo_path()
    if logo_path and logo_path.exists():
        shutil.copy2(logo_path, media_dir / logo_path.name)

    # 复制封面
    boxfront_path = source_game.get_boxfront_path()
    if boxfront_path and boxfront_path.exists():
        shutil.copy2(boxfront_path, media_dir / boxfront_path.name)

    # 复制视频
    video_path = source_game.get_video_path()
    if video_path and video_path.exists():
        shutil.copy2(video_path, media_dir / video_path.name)

    # 合并 Header 配置
    project_header = self.headers.get(platform, "")
    try:
        source_header, _ = MetadataParser.parse_platform_directory(source_game.platform_path)
        merged_header = MetadataParser.merge_header_fields(
            project_header, source_header,
            ["collection", "sort-by", "extensions", "launch"], platform
        )
        if merged_header != project_header:
            self.headers[platform] = merged_header
    except Exception:
        pass

    # 更新游戏列表和元数据文件
    new_game = self._create_game_copy(source_game, platform_path)
    self._upsert_platform_game(platform, new_game)

    metadata_file = platform_path / "metadata.pegasus.txt"
    header = self.headers.get(platform, "")
    MetadataParser.write_metadata(self.platforms[platform], metadata_file, header)

    return True
```

- [ ] **Step 2: 在 GameManager 中新增 `remove_game(game)` 方法**

```python
def remove_game(self, game: Game) -> bool:
    """直接删除一个游戏及其媒体资源"""
    platform = game.platform
    platform_path = self.roms_root / platform

    # 删除游戏文件
    game_file = platform_path / game.file
    if game_file.exists():
        game_file.unlink()

    # 删除 media 目录
    media_dir_name = Path(game.file).stem or game.game
    media_dir = platform_path / "media" / media_dir_name
    if media_dir.exists():
        shutil.rmtree(media_dir)

    # 从列表中移除并更新元数据
    if platform in self.platforms:
        self.platforms[platform] = [
            g for g in self.platforms[platform]
            if g.game != game.game
        ]
        metadata_file = platform_path / "metadata.pegasus.txt"
        header = self.headers.get(platform, "")
        MetadataParser.write_metadata(self.platforms[platform], metadata_file, header)

    return True
```

- [ ] **Step 3: 提交**

```bash
git add core/game_manager.py
git commit -m "feat: add direct add_game/remove_game methods to GameManager"
```

---

### Task 2: GameListWidget 去掉分页，改为批量加载

**Files:**
- Modify: `ui/game_list_widget.py`

- [ ] **Step 1: 移除分页相关代码**

删除以下属性：
- `self.page_size`
- `self.current_page`
- `self.loading_dialog`
- `self.autoplay_timer` (移至面板层)

删除以下方法：
- `_start_loading()` / `_finish_loading()`
- `_update_pagination_label()`
- `_update_page_buttons()`
- `next_page()` / `prev_page()`
- `_on_autoplay_timeout()` (移至面板层)

删除分页 UI 控件创建代码（`pagination_label`, `prev_page_btn`, `next_page_btn`）。

- [ ] **Step 2: 实现批量加载 + 触底追加**

在 `__init__` 中添加：
```python
self.batch_size = 300          # 每批渲染数量
self.visible_count = 0         # 当前已渲染数量
```

修改 `update_list()`：
```python
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
```

新增 `_on_scroll()` 方法：
```python
def _on_scroll(self, value):
    """滚动条变化事件，触底时加载更多"""
    scrollbar = self.list_widget.verticalScrollBar()
    if scrollbar.maximum() == 0:
        return
    ratio = value / scrollbar.maximum()
    if ratio > 0.75 and self.visible_count < len(self.filtered_games):
        self._load_more()
```

新增 `_load_more()` 方法：
```python
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
```

新增 `_render_game_item()` 辅助方法：
```python
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
```

- [ ] **Step 3: 去掉 task_queue 依赖**

移除 `set_task_queue()` 方法。修改 `toggle_selection()`：
```python
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
```

从 `__init__.py` 导入中移除 `TaskQueue`, `TaskType` 相关导入。

- [ ] **Step 4: 新增 `mark_existing()` 和 `mark_modified()` 方法**

```python
def set_existing_checker(self, checker):
    """设置已存在检测回调（返回 True 表示目标中已存在）"""
    self.existing_checker = checker

def set_modified_marker(self, marker):
    """设置元数据修改标记回调（返回 True 表示已修改）"""
    self.modified_marker = marker
```

在 `_render_game_item()` 中使用这些标记来设置灰色斜体或 ✎ 图标。

- [ ] **Step 5: 添加 Shift+Click 范围选择**

在 `eventFilter()` 的 KeyPress 分支前追加：
```python
def mousePressEvent(self, event):
    """重写鼠标点击以支持 Shift+Click 范围选择"""
    if event.modifiers() & Qt.ShiftModifier:
        item = self.list_widget.itemAt(event.pos())
        if item and self._last_clicked_item:
            start = self.list_widget.row(self._last_clicked_item)
            end = self.list_widget.row(item)
            for i in range(min(start, end), max(start, end) + 1):
                game = self.list_widget.item(i).data(Qt.UserRole)
                if game:
                    self.selected_games.add(game)
                    self.list_widget.item(i).setSelected(True)
            self.update_list()
            self.selection_changed.emit(self.selected_games)
    else:
        item = self.list_widget.itemAt(event.pos())
        if item:
            self._last_clicked_item = item
    super().mousePressEvent(event)
```

注意：`mousePressEvent` 是 `QListWidget` 的，不是 `GameListWidget`（QWidget）的。需要改用事件过滤器或者修改为让 `list_widget` 的子类处理。稳妥做法：在 `eventFilter` 中处理 `MouseButtonPress` 事件。

- [ ] **Step 6: 提交**

```bash
git add ui/game_list_widget.py
git commit -m "refactor: remove pagination, add batch loading with scroll-to-load in GameListWidget"
```

---

### Task 3: 创建 OperateBar 中间操作区

**Files:**
- Create: `ui/operate_bar.py`

- [ ] **Step 1: 创建 OperateBar 类**

```python
"""
中间操作区组件
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
from core.i18n import tr


class OperateBar(QWidget):
    """中间操作区：复制和删除按钮"""

    copy_clicked = pyqtSignal()
    delete_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(80)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)
        self.setLayout(layout)

        layout.addStretch()

        self.copy_btn = QPushButton("→\n" + tr("copy_selection"))
        self.copy_btn.setFixedSize(60, 60)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #4CAF50; color: white;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.copy_btn.clicked.connect(self.copy_clicked)
        layout.addWidget(self.copy_btn, alignment=Qt.AlignCenter)

        self.delete_btn = QPushButton("←\n" + tr("delete_selection"))
        self.delete_btn.setFixedSize(60, 60)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px; font-weight: bold;
                background-color: #f44336; color: white;
                border-radius: 8px; border: none;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:disabled { background-color: #888; }
        """)
        self.delete_btn.clicked.connect(self.delete_clicked)
        layout.addWidget(self.delete_btn, alignment=Qt.AlignCenter)

        layout.addStretch()

    def set_copy_enabled(self, enabled: bool):
        self.copy_btn.setEnabled(enabled)

    def set_delete_enabled(self, enabled: bool):
        self.delete_btn.setEnabled(enabled)

    def retranslate_ui(self):
        self.copy_btn.setText("→\n" + tr("copy_selection"))
        self.delete_btn.setText("←\n" + tr("delete_selection"))
```

- [ ] **Step 2: 提交**

```bash
git add ui/operate_bar.py
git commit -m "feat: add OperateBar widget for copy/delete actions"
```

---

### Task 4: 创建 SourcePanel 来源面板

**Files:**
- Create: `ui/source_panel.py`

- [ ] **Step 1: 创建 SourcePanel 类**

```python
"""
来源面板组件（左侧）
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QShortcut)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QKeySequence
from ui.game_list_widget import GameListWidget
from core.i18n import tr


class SourcePanel(QWidget):
    """来源 ROM 面板"""

    game_selected = pyqtSignal(object)
    game_activated = pyqtSignal(object)
    copy_requested = pyqtSignal(list)
    selection_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.games = []
        self._init_ui()

        # 自动播放计时器
        self.autoplay_timer = QTimer()
        self.autoplay_timer.setSingleShot(True)
        self.autoplay_timer.setInterval(500)
        self.autoplay_timer.timeout.connect(self._on_autoplay)

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 标题
        title_label = QLabel(tr("source_title"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(title_label)

        # 搜索与平台过滤
        filter_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.search_box.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_box)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem(tr("all_platforms"), "")
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        filter_layout.addWidget(self.platform_combo)
        layout.addLayout(filter_layout)

        # 游戏列表
        self.game_list = GameListWidget()
        self.game_list.game_selected.connect(self._on_game_selected)
        self.game_list.selection_changed.connect(self._on_selection_changed)
        self.game_list.game_activated.connect(self._on_game_activated)
        layout.addWidget(self.game_list)

        # 计数标签
        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        # 快捷键
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+P"), self, self._focus_platform)

    def set_games(self, games):
        self.games = games
        self.game_list.set_games(games)

    def set_platforms(self, platforms):
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem(tr("all_platforms"), "")
        for p in sorted(platforms):
            self.platform_combo.addItem(p, p)
        self.platform_combo.blockSignals(False)

    def set_existing_checker(self, checker):
        self.game_list.set_existing_checker(checker)

    def get_selected_games(self):
        return list(self.game_list.get_selected_games())

    def get_current_game(self):
        return self.game_list.get_current_game()

    def refresh(self):
        self.game_list.update_list()

    def _on_search(self, text):
        self.game_list.filter_text = text
        self.game_list.apply_filters()

    def _on_platform_changed(self, index):
        self.game_list.apply_filters()
        self.game_list.list_widget.setFocus()

    def _on_game_selected(self, game):
        self.autoplay_timer.stop()
        self.game_selected.emit(game)
        self.autoplay_timer.start()

    def _on_game_activated(self, game):
        self.game_activated.emit(game)

    def _on_autoplay(self):
        current = self.game_list.get_current_game()
        if current:
            self.game_activated.emit(current)

    def _on_selection_changed(self, selected):
        games = list(selected)
        self.selection_changed.emit(games)
        self.count_label.setText(tr("game_count_label",
            total=len(self.game_list.filtered_games),
            selected=len(games)))

    def _focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()

    def _focus_platform(self):
        self.platform_combo.setFocus()
        self.platform_combo.showPopup()

    def retranslate_ui(self):
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.platform_combo.setItemText(0, tr("all_platforms"))
        self.game_list.retranslate_ui()
        self.count_label.setText(tr("game_count_label",
            total=len(self.game_list.filtered_games),
            selected=len(self.game_list.get_selected_games())))
```

- [ ] **Step 2: 提交**

```bash
git add ui/source_panel.py
git commit -m "feat: add SourcePanel widget for source ROM browsing"
```

---

### Task 5: 创建 CollectionPanel 收藏面板

**Files:**
- Create: `ui/collection_panel.py`

- [ ] **Step 1: 创建 CollectionPanel 类**

```python
"""
收藏面板组件（右侧）
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QShortcut, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QKeySequence
from ui.game_list_widget import GameListWidget
from core.i18n import tr


class CollectionPanel(QWidget):
    """收藏 ROM 面板"""

    game_selected = pyqtSignal(object)
    game_activated = pyqtSignal(object)
    delete_requested = pyqtSignal(list)
    selection_changed = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.games = []
        self._init_ui()

        self.autoplay_timer = QTimer()
        self.autoplay_timer.setSingleShot(True)
        self.autoplay_timer.setInterval(500)
        self.autoplay_timer.timeout.connect(self._on_autoplay)

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        title_label = QLabel(tr("collection_title"))
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 4px;")
        layout.addWidget(title_label)

        filter_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.search_box.textChanged.connect(self._on_search)
        filter_layout.addWidget(self.search_box)

        self.platform_combo = QComboBox()
        self.platform_combo.addItem(tr("all_platforms"), "")
        self.platform_combo.currentIndexChanged.connect(self._on_platform_changed)
        filter_layout.addWidget(self.platform_combo)
        layout.addLayout(filter_layout)

        self.game_list = GameListWidget()
        self.game_list.game_selected.connect(self._on_game_selected)
        self.game_list.selection_changed.connect(self._on_selection_changed)
        self.game_list.game_activated.connect(self._on_game_activated)
        layout.addWidget(self.game_list)

        self.count_label = QLabel()
        layout.addWidget(self.count_label)

        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+P"), self, self._focus_platform)
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._on_delete_key)
        QShortcut(QKeySequence("Del"), self, self._on_delete_key)

    def set_games(self, games):
        self.games = games
        self.game_list.set_games(games)

    def set_platforms(self, platforms):
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem(tr("all_platforms"), "")
        for p in sorted(platforms):
            self.platform_combo.addItem(p, p)
        self.platform_combo.blockSignals(False)

    def set_modified_marker(self, marker):
        self.game_list.set_modified_marker(marker)

    def get_selected_games(self):
        return list(self.game_list.get_selected_games())

    def get_current_game(self):
        return self.game_list.get_current_game()

    def refresh(self):
        self.game_list.update_list()

    def _on_search(self, text):
        self.game_list.filter_text = text
        self.game_list.apply_filters()

    def _on_platform_changed(self, index):
        self.game_list.apply_filters()
        self.game_list.list_widget.setFocus()

    def _on_game_selected(self, game):
        self.autoplay_timer.stop()
        self.game_selected.emit(game)
        self.autoplay_timer.start()

    def _on_game_activated(self, game):
        self.game_activated.emit(game)

    def _on_autoplay(self):
        current = self.game_list.get_current_game()
        if current:
            self.game_activated.emit(current)

    def _on_selection_changed(self, selected):
        games = list(selected)
        self.selection_changed.emit(games)
        self.count_label.setText(tr("game_count_label",
            total=len(self.game_list.filtered_games),
            selected=len(games)))

    def _on_delete_key(self):
        selected = self.get_selected_games()
        if selected:
            self.delete_requested.emit(selected)

    def _focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()

    def _focus_platform(self):
        self.platform_combo.setFocus()
        self.platform_combo.showPopup()

    def retranslate_ui(self):
        self.search_box.setPlaceholderText(tr("search_placeholder"))
        self.platform_combo.setItemText(0, tr("all_platforms"))
        self.game_list.retranslate_ui()
        self.count_label.setText(tr("game_count_label",
            total=len(self.game_list.filtered_games),
            selected=len(self.game_list.get_selected_games())))
```

- [ ] **Step 2: 提交**

```bash
git add ui/collection_panel.py
git commit -m "feat: add CollectionPanel widget for collection ROM management"
```

---

### Task 6: 创建 PreviewPanel 底部预览面板

**Files:**
- Create: `ui/preview_panel.py`

- [ ] **Step 1: 创建 PreviewPanel 类**

```python
"""
底部可折叠预览面板
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QTextEdit, QPushButton, QFormLayout)
from PyQt5.QtCore import pyqtSignal, Qt, QUrl
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
        btn_layout.addStretch()
        info_layout.addLayout(btn_layout)

        content_layout.addWidget(info_widget, stretch=1)

        # 右侧：视频
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedSize(320, 220)
        self.video_widget.hide()
        content_layout.addWidget(self.video_widget)

        self.playlist = QMediaPlaylist()
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setPlaylist(self.playlist)
        self.media_player.setVideoOutput(self.video_widget)

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
        self._load_video(game)

        self.edit_btn.setVisible(editable)

    def hide_panel(self):
        self.setVisible(False)
        self.stop_video()

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
                self.playlist.clear()
                self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(str(full_path))))
                self.playlist.setCurrentIndex(0)
                self.video_widget.show()
                self.media_player.play()
                return
        self.video_widget.hide()
        self.media_player.stop()

    def stop_video(self):
        self.media_player.stop()
        self.media_player.setMedia(QMediaContent())
        self.playlist.clear()

    def retranslate_ui(self):
        arrow = "▲" if self._collapsed else "▼"
        self.toggle_btn.setText(f"{arrow}  {tr('preview_panel')}")
        self.edit_btn.setText(tr("edit_metadata"))
        self.run_btn.setText(tr("run_game"))
```

- [ ] **Step 2: 提交**

```bash
git add ui/preview_panel.py
git commit -m "feat: add collapsible PreviewPanel for game details"
```

---

### Task 7: 创建 DualPanelLayout 主布局容器

**Files:**
- Create: `ui/dual_panel_layout.py`

- [ ] **Step 1: 创建 DualPanelLayout 类**

```python
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
```

- [ ] **Step 2: 提交**

```bash
git add ui/dual_panel_layout.py
git commit -m "feat: add DualPanelLayout container with source/collection/operate/preview"
```

---

### Task 8: 重写 MainWindow

**Files:**
- Modify: `ui/main_window.py` (大改)

- [ ] **Step 1: 重写 MainWindow，使用 DualPanelLayout**

`ui/main_window.py` 完整重写为精简版 (~400 行)：

```python
"""
主窗口（双栏文件管理器重构版）
"""
from pathlib import Path
import subprocess
import shlex
import shutil
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QAction,
                             QFileDialog, QMessageBox, QInputDialog, QApplication,
                             QProgressDialog, QMenu, QLabel)
from PyQt5.QtCore import Qt, QSettings, QTimer
from PyQt5.QtGui import QKeySequence
from core.project import Project
from core.game_manager import GameManager
from core.i18n import tr, set_lang, get_lang
from core.theme import build_stylesheet, available_themes, apply_titlebar_theme, load_icon
from core.metadata_parser import MetadataParser
from ui.dual_panel_layout import DualPanelLayout
from ui.about_dialog import AboutDialog
from ui.project_settings_dialog import ProjectSettingsDialog
from ui.startup_dialog import StartupDialog
from ui.metadata_edit_dialog import MetadataEditDialog
from ui.metadata_extract_dialog import MetadataExtractDialog
from ui.metadata_merge_dialog import MetadataMergeDialog


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.project = None
        self.source_manager = None
        self.collection_manager = None

        self.settings = QSettings("PegasusGameFilter", "App")
        self.current_theme = self.settings.value("theme", "dark")

        self.init_ui()
        self.setup_shortcuts()
        QTimer.singleShot(100, self.show_startup_dialog)

    def init_ui(self):
        self.setWindowTitle(tr("app_title"))
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setGeometry(100, 100, 1400, 900)

        self.create_menu_bar()

        # 双栏布局作为中央组件
        self.dual_panel = DualPanelLayout()
        self.dual_panel.copy_requested.connect(self.copy_games)
        self.dual_panel.delete_requested.connect(self.delete_games)
        self.dual_panel.edit_metadata_requested.connect(self.edit_metadata)
        self.dual_panel.run_game_requested.connect(self.run_game)
        self.setCentralWidget(self.dual_panel)

        self.apply_theme(self.current_theme)

        # 状态栏
        self.status_label = QLabel(tr("status_no_project"))
        self.statusBar().addWidget(self.status_label)

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.clear()

        # 文件
        file_menu = menubar.addMenu(tr("menu_file"))
        for label, shortcut, handler in [
            (tr("menu_new_project"), QKeySequence.New, self.new_project),
            (tr("menu_open_project"), QKeySequence.Open, self.open_project),
        ]:
            a = QAction(label, self)
            a.setShortcut(shortcut)
            a.triggered.connect(handler)
            file_menu.addAction(a)

        self.recent_projects_menu = file_menu.addMenu(tr("menu_recent_projects"))

        save_action = QAction(tr("menu_save_project"), self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        settings_action = QAction(tr("menu_project_settings"), self)
        settings_action.triggered.connect(self.show_project_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction(tr("menu_exit"), self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 工具
        tools_menu = menubar.addMenu(tr("menu_tools"))
        for label, shortcut, handler in [
            (tr("menu_extract_metadata"), "Ctrl+Alt+E", self.extract_metadata_tool),
            (tr("menu_merge_metadata"), "Ctrl+Alt+M", self.merge_metadata_tool),
        ]:
            a = QAction(label, self)
            a.setShortcut(QKeySequence(shortcut))
            a.triggered.connect(handler)
            tools_menu.addAction(a)

        # 批量添加
        batch_action = QAction(tr("batch_add"), self)
        batch_action.setShortcut(QKeySequence("Ctrl+B"))
        batch_action.triggered.connect(self.batch_add_games)
        tools_menu.addAction(batch_action)

        # 设置
        settings_menu = menubar.addMenu(tr("menu_settings"))
        lang_submenu = settings_menu.addMenu(tr("menu_language"))
        for code, name in [("zh", "简体中文"), ("en", "English")]:
            a = QAction(name, self)
            a.setCheckable(True)
            a.setChecked(get_lang() == code)
            a.triggered.connect(lambda checked, c=code: self.change_language(c))
            lang_submenu.addAction(a)

        self.theme_menu = settings_menu.addMenu(tr("menu_theme"))
        self.theme_actions = {}
        for idx, key in enumerate(available_themes(), start=1):
            a = QAction(tr(f"theme_{key}"), self)
            a.setCheckable(True)
            a.setShortcut(QKeySequence(f"Ctrl+Alt+{idx}"))
            a.triggered.connect(lambda checked, t=key: self.set_theme(t))
            self.theme_menu.addAction(a)
            self.theme_actions[key] = a
        self._update_theme_menu_checks()

        # 帮助
        help_menu = menubar.addMenu(tr("menu_help"))
        about_action = QAction(tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_shortcuts(self):
        from PyQt5.QtWidgets import QShortcut
        QShortcut(QKeySequence(Qt.Key_Tab), self, self._switch_focus)
        QShortcut(QKeySequence(Qt.Key_F5), self, self._on_f5)

    def _switch_focus(self):
        """Tab 切换焦点到另一侧面板"""
        sp = self.dual_panel.source_panel
        cp = self.dual_panel.collection_panel
        if sp.game_list.list_widget.hasFocus():
            cp.game_list.list_widget.setFocus()
            if cp.game_list.list_widget.count() > 0:
                cp.game_list.list_widget.setCurrentRow(0)
        else:
            sp.game_list.list_widget.setFocus()
            if sp.game_list.list_widget.count() > 0:
                sp.game_list.list_widget.setCurrentRow(0)

    def _on_f5(self):
        """F5 复制选中的来源游戏"""
        if self.dual_panel.source_panel.game_list.list_widget.hasFocus():
            self.copy_games(self.dual_panel.source_panel.get_selected_games())

    # ─── 项目管理 ──────────────────────────────────────

    def new_project(self):
        name, ok = QInputDialog.getText(self, tr("dialog_new_project"), tr("dialog_project_name"))
        if not ok or not name:
            return
        source_dir = QFileDialog.getExistingDirectory(self, tr("dialog_select_source"))
        if not source_dir:
            return
        project_dir = QFileDialog.getExistingDirectory(self, tr("dialog_select_project"))
        if not project_dir:
            return
        self.project = Project(name, project_dir, source_dir)
        save_path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog_save_project"), f"{name}.json", "JSON Files (*.json)")
        if save_path:
            save_path = Path(save_path)
            self.project.save(save_path)
            self.add_to_recent_projects(save_path)
        self.init_managers()

    def open_project(self, filepath=None):
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, tr("menu_open_project"), "", "JSON Files (*.json)")
        if not filepath:
            return
        filepath = Path(filepath)
        self.project = Project.load(filepath)
        if not self.project:
            QMessageBox.warning(self, tr("error"), tr("msg_load_failed"))
            return
        self.add_to_recent_projects(filepath)
        self.init_managers()

    def save_project(self):
        if not self.project or not self.project.project_file:
            QMessageBox.warning(self, tr("info"), tr("status_no_project"))
            return
        self.project.save(self.project.project_file)
        self.statusBar().showMessage(tr("project_saved"), 2000)

    def init_managers(self):
        try:
            self.source_manager = GameManager(self.project.source_path)
            self.source_manager.load_all_platforms()

            self.project.roms_path.mkdir(parents=True, exist_ok=True)
            self.collection_manager = GameManager(self.project.roms_path)
            self.collection_manager.load_all_platforms()

            self.dual_panel.load_source(
                self.source_manager.get_all_games(),
                self.source_manager.get_platform_names(),
                lambda g: self.collection_manager.has_game(g)
            )
            self.dual_panel.load_collection(
                self.collection_manager.get_all_games(),
                self.collection_manager.get_platform_names()
            )

            self.status_label.setText(tr("status_project", name=self.project.name))
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("msg_init_failed", error=str(e)))

    # ─── 核心操作：复制 / 删除 ──────────────────────────

    def copy_games(self, games):
        if not games or not self.collection_manager:
            return
        count = 0
        self.dual_panel.stop_preview()
        for game in games:
            try:
                self.collection_manager.add_game(game)
                count += 1
            except Exception as e:
                QMessageBox.warning(self, tr("error"), f"复制失败: {game.game} - {e}")
        self.collection_manager.load_all_platforms()
        self.dual_panel.refresh_collection(
            self.collection_manager.get_all_games(),
            self.collection_manager.get_platform_names()
        )
        self.statusBar().showMessage(tr("copy_complete", count=count), 3000)

    def delete_games(self, games):
        if not games or not self.collection_manager:
            return
        names = "\n".join(f"  • {g.game} [{g.platform}]" for g in games)
        reply = QMessageBox.question(
            self, tr("confirm_delete_title"),
            tr("confirm_delete_msg", names=names),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        count = 0
        self.dual_panel.stop_preview()
        for game in games:
            try:
                self.collection_manager.remove_game(game)
                count += 1
            except Exception as e:
                QMessageBox.warning(self, tr("error"), f"删除失败: {game.game} - {e}")
        self.collection_manager.load_all_platforms()
        self.dual_panel.refresh_collection(
            self.collection_manager.get_all_games(),
            self.collection_manager.get_platform_names()
        )
        self.statusBar().showMessage(tr("delete_complete", count=count), 3000)

    # ─── 辅助功能 ──────────────────────────────────────

    def edit_metadata(self, game):
        if not game or not self.collection_manager:
            return
        platform = game.platform
        content = self.collection_manager.headers.get(platform, "")
        dialog = MetadataEditDialog(platform, content, self, editable=True)
        self._apply_dialog_theme(dialog)
        if dialog.exec_():
            self.collection_manager.headers[platform] = dialog.get_header()
            self.collection_manager.load_all_platforms()
            self.statusBar().showMessage(f"平台 {platform} 的配置已更新", 3000)

    def run_game(self, game):
        if not game or not self.collection_manager:
            return
        manager = self.collection_manager
        header = manager.headers.get(game.platform, "")
        fields = MetadataParser.parse_header_fields(header) if header else {}
        launch_tpl = (fields.get("launch", "") or "").strip()

        platform_path = game.platform_path or (manager.roms_root / game.platform)
        file_path = Path(platform_path) / game.file if platform_path else None
        if not file_path or not file_path.exists():
            QMessageBox.information(self, tr("info"), "未找到游戏文件，无法运行")
            return

        pegasus_dir = ""
        if getattr(self.project, "pegasus_path", None):
            pegasus_dir = str(Path(self.project.pegasus_path))
        elif Path(r"C:\\Workspaces\\games\\Pegasus G").exists():
            pegasus_dir = r"C:\\Workspaces\\games\\Pegasus G"

        replacements = {
            "{file}": str(file_path), "{file.path}": str(file_path),
            "{filepath}": str(file_path), "{rom}": str(file_path),
            "{rompath}": str(file_path.parent), "{dir}": str(file_path.parent),
            "{directory}": str(file_path.parent), "{platform}": game.platform,
            "{name}": game.game,
        }
        if "{env.appdir}" in launch_tpl:
            if not pegasus_dir:
                QMessageBox.information(self, tr("info"),
                    "检测到 {env.appdir} 占位符，请在项目设置中填写 Pegasus G 目录。")
                return
            replacements["{env.appdir}"] = pegasus_dir

        if launch_tpl:
            cmd = launch_tpl
            for k, v in replacements.items():
                cmd = cmd.replace(k, v)
            cmd = cmd.strip()
            if not cmd:
                QMessageBox.information(self, tr("info"), "launch 命令为空。")
                return
            tokens = shlex.split(cmd)
            first = tokens[0] if tokens else ""
            if first == "am":
                QMessageBox.information(self, tr("info"),
                    "检测到 launch 以 'am' 开头，请在设备端执行。")
                return
            if first and not Path(first).exists() and not shutil.which(first):
                QMessageBox.information(self, tr("info"),
                    f"未找到可执行命令: {first}")
                return
            reply = QMessageBox.question(self, tr("info"),
                f"即将执行:\n{cmd}\n\n工作目录：{file_path.parent}\n\n是否继续？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply != QMessageBox.Yes:
                return
            try:
                subprocess.Popen(cmd, shell=True, cwd=str(file_path.parent))
                self.statusBar().showMessage("正在运行游戏…", 2000)
            except Exception as e:
                QMessageBox.critical(self, tr("error"), f"运行失败: {e}")
            return

        QMessageBox.information(self, tr("info"),
            "未找到 Pegasus G 应用路径，且元数据中缺少 launch 配置。\n"
            "请在项目设置中填写 Pegasus G 目录，或在 metadata.pegasus.txt 中添加 launch 命令。")

    def batch_add_games(self):
        if not self.project or not self.source_manager:
            return
        text, ok = QInputDialog.getMultiLineText(
            self, tr("batch_add_input_title"), tr("batch_add_input_label"))
        if not ok or not text:
            return
        game_names = [name.strip() for name in text.split('\n') if name.strip()]
        if not game_names:
            return
        progress = QProgressDialog(tr("batch_add_searching"), tr("cancel"),
                                   0, len(game_names), self)
        self._apply_dialog_theme(progress)
        progress.setWindowTitle(tr("batch_add_progress_title"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        found = 0
        all_games = self.source_manager.get_all_games()
        for i, name in enumerate(game_names):
            progress.setValue(i)
            progress.setLabelText(tr("batch_add_searching_status",
                current=i+1, total=len(game_names), name=name))
            QApplication.processEvents()
            if progress.wasCanceled():
                break
            best = self._find_best_match(name, all_games)
            if best:
                try:
                    self.collection_manager.add_game(best)
                    found += 1
                except Exception:
                    pass
        progress.setValue(len(game_names))
        self.collection_manager.load_all_platforms()
        self.dual_panel.refresh_collection(
            self.collection_manager.get_all_games(),
            self.collection_manager.get_platform_names())
        QMessageBox.information(self, tr("info"),
            tr("batch_add_complete", total=len(game_names), found=found))

    def _find_best_match(self, search_name, games):
        import re
        from difflib import SequenceMatcher
        search_name = search_name.lower().strip()
        clean_search = re.sub(r'[^\w\s一-龥]', '', search_name)
        search_tokens = set(clean_search.split())
        best_game, best_score = None, 0
        for game in games:
            game_name = game.game.lower()
            if search_name == game_name:
                return game
            clean_game = re.sub(r'[^\w\s一-龥]', '', game_name)
            if clean_search == clean_game:
                return game
            score = 0
            if clean_search and clean_search in clean_game:
                score = 0.8
            game_tokens = set(clean_game.split())
            if search_tokens and search_tokens.issubset(game_tokens):
                score = max(score, 0.85)
            if score < 0.8:
                score = max(score, SequenceMatcher(None, clean_search, clean_game).ratio())
            if score > best_score:
                best_score, best_game = score, game
        return best_game if best_score > 0.6 else None

    def change_language(self, lang):
        if set_lang(lang):
            QMessageBox.information(self, tr("info"), "语言设置已更改，请重启程序以完全应用。")
            self.dual_panel.retranslate_ui()
            self.create_menu_bar()

    def set_theme(self, theme):
        theme = theme if theme in available_themes() else "light"
        self.current_theme = theme
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(theme))
        apply_titlebar_theme(self, theme)
        self.settings.setValue("theme", theme)
        self._update_theme_menu_checks()

    def apply_theme(self, theme):
        self.set_theme(theme)

    def _apply_dialog_theme(self, dialog):
        try:
            apply_titlebar_theme(dialog, getattr(self, "current_theme", "light"))
        except Exception:
            pass

    def _update_theme_menu_checks(self):
        if hasattr(self, "theme_actions"):
            for key, action in self.theme_actions.items():
                action.setChecked(key == self.current_theme)

    def add_to_recent_projects(self, filepath):
        recent = self.settings.value("recentProjects", [])
        if not isinstance(recent, list):
            recent = []
        path_str = str(filepath)
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        recent = recent[:10]
        self.settings.setValue("recentProjects", recent)
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self):
        self.recent_projects_menu.clear()
        recent = self.settings.value("recentProjects", [])
        if not isinstance(recent, list):
            recent = []
        if not recent:
            no_action = QAction("无最近项目", self)
            no_action.setEnabled(False)
            self.recent_projects_menu.addAction(no_action)
            return
        for path_str in recent:
            path = Path(path_str)
            action = QAction(path.name, self)
            action.setData(path_str)
            action.triggered.connect(lambda checked, p=path_str: self.open_project(p))
            self.recent_projects_menu.addAction(action)
        self.recent_projects_menu.addSeparator()
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(lambda: self.settings.setValue("recentProjects", []))
        self.recent_projects_menu.addAction(clear_action)

    def show_startup_dialog(self):
        recent = self.settings.value("recentProjects", [])
        if not isinstance(recent, list):
            recent = []
        dialog = StartupDialog(recent, self)
        self._apply_dialog_theme(dialog)
        if dialog.exec_():
            if dialog.action == 'new':
                self.new_project()
            elif dialog.action == 'open':
                self.open_project()
            elif dialog.action == 'recent' and dialog.selected_path:
                self.open_project(dialog.selected_path)

    def show_project_settings(self):
        if not self.project:
            QMessageBox.warning(self, tr("info"), tr("status_no_project"))
            return
        dialog = ProjectSettingsDialog(self.project, self)
        self._apply_dialog_theme(dialog)
        if dialog.exec_():
            self.init_managers()

    def extract_metadata_tool(self):
        default_source = ""
        if self.project and self.project.source_path:
            default_source = str(self.project.source_path)
        dialog = MetadataExtractDialog(default_source, self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()

    def merge_metadata_tool(self):
        default_target = ""
        if self.project and self.project.roms_path:
            default_target = str(self.project.roms_path)
        dialog = MetadataMergeDialog(default_target, self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()

    def show_about(self):
        dialog = AboutDialog(self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()
```

- [ ] **Step 2: 迁移保留的辅助方法**

将以下方法从原 `main_window.py` 迁移过来（不改逻辑，只复制代码）：
- `add_to_recent_projects()`
- `update_recent_projects_menu()`
- `clear_recent_projects()`
- `show_startup_dialog()`
- `show_project_settings()`
- `extract_metadata_tool()`
- `merge_metadata_tool()`
- `show_about()`

- [ ] **Step 3: 提交**

```bash
git add ui/main_window.py
git commit -m "refactor: rewrite MainWindow to use DualPanelLayout, remove view switching and task queue"
```

---

### Task 9: 清理废弃代码，更新导出和翻译

**Files:**
- Delete: `ui/log_window.py`
- Modify: `core/__init__.py`
- Modify: `ui/__init__.py`
- Modify: `core/i18n.py`

- [ ] **Step 1: 删除 LogWindow**

```bash
rm ui/log_window.py
```

- [ ] **Step 2: 更新 `core/__init__.py` 导出**

```python
"""
核心模块
"""
from core.project import Project
from core.metadata_parser import Game, MetadataParser
from core.game_manager import GameManager
```

移除 `TaskQueue, TaskType, TaskStatus, Task`。

- [ ] **Step 3: 更新 `ui/__init__.py` 导出**

```python
"""
UI 模块
"""
from ui.main_window import MainWindow
from ui.dual_panel_layout import DualPanelLayout
from ui.source_panel import SourcePanel
from ui.collection_panel import CollectionPanel
from ui.operate_bar import OperateBar
from ui.preview_panel import PreviewPanel
from ui.game_list_widget import GameListWidget
from ui.game_detail_widget import GameDetailWidget
```

移除 `LogWindow`。

- [ ] **Step 4: 更新 `core/i18n.py` 翻译字符串**

在 `_translations` 字典（zh 和 en）中添加新的翻译 key：

```python
# 新增的翻译 key
"source_title": ("来源 ROM", "Source ROMs"),
"collection_title": ("收藏 ROM", "Collection ROMs"),
"preview_panel": ("预览面板", "Preview Panel"),
"copy_complete": ("已复制 {count} 个游戏", "Copied {count} game(s)"),
"delete_complete": ("已删除 {count} 个游戏", "Deleted {count} game(s)"),
"confirm_delete_title": ("确认删除", "Confirm Delete"),
"confirm_delete_msg": ("确认删除以下游戏？ROM 文件和媒体资源将被永久删除。\n\n{names}", "Delete the following games? ROM files and media will be permanently deleted.\n\n{names}"),
"run_game": ("运行游戏", "Run Game"),
```

- [ ] **Step 5: 提交**

```bash
git rm ui/log_window.py
git add core/__init__.py ui/__init__.py core/i18n.py
git commit -m "refactor: remove LogWindow, update exports, add new i18n keys"
```

---

### Task 10: 集成测试与手动验证

- [ ] **Step 1: 启动应用，验证基本布局**

```bash
python main.py
```

验证点：
- [ ] 菜单栏 File/Tools/Settings/Help 正常显示
- [ ] 左侧来源面板出现（无项目时为空）
- [ ] 中间 OperateBar 两个按钮可见
- [ ] 右侧收藏面板出现
- [ ] 底部预览面板折叠状态

- [ ] **Step 2: 创建新项目，验证数据加载**

- 文件 → 新建项目 → 输入名称 → 选择来源目录 → 选择收藏目录
- 验证：来源面板正确显示 ROM 列表，平台过滤工作正常

- [ ] **Step 3: 验证复制操作**

- 在来源面板中选中游戏 → 点击 `→ 复制` 或按 F5
- 验证：游戏出现在右侧收藏面板，文件确实被复制到收藏目录

- [ ] **Step 4: 验证删除操作**

- 在收藏面板中选中游戏 → 点击 `← 删除` 或按 Del
- 验证：确认对话框弹出 → 确认后游戏从收藏面板消失，文件确实被删除

- [ ] **Step 5: 验证无限滚动**

- 加载 ≥ 300 个游戏的来源目录
- 向下滚动列表到底 → 验证自动加载下一批

- [ ] **Step 6: 验证预览面板**

- 单击某个游戏 → 验证底部预览面板展开，显示封面和信息
- 双击或按 Enter → 验证视频自动播放

- [ ] **Step 7: 验证主题和语言切换**

- 设置 → 主题 → 切换 4 个主题，验证 UI 正确响应
- 设置 → 语言 → 切换，验证文字更新

- [ ] **Step 8: 验证元数据编辑**

- 在收藏面板中选中游戏 → 点击预览面板的"编辑元数据"
- 验证 MetadataEditDialog 正确打开

- [ ] **Step 9: 提交最终验证结果**

```bash
git commit --allow-empty -m "test: manual verification - dual panel refactor complete"
```
