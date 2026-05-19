"""
主窗口（双栏文件管理器重构版）
"""
from pathlib import Path
import subprocess
import shlex
import shutil
from PyQt5.QtWidgets import (QMainWindow, QWidget, QAction, QFileDialog,
                             QMessageBox, QInputDialog, QApplication,
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

        self.dual_panel = DualPanelLayout()
        self.dual_panel.copy_requested.connect(self.copy_games)
        self.dual_panel.delete_requested.connect(self.delete_games)
        self.dual_panel.edit_metadata_requested.connect(self.edit_metadata)
        self.dual_panel.run_game_requested.connect(self.run_game)
        self.setCentralWidget(self.dual_panel)

        self.apply_theme(self.current_theme)

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
        games = self.dual_panel.source_panel.get_selected_games()
        if games:
            self.copy_games(games)

    # ─── 项目管理 ───

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

    # ─── 核心操作：复制 / 删除 ───

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

    # ─── 辅助功能 ───

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

    # ─── 最近项目 ───

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

    # ─── 对话框 ───

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
