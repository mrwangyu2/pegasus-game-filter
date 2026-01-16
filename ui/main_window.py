"""
主窗口UI（重构版）
"""

from pathlib import Path
import subprocess
import shlex
import shutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSplitter, QPushButton, QLabel, QFileDialog,
                             QMessageBox, QInputDialog, QAction, QToolBar, QMenu,
                             QSizePolicy, QProgressDialog, QApplication)
from PyQt5.QtCore import Qt, QSettings, QTimer, QPoint
from PyQt5.QtGui import QIcon, QKeySequence
from core.project import Project
from core.game_manager import GameManager
from core.task_system import TaskType
from core.i18n import tr, set_lang, get_lang
from core.theme import build_stylesheet, available_themes, apply_titlebar_theme, load_icon
from core.metadata_parser import MetadataParser
from ui.game_list_widget import GameListWidget
from ui.game_detail_widget import GameDetailWidget
from ui.log_window import LogWindow
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
        self.project_manager = None
        self.current_view = "source"  # "source" or "project"
        
        # 初始化设置
        self.settings = QSettings("PegasusGameFilter", "App")
        self.current_theme = self.settings.value("theme", "dark")
        
        self.init_ui()
        self.setup_shortcuts()
        self.update_recent_projects_menu()
        
        # 启动时显示项目选择对话框
        QTimer.singleShot(100, self.show_startup_dialog)
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(tr("app_title"))
        # 确保图标路径正确且为绝对路径
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        self._update_view_label()
        
        # 主窗口布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 游戏列表
        self.game_list = GameListWidget()
        self.game_list.game_selected.connect(self.on_game_selected)
        self.game_list.game_activated.connect(self.on_game_activated)
        self.game_list.selection_changed.connect(self.on_selection_changed)
        self.game_list.platform_changed.connect(self._update_edit_metadata_btn_state)
        splitter.addWidget(self.game_list)
        
        # 游戏详情
        self.game_detail = GameDetailWidget()
        self.game_detail.game_updated.connect(self.on_game_updated)
        splitter.addWidget(self.game_detail)
        
        splitter.setSizes([450, 950])
        main_layout.addWidget(splitter)

        # 应用主题（初始）
        self.apply_theme(self.current_theme)
        
        # 状态栏
        self.status_label = QLabel(tr("status_no_project"))
        self.statusBar().addWidget(self.status_label)
        
        self.task_count_label = QLabel(tr("status_tasks", count=0))
        self.statusBar().addPermanentWidget(self.task_count_label)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        menubar.clear() # 确保在重新加载时清空
        
        # 文件菜单
        file_menu = menubar.addMenu(tr("menu_file"))
        
        new_action = QAction(tr("menu_new_project"), self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction(tr("menu_open_project"), self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        # 最近打开项目子菜单
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
        
        # 工具菜单
        tools_menu = menubar.addMenu(tr("menu_tools"))
        
        extract_action = QAction(tr("menu_extract_metadata"), self)
        extract_action.setShortcut(QKeySequence("Ctrl+Alt+E"))
        extract_action.triggered.connect(self.extract_metadata_tool)
        tools_menu.addAction(extract_action)

        merge_action = QAction(tr("menu_merge_metadata"), self)
        merge_action.setShortcut(QKeySequence("Ctrl+Alt+M"))
        merge_action.triggered.connect(self.merge_metadata_tool)
        tools_menu.addAction(merge_action)

        # 设置菜单 (包含语言和主题)
        settings_menu = menubar.addMenu(tr("menu_settings"))
        settings_menu.setTitle(f"{tr('menu_settings')} (&S)")
        
        # 语言子菜单
        lang_submenu = settings_menu.addMenu(tr("menu_language"))
        
        zh_action = QAction("简体中文", self)
        zh_action.setCheckable(True)
        zh_action.setShortcut(QKeySequence("Ctrl+Alt+L"))
        zh_action.setChecked(get_lang() == "zh")
        zh_action.triggered.connect(lambda: self.change_language("zh"))
        lang_submenu.addAction(zh_action)
        
        en_action = QAction("English", self)
        en_action.setCheckable(True)
        en_action.setShortcut(QKeySequence("Ctrl+Alt+G"))
        en_action.setChecked(get_lang() == "en")
        en_action.triggered.connect(lambda: self.change_language("en"))
        lang_submenu.addAction(en_action)

        # 主题子菜单
        self.theme_menu = settings_menu.addMenu(tr("menu_theme"))
        self.theme_actions = {}
        for idx, key in enumerate(available_themes(), start=1):
            action = QAction(tr(f"theme_{key}"), self)
            action.setCheckable(True)
            action.setShortcut(QKeySequence(f"Ctrl+Alt+{idx}"))
            action.triggered.connect(lambda checked, t=key: self.set_theme(t))
            self.theme_menu.addAction(action)
            self.theme_actions[key] = action
        self._update_theme_menu_checks()
        
        # 帮助菜单
        help_menu = menubar.addMenu(tr("menu_help"))
        
        about_action = QAction(tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def change_language(self, lang):
        """切换语言"""
        if set_lang(lang):
            QMessageBox.information(self, tr("info"), "语言设置已更改，请重启程序以完全应用。")
            # 也可以尝试立即更新部分UI
            self.retranslate_ui()

    def apply_theme(self, theme: str):
        """应用主题（用于初始化或切换）"""
        self.set_theme(theme)

    def set_theme(self, theme: str):
        """切换主题"""
        theme = theme if theme in available_themes() else "light"
        self.current_theme = theme
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(theme))
        apply_titlebar_theme(self, theme)
        self.settings.setValue("theme", theme)
        self._update_theme_menu_checks()

    def _apply_dialog_theme(self, dialog):
        """应用当前主题到对话框标题栏（仅 Windows 10+ 有效）"""
        if dialog is None:
            return
        try:
            apply_titlebar_theme(dialog, getattr(self, "current_theme", "light"))
        except Exception:
            # 如果窗口尚未初始化或平台不支持，忽略异常
            pass

    def _update_theme_menu_checks(self):
        if hasattr(self, "theme_actions"):
            for key, action in self.theme_actions.items():
                action.setChecked(key == self.current_theme)

    def show_theme_menu(self):
        """Alt+S 打开设置菜单 (包含主题)"""
        if not hasattr(self, "theme_menu"):
            return
        # 找到 theme_menu 的 parent (settings_menu)
        settings_menu = self.theme_menu.parentWidget()
        if not isinstance(settings_menu, QMenu):
            # 如果不是 QMenu，尝试直接弹出
            action = self.theme_menu.menuAction()
        else:
            action = settings_menu.menuAction()
            
        bar = self.menuBar()
        if action and bar:
            rect = bar.actionGeometry(action)
            pos = bar.mapToGlobal(rect.bottomLeft())
            if isinstance(settings_menu, QMenu):
                settings_menu.popup(pos)
                settings_menu.setFocus()
            else:
                self.theme_menu.popup(pos)
                self.theme_menu.setFocus()

    def retranslate_ui(self):
        """立即更新UI上的文字"""
        self.setWindowTitle(tr("app_title"))
        # 重新创建菜单
        self.create_menu_bar()
        # 更新工具栏
        self.switch_view_btn.setText(tr("switch_view"))
        self.select_all_btn.setText(tr("select_all"))
        self._update_execute_btn_label()
        self.clear_tasks_btn.setText(tr("clear_tasks"))
        self.batch_add_btn.setText(tr("batch_add"))
        self.edit_metadata_btn.setText(tr("edit_metadata"))
        self._update_view_label()
        # 更新状态栏
        if not self.project:
            self.status_label.setText(tr("status_no_project"))
        else:
            self.status_label.setText(tr("status_project", name=self.project.name))
        self.update_task_count()
        # 更新子组件
        if hasattr(self, 'game_list'):
            self.game_list.retranslate_ui()
        if hasattr(self, 'game_detail'):
            self.game_detail.retranslate_ui()
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        self.toolbar = toolbar
        
        # 视图标签 (靠左)
        self.view_label = QLabel()
        toolbar.addWidget(self.view_label)
        
        # 弹簧组件，将后面的按键推向右侧
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # 切换视图按钮
        self.switch_view_btn = QPushButton(tr("switch_view"))
        self.switch_view_btn.clicked.connect(self.switch_view)
        toolbar.addWidget(self.switch_view_btn)
        
        toolbar.addSeparator()

        # 全选按钮
        self.select_all_btn = QPushButton(tr("select_all"))
        self.select_all_btn.clicked.connect(self.select_all_games)
        self.select_all_btn.setVisible(False) # 初始隐藏
        toolbar.addWidget(self.select_all_btn)
        
        # 复制/删除选择按钮（随视图变化）
        self.execute_btn = QPushButton()
        self.execute_btn.clicked.connect(self.on_execute_action)
        self.execute_btn.setEnabled(False)
        self.execute_btn.setStyleSheet("font-weight: bold; color: red;")
        self._update_execute_btn_label()
        toolbar.addWidget(self.execute_btn)
        
        # 清空任务按钮
        self.clear_tasks_btn = QPushButton(tr("clear_tasks"))
        self.clear_tasks_btn.clicked.connect(self.clear_tasks)
        self.clear_tasks_btn.setEnabled(False)
        toolbar.addWidget(self.clear_tasks_btn)
        
        toolbar.addSeparator()
        
        # 批量添加按钮（来源视图专用）
        self.batch_add_btn = QPushButton(tr("batch_add"))
        self.batch_add_btn.clicked.connect(self.batch_add_games)
        self.batch_add_btn.setEnabled(False)
        self.batch_add_action = toolbar.addWidget(self.batch_add_btn)

        # 编辑/查阅元数据按钮
        self.edit_metadata_btn = QPushButton(f"{tr('edit_metadata')} (Ctrl+E)")
        self.edit_metadata_btn.clicked.connect(self.edit_metadata)
        self.edit_metadata_btn.setShortcut(QKeySequence("Ctrl+E"))
        self.edit_metadata_btn.setEnabled(False)
        self.edit_metadata_action = toolbar.addWidget(self.edit_metadata_btn)

        # 运行游戏按钮
        self.run_game_btn = QPushButton("运行游戏 (Ctrl+R)")
        self.run_game_btn.clicked.connect(self.run_selected_game)
        self.run_game_btn.setEnabled(False)
        toolbar.addWidget(self.run_game_btn)
    
    def setup_shortcuts(self):
        """设置快捷键"""
        from PyQt5.QtWidgets import QShortcut
        
        # Tab - 切换视图
        QShortcut(QKeySequence(Qt.Key_Tab), self, self.switch_view)
        
        # F5 - 复制/删除选择
        QShortcut(QKeySequence(Qt.Key_F5), self, self.on_execute_action)
        
        # Ctrl+B - 批量添加
        QShortcut(QKeySequence("Ctrl+B"), self, self.batch_add_games)

        # Ctrl+Shift+C - 清空任务
        QShortcut(QKeySequence("Ctrl+Shift+C"), self, self.clear_tasks)

        # Ctrl+E - 编辑/查阅元数据
        QShortcut(QKeySequence("Ctrl+E"), self, self.edit_metadata)
        # Ctrl+Shift+E - 另一快捷键打开编辑/查阅
        QShortcut(QKeySequence("Ctrl+Shift+E"), self, self.edit_metadata)

        # Alt+S - 打开设置菜单
        QShortcut(QKeySequence("Alt+S"), self, self.show_theme_menu)

        # Ctrl+R - 运行游戏
        # 使用 QAction 绑定到主窗口，这是最可靠的快捷键实现方式
        self.run_action = QAction(self)
        self.run_action.setShortcut(QKeySequence("Ctrl+R"))
        # WindowShortcut 确保在窗口激活时有效，ApplicationShortcut 范围更广
        self.run_action.setShortcutContext(Qt.ApplicationShortcut)
        self.run_action.triggered.connect(self.run_selected_game)
        self.addAction(self.run_action)
    
    def new_project(self):
        """创建新项目"""
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
        
        # 保存项目
        save_path, _ = QFileDialog.getSaveFileName(
            self, tr("dialog_save_project"), f"{name}.json", "JSON Files (*.json)"
        )
        if save_path:
            save_path = Path(save_path)
            self.project.save(save_path)
            self.add_to_recent_projects(save_path)
        
        self.init_managers()
        self.update_ui_state()
    
    def open_project(self, filepath=None):
        """打开项目"""
        if not filepath:
            filepath, _ = QFileDialog.getOpenFileName(
                self, tr("menu_open_project"), "", "JSON Files (*.json)"
            )
        
        if not filepath:
            return
        
        filepath = Path(filepath)
        self.project = Project.load(filepath)
        if not self.project:
            QMessageBox.warning(self, tr("error"), tr("msg_load_failed"))
            return
        
        self.add_to_recent_projects(filepath)
        self.init_managers()
        self.update_ui_state()

    def add_to_recent_projects(self, filepath):
        """将项目路径添加到最近打开列表"""
        recent = self.settings.value("recentProjects", [])
        if not isinstance(recent, list):
            recent = []
        
        path_str = str(filepath)
        if path_str in recent:
            recent.remove(path_str)
        recent.insert(0, path_str)
        recent = recent[:10]  # 只保留最近10个
        
        self.settings.setValue("recentProjects", recent)
        self.update_recent_projects_menu()

    def update_recent_projects_menu(self):
        """更新最近打开项目菜单"""
        self.recent_projects_menu.clear()
        recent = self.settings.value("recentProjects", [])
        if not isinstance(recent, list):
            recent = []
        
        if not recent:
            no_recent_action = QAction("无最近项目", self)
            no_recent_action.setEnabled(False)
            self.recent_projects_menu.addAction(no_recent_action)
            return
        
        for path_str in recent:
            path = Path(path_str)
            action = QAction(path.name, self)
            action.setData(path_str)
            action.triggered.connect(lambda checked, p=path_str: self.open_project(p))
            self.recent_projects_menu.addAction(action)
        
        self.recent_projects_menu.addSeparator()
        clear_action = QAction("清空列表", self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_projects_menu.addAction(clear_action)

    def clear_recent_projects(self):
        """清空最近项目列表"""
        self.settings.setValue("recentProjects", [])
        self.update_recent_projects_menu()

    def extract_metadata_tool(self):
        """打开元数据提取工具"""
        default_source = ""
        if self.project and self.project.source_path:
            default_source = str(self.project.source_path)
        
        dialog = MetadataExtractDialog(default_source, self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()

    def merge_metadata_tool(self):
        """打开元数据整合工具"""
        default_target = ""
        if self.project and self.project.roms_path:
            default_target = str(self.project.roms_path)
        
        dialog = MetadataMergeDialog(default_target, self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()
    
    def show_startup_dialog(self):
        """显示启动项目选择对话框"""
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
    
    def save_project(self):
        """保存项目"""
        if not self.project or not self.project.project_file:
            QMessageBox.warning(self, tr("info"), tr("status_no_project"))
            return
        
        self.project.save(self.project.project_file)
        self.statusBar().showMessage(tr("project_saved"), 2000)
    
    def show_project_settings(self):
        """显示项目设置"""
        if not self.project:
            QMessageBox.warning(self, tr("info"), tr("status_no_project"))
            return
        
        dialog = ProjectSettingsDialog(self.project, self)
        self._apply_dialog_theme(dialog)
        if dialog.exec_():
            # 重新初始化管理器
            self.init_managers()
            self.update_ui_state()
    
    def init_managers(self):
        """初始化游戏管理器"""
        try:
            # 加载来源目录游戏
            self.source_manager = GameManager(self.project.source_path)
            self.source_manager.load_all_platforms()
            
            # 加载项目游戏
            self.project.roms_path.mkdir(parents=True, exist_ok=True)
            self.project_manager = GameManager(self.project.roms_path)
            self.project_manager.load_all_platforms()
            
            # 显示来源目录游戏
            self.current_view = "source"
            self.game_list.set_games(self.source_manager.get_all_games())
            self.game_list.set_platforms(self.source_manager.get_platform_names())
            self.game_list.set_task_queue(self.project_manager.task_queue)
            self.game_list.set_duplicate_checker(lambda g: self.project_manager.has_game(g) if self.project_manager else False)
            
        except Exception as e:
            QMessageBox.critical(self, tr("error"), tr("msg_init_failed", error=str(e)))
    
    def update_ui_state(self):
        """更新UI状态"""
        has_project = self.project is not None
        is_source_view = self.current_view == "source"
        is_project_view = self.current_view == "project"
        
        self.switch_view_btn.setEnabled(has_project)
        # 批量添加按钮：仅来源视图存在
        if hasattr(self, "batch_add_action") and hasattr(self, "toolbar"):
            if has_project and is_source_view:
                if self.batch_add_action not in self.toolbar.actions():
                    # 插入到元数据按钮之前，保持原有顺序
                    self.toolbar.insertAction(getattr(self, "edit_metadata_action", None), self.batch_add_action)
                self.batch_add_btn.setEnabled(True)
            else:
                if self.batch_add_action in self.toolbar.actions():
                    self.toolbar.removeAction(self.batch_add_action)
        # 全选按钮：仅在项目视图显示
        self.select_all_btn.setVisible(has_project and is_project_view)
        self.select_all_btn.setEnabled(has_project and is_project_view)

        # 编辑/查阅元数据按钮：有项目就显示，具体状态由下方函数控制
        self.edit_metadata_btn.setVisible(has_project)
        self._update_edit_metadata_btn_state()

        # 运行按钮：有项目且有选中游戏时可用
        self._update_run_btn_state()
        
        if has_project:
            self.status_label.setText(tr("status_project", name=self.project.name))
            self.update_task_count()
        else:
            self.status_label.setText(tr("status_no_project"))
        self._update_execute_btn_label()
        self._update_view_label()
    
    def _update_execute_btn_label(self):
        """根据视图更新按钮文案"""
        if self.current_view == "project":
            self.execute_btn.setText(tr("delete_selection"))
        else:
            self.execute_btn.setText(tr("copy_selection"))
    
    def on_execute_action(self):
        """根据当前视图执行复制或删除"""
        if self.current_view == "project":
            self.delete_selected_games()
        else:
            self.copy_selected_games()
    
    def _update_view_label(self):
        """更新视图标签样式"""
        label_text = tr("view_label")
        if self.current_view == "source":
            self.view_label.setText(f"  {label_text} <span style='color: #2196F3; font-weight: bold;'>{tr('view_source')}</span>  ")
        else:
            self.view_label.setText(f"  {label_text} <span style='color: #4CAF50; font-weight: bold;'>{tr('view_project')}</span>  ")

    def _update_edit_metadata_btn_state(self):
        """更新编辑/查阅元数据按钮状态
        来源视图：始终显示为查阅模式，可点击；未选平台时在点击时提示
        收藏视图：显示为编辑模式，可点击；未选平台时在点击时提示
        """
        has_project = bool(self.project)
        is_project_view = self.current_view == "project"

        self.edit_metadata_btn.setVisible(has_project)
        if not has_project:
            self.edit_metadata_btn.setEnabled(False)
            return

        label = tr("edit_metadata") if is_project_view else tr("view_metadata")
        self.edit_metadata_btn.setText(f"{label} (Ctrl+E)")
        # 保持可点击以便在“全部平台”状态下提示选择具体平台
        self.edit_metadata_btn.setEnabled(True)

    def edit_metadata(self):
        """编辑/查阅当前平台的元数据（来源视图查看完整文件，项目视图编辑 Header）"""
        if not self.project:
            return
        if not self.project_manager or not self.source_manager:
            return
            
        platform = self.game_list.get_current_platform()
        if not platform:
            QMessageBox.information(self, tr("info"), "请选择具体平台后再查看元数据")
            return
            
        editable = self.current_view == "project"
        if editable:
            content = self.project_manager.headers.get(platform, "")
        else:
            if not self.project.source_path:
                QMessageBox.warning(self, tr("error"), "未配置来源目录，无法读取元数据")
                return
            metadata_path = Path(self.project.source_path) / platform / "metadata.pegasus.txt"
            if not metadata_path.exists():
                QMessageBox.warning(self, tr("error"), f"来源目录下未找到 {platform}/metadata.pegasus.txt")
                return
            try:
                content = metadata_path.read_text(encoding="utf-8")
            except Exception as e:
                QMessageBox.warning(self, tr("error"), f"读取 metadata.pegasus.txt 失败: {e}")
                return
        
        dialog = MetadataEditDialog(platform, content, self, editable=editable)
        self._apply_dialog_theme(dialog)
        if dialog.exec_():
            if not editable:
                return  # 查看模式直接关闭
            new_header = dialog.get_header()
            self.project_manager.headers[platform] = new_header
            
            # 添加一个更新任务到队列
            from core.metadata_parser import Game
            fake_game = Game()
            fake_game.game = f"Platform Config ({platform})"
            fake_game.platform = platform
            self.project_manager.task_queue.add_task(TaskType.UPDATE, fake_game)
            self.update_task_count()
            
            self.statusBar().showMessage(f"平台 {platform} 的配置已更新，请点击执行以保存到文件", 3000)

    def switch_view(self):
        """切换视图"""
        if not self.project:
            return
        
        if self.current_view == "source":
            self.current_view = "project"
            # 切到项目视图时重新扫描项目Roms目录，确保已有游戏被加载
            try:
                self.project_manager.load_all_platforms()
            except Exception as e:
                QMessageBox.warning(self, "提示", f"加载收藏目录失败: {e}")
            self.game_list.set_games(self.project_manager.get_all_games())
            self.game_list.set_platforms(self.project_manager.get_platform_names())
            self.game_list.set_duplicate_checker(None)
            self.game_detail.set_editable(True)
        else:
            self.current_view = "source"
            # 返回来源视图时同步刷新来源目录
            try:
                self.source_manager.load_all_platforms()
            except Exception as e:
                QMessageBox.warning(self, "提示", f"加载来源目录失败: {e}")
            self.game_list.set_games(self.source_manager.get_all_games())
            self.game_list.set_platforms(self.source_manager.get_platform_names())
            self.game_list.set_duplicate_checker(lambda g: self.project_manager.has_game(g) if self.project_manager else False)
            self.game_detail.set_editable(False)
        
        self.update_ui_state()
        
        # 清理当前展示内容与选择
        self.game_list.clear_selection()
        self.game_detail.clear()
        # 删除按钮仅在项目视图可用，由选中控制
        self.execute_btn.setEnabled(False)
        self.update_task_count()
    
    def on_game_selected(self, game):
        """游戏选中事件（单击或上下键）"""
        # 仅显示封面和信息，不播放视频
        self.game_detail.set_game(game, auto_play=False)
        self._update_run_btn_state()

    def on_game_activated(self, game):
        """游戏激活事件（回车或双击）"""
        # 显式播放视频
        self.game_detail.set_game(game, auto_play=True)
    
    def on_selection_changed(self, selected_games):
        """选择改变事件"""
        has_selection = len(selected_games) > 0
        # 如果有选中的项，优先根据选中状态启用按钮
        if has_selection:
            self.execute_btn.setEnabled(True)
        else:
            # 如果没有选中的项，则根据任务队列是否有任务来决定是否启用“复制选择”
            if self.project_manager:
                count = self.project_manager.task_queue.get_task_count()
                total = sum(count.values())
                if self.current_view == "source" and total > 0:
                    self.execute_btn.setEnabled(True)
                else:
                    self.execute_btn.setEnabled(False)
        
        # 实时更新任务计数显示
        self.update_task_count()
        self._update_run_btn_state()
    
    def _update_run_btn_state(self):
        has_project = bool(self.project)
        has_game = bool(self.game_list.get_current_game()) if hasattr(self, "game_list") else False
        if hasattr(self, "run_game_btn"):
            self.run_game_btn.setEnabled(has_project and has_game)
    
    def _get_launch_command(self, game, manager):
        header = manager.headers.get(game.platform, "") if manager and hasattr(manager, "headers") else ""
        if not header:
            return ""
        fields = MetadataParser.parse_header_fields(header)
        return (fields.get("launch", "") or "").strip()

    def run_selected_game(self):
        """运行当前选中的游戏"""
        if not self.project:
            QMessageBox.information(self, tr("info"), "请先打开或创建项目")
            return

        game = self.game_list.get_current_game()
        if not game:
            QMessageBox.information(self, tr("info"), "请先选中一款游戏")
            return

        manager = self.project_manager if self.current_view == "project" else self.source_manager
        if not manager:
            QMessageBox.warning(self, tr("warning"), "未找到游戏管理器，无法运行")
            return

        # 解析 launch 模板
        launch_tpl = self._get_launch_command(game, manager)

        # 游戏文件路径
        platform_path = game.platform_path or (manager.roms_root / game.platform)
        file_path = Path(platform_path) / game.file if platform_path else None
        if not file_path or not file_path.exists():
            QMessageBox.information(self, tr("info"), "未找到游戏文件，无法运行")
            return

        # Pegasus 应用目录，用于替换 {env.appdir}
        pegasus_dir = ""
        if getattr(self.project, "pegasus_path", None):
            pegasus_dir = str(Path(self.project.pegasus_path))
        elif Path(r"C:\\Workspaces\\games\\Pegasus G").exists():
            pegasus_dir = r"C:\\Workspaces\\games\\Pegasus G"

        # 替换占位符
        replacements = {
            "{file}": str(file_path),
            "{file.path}": str(file_path),
            "{filepath}": str(file_path),
            "{rom}": str(file_path),
            "{rompath}": str(file_path.parent),
            "{dir}": str(file_path.parent),
            "{directory}": str(file_path.parent),
            "{platform}": game.platform,
            "{name}": game.game,
        }
        if "{env.appdir}" in (launch_tpl or ""):
            if not pegasus_dir:
                QMessageBox.information(
                    self,
                    tr("info"),
                    "检测到 {env.appdir} 占位符，请在项目设置填写 Pegasus G 目录用于替换。"
                )
                return
            replacements["{env.appdir}"] = pegasus_dir

        if launch_tpl:
            cmd = launch_tpl
            for k, v in replacements.items():
                cmd = cmd.replace(k, v)

            # 基本可执行检测，避免 cmd 提示“不是内部或外部命令”
            cmd_stripped = cmd.strip()
            if not cmd_stripped:
                QMessageBox.information(self, tr("info"), "launch 命令为空，请检查 metadata.pegasus.txt")
                return
            tokens = shlex.split(cmd_stripped)
            first = tokens[0] if tokens else ""
            # 常见 Android am 启动提示
            if first == "am":
                QMessageBox.information(
                    self,
                    tr("info"),
                    "检测到 launch 以 'am' 开头，需要在设备端执行。\n"
                    "请改为 'adb shell am start ...' 或在 Pegasus G 中配置正确命令。"
                )
                return
            if first and not Path(first).exists() and not shutil.which(first):
                QMessageBox.information(
                    self,
                    tr("info"),
                    f"未找到可执行命令: {first}\n请确认 launch 配置或将命令加入系统 PATH。"
                )
                return

            # 改为 Yes/No 确认弹窗
            reply = QMessageBox.question(
                self,
                tr("info"),
                f"即将执行:\n{cmd_stripped}\n\n工作目录：{file_path.parent}\n\n是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return

            try:
                subprocess.Popen(cmd_stripped, shell=True, cwd=str(file_path.parent))
                self.statusBar().showMessage("正在运行游戏…", 2000)
            except Exception as e:
                QMessageBox.critical(self, tr("error"), f"运行失败: {e}")
            return

        # 无 launch 配置，尝试启动 Pegasus G 应用或提示
        pegasus_exe = None
        if getattr(self.project, "pegasus_path", None):
            candidate = Path(self.project.pegasus_path) / "Pegasus.exe"
            if candidate.exists():
                pegasus_exe = candidate
        default_candidate = Path(r"C:\\Workspaces\\games\\Pegasus G\\Pegasus.exe")
        if not pegasus_exe and default_candidate.exists():
            pegasus_exe = default_candidate

        if pegasus_exe:
            # 提示即将执行的 Pegasus 前端（改为 Yes/No）
            reply = QMessageBox.question(
                self,
                tr("info"),
                f"即将启动：{pegasus_exe}\n\n工作目录：{pegasus_exe.parent}\n\n是否继续？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply != QMessageBox.Yes:
                return
            try:
                subprocess.Popen([str(pegasus_exe)], cwd=str(pegasus_exe.parent))
                QMessageBox.information(self, tr("info"), "已启动 Pegasus G，请在前端中选择游戏运行。")
                return
            except Exception as e:
                QMessageBox.critical(self, tr("error"), f"启动 Pegasus G 失败: {e}")
                return

        QMessageBox.information(
            self,
            tr("info"),
            "未找到 Pegasus G 应用路径，且元数据中缺少 launch 配置。\n"
            "请在项目设置中填写 Pegasus G 目录，或在 metadata.pegasus.txt 的 Header 中添加 launch 命令（例如 launch: cmd /c \"emu.exe {file}\"）。"
        )
    
    def on_game_updated(self, game):
        """游戏更新事件"""
        if self.current_view == "project":
            self.project_manager.task_queue.add_task(TaskType.UPDATE, game)
            self.update_task_count()
    
    def add_to_task_queue(self):
        """添加到任务队列"""
        if not self.project_manager:
            return
        
        selected_games = self.game_list.get_selected_games()
        if not selected_games:
            return
        
        for game in selected_games:
            if self.current_view == "source":
                self.source_manager.task_queue.add_task(TaskType.ADD, game)
                self.project_manager.task_queue.add_task(TaskType.ADD, game)
            else:
                # 项目视图下不能添加
                pass
        
        self.update_task_count()
        self.statusBar().showMessage(f"已添加 {len(selected_games)} 个游戏到任务队列", 2000)
    
    def copy_selected_games(self):
        """复制选中游戏（来源视图 -> 项目）"""
        if not self.project_manager or self.current_view != "source":
            return
        
        # 首先检查任务队列是否已经有批量添加的任务
        if self.project_manager.task_queue.has_pending_tasks():
            self.execute_tasks()
            return

        selected_games = self.game_list.get_selected_games()
        if not selected_games:
            return
        
        for game in selected_games:
            self.project_manager.task_queue.add_task(TaskType.ADD, game)
        
        # 直接执行复制任务
        self.execute_tasks()
    
    def delete_selected_games(self):
        """删除选中游戏（项目视图）"""
        if not self.project_manager or self.current_view != "project":
            return
        
        selected_games = self.game_list.get_selected_games()
        if not selected_games:
            return
        
        for game in selected_games:
            self.project_manager.task_queue.add_task(TaskType.REMOVE, game)
        
        # 直接执行任务
        self.execute_tasks()
    
    def execute_tasks(self):
        """执行任务"""
        if not self.project_manager:
            return
        
        if not self.project_manager.task_queue.has_pending_tasks():
            QMessageBox.information(self, tr("info"), tr("msg_no_pending_tasks"))
            return
        
        # 1. 停止自动播放计时器，防止在执行期间后台触发播放导致文件锁定
        self.game_list.autoplay_timer.stop()
        
        # 2. 释放播放器当前占用的文件
        self.game_detail.stop_video()
        
        # 3. 显示确认对话框
        task_count = self.project_manager.task_queue.get_task_count()
        msg = tr("confirm_exec_msg", 
                 add=task_count[TaskType.ADD], 
                 remove=task_count[TaskType.REMOVE], 
                 update=task_count[TaskType.UPDATE])
        
        reply = QMessageBox.question(self, tr("confirm_exec_title"), msg,
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 显示日志窗口
            log_window = LogWindow(self)
            self._apply_dialog_theme(log_window)
            if self.current_view == "source":
                log_window.set_close_text(tr("btn_close"))
            log_window.start_execution(self.project_manager)
            log_window.exec_()
            
            # 刷新显示
            self.project_manager.load_all_platforms()
            if self.current_view == "project":
                self.game_list.set_games(self.project_manager.get_all_games())
                self.game_list.set_platforms(self.project_manager.get_platform_names())
            
            self.game_list.clear_selection()
            self.update_task_count()
            self.execute_btn.setEnabled(False)
    
    def clear_tasks(self):
        """清空任务"""
        if self.project_manager:
            self.project_manager.task_queue.clear()
            # 清除列表的选择状态（取消黄色背景和勾选）
            self.game_list.clear_selection()
            self.update_task_count()
            self.statusBar().showMessage(tr("tasks_cleared"), 2000)
    
    def update_task_count(self):
        """更新任务计数"""
        if self.project_manager:
            count = self.project_manager.task_queue.get_task_count()
            total = sum(count.values())
            self.task_count_label.setText(tr("status_tasks", count=total))
            
            has_tasks = total > 0
            # 清空按钮随任务可用
            self.clear_tasks_btn.setEnabled(has_tasks)
            # 如果有任务且在来源视图，启用“复制选择”按钮
            if self.current_view == "source" and has_tasks:
                self.execute_btn.setEnabled(True)
    
    def batch_add_games(self):
        """批量添加游戏"""
        if not self.project:
            return
        if self.current_view != "source":
            return
        
        text, ok = QInputDialog.getMultiLineText(
            self, tr("batch_add_input_title"), tr("batch_add_input_label")
        )
        
        if not ok or not text:
            return
        
        game_names = [name.strip() for name in text.split('\n') if name.strip()]
        total_to_search = len(game_names)
        if total_to_search == 0:
            return
# ... (rest of search)
        # 创建并显示进度对话框
        progress = QProgressDialog(tr("batch_add_searching"), tr("cancel"), 0, total_to_search, self)
        self._apply_dialog_theme(progress)
        progress.setWindowTitle(tr("batch_add_progress_title"))
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        
        found = 0
        all_games = self.source_manager.get_all_games()
        
        for i, name in enumerate(game_names):
            # 更新进度条
            progress.setValue(i)
            progress.setLabelText(tr("batch_add_searching_status", current=i+1, total=total_to_search, name=name))
            QApplication.processEvents()
            
            if progress.wasCanceled():
                break
                
            best_match = self._find_best_match(name, all_games)
            if best_match:
                self.project_manager.task_queue.add_task(TaskType.ADD, best_match)
                found += 1
        
        progress.setValue(total_to_search)
        self.update_task_count()

        info_box = QMessageBox(self)
        info_box.setIcon(QMessageBox.Information)
        info_box.setWindowTitle(tr("info"))
        info_box.setText(tr("batch_add_complete", total=len(game_names), found=found))
        self._apply_dialog_theme(info_box)
        info_box.exec_()

    def _find_best_match(self, search_name, games):
        """智能模糊匹配逻辑"""
        import re
        from difflib import SequenceMatcher
        
        search_name = search_name.lower().strip()
        # 清理搜索名：移除标点符号
        clean_search = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', search_name)
        search_tokens = set(clean_search.split())
        
        best_game = None
        best_score = 0
        
        for game in games:
            game_name = game.game.lower()
            # 1. 完全一致
            if search_name == game_name:
                return game
                
            # 2. 清理后的完全一致
            clean_game = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', game_name)
            if clean_search == clean_game:
                return game
            
            score = 0
            # 3. 包含关系 (基础分)
            if clean_search and clean_search in clean_game:
                score = 0.8
            
            # 4. 单词覆盖率 (处理词序不同)
            game_tokens = set(clean_game.split())
            if search_tokens and search_tokens.issubset(game_tokens):
                score = max(score, 0.85)
            
            # 5. 模糊相似度 (difflib)
            # 只有当基础分不够高时才尝试计算，以保证效率
            if score < 0.8:
                similarity = SequenceMatcher(None, clean_search, clean_game).ratio()
                score = max(score, similarity)
            
            if score > best_score:
                best_score = score
                best_game = game
                
        # 相似度阈值设为 0.6，防止乱匹配
        return best_game if best_score > 0.6 else None
    
    def select_all_games(self):
        """全选当前视图的游戏"""
        self.game_list.select_all()
    
    def clear_selection(self):
        """清空选择"""
        self.game_list.clear_selection()
    
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        self._apply_dialog_theme(dialog)
        dialog.exec_()
