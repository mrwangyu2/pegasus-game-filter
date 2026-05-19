"""
收藏面板组件（右侧）
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QComboBox, QShortcut)
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

        title_label = QLabel("⭐ " + tr("collection_title"))
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

    def set_games(self, games):
        self.games = games
        self.game_list.set_games(games)

    def set_platforms(self, platforms):
        self.platform_combo.blockSignals(True)
        self.platform_combo.clear()
        self.platform_combo.addItem(tr("all_platforms"), "")
        max_text = tr("all_platforms")
        for p in sorted(platforms):
            self.platform_combo.addItem(p, p)
            if len(p) > len(max_text):
                max_text = p
        self.platform_combo.blockSignals(False)
        self._adjust_combo_width(max_text)

    def _adjust_combo_width(self, max_text: str):
        fm = self.platform_combo.fontMetrics()
        width = fm.horizontalAdvance(max_text + "     ") + 30
        width = max(width, 120)
        self.platform_combo.setMinimumWidth(width)
        try:
            view = self.platform_combo.view()
            view.setMinimumWidth(width + 20)
        except Exception:
            pass

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
        self.game_list.set_platform_filter(self.platform_combo.currentData() or "")
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
