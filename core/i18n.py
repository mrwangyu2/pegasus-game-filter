
import json
from PyQt5.QtCore import QSettings

class Translator:
    _instance = None
    
    # 语言定义
    LANG_ZH = "zh"
    LANG_EN = "en"
    
    # 翻译字典
    TRANSLATIONS = {
        LANG_ZH: {
            "app_title": "天马G游戏筛选器 v1.0",
            "menu_file": "文件(&F)",
            "menu_new_project": "新建项目(&N)",
            "menu_open_project": "打开项目(&O)",
            "menu_recent_projects": "最近打开项目",
            "menu_save_project": "保存项目(&S)",
            "menu_project_settings": "项目设置(&P)",
            "menu_exit": "退出(&X)",
            "menu_help": "帮助(&H)",
            "menu_about": "关于(&A)",
            "menu_language": "语言",
            "menu_tools": "工具(&T)",
            "menu_settings": "设置(&S)",
            "menu_theme": "主题",

            "theme_light": "明亮",

            "theme_dark": "暗黑",
            "theme_blue": "深蓝",
            "theme_sepia": "柔和米色",

            "menu_extract_metadata": "提取元数据(&E)",
            "menu_merge_metadata": "整合元数据(&M)",




            "switch_view": "切换视图 (Tab)",
            "delete_selection": "删除选择 (F5)",
            "copy_selection": "复制选择 (F5)",

            "clear_tasks": "清空任务 (Ctrl+Shift+C)",
            "batch_add": "批量添加 (Ctrl+B)",
            "edit_metadata": "编辑元数据 (Ctrl+E)",
            "view_metadata": "查阅元数据",



            "select_all": "全选",

            "status_no_project": "请创建或打开项目",
            "status_tasks": "任务: {count}",
            "status_project": "项目: {name}",
            "view_label": "当前视图: ",
            "view_source": "来源目录",
            "view_project": "收藏目录",

            "hint_label": "<b>导航</b> <span style='color: #2196F3;'>↑↓</span> 浏览 · <span style='color: #2196F3;'>Alt+↑↓</span> 平台 · <span style='color: #2196F3;'>PgUp/Dn</span> 翻页<br><b>检索</b> <span style='color: #4CAF50;'>Ctrl+F</span> 搜索 · <span style='color: #4CAF50;'>Ctrl+P</span> 平台 · <span style='color: #4CAF50;'>Ctrl+L</span> 列表<br><b>操作</b> <span style='color: #F44336;'>Space</span> 选择 · <span style='color: #F44336;'>Enter</span> 播放 · <span style='color: #F44336;'>Ctrl+B</span> 批量 · <span style='color: #F44336;'>Ctrl+E</span> 编辑",




            "search_label": "搜索:",
            "platform_label": "平台:",
            "all_platforms": "全部平台",
            "search_placeholder": "输入游戏名称、平台或开发者...",
            "game_count_label": "游戏数量: {total} | 已选择: {selected}",
            "pagination_label": "分页: {current}/{total_pages} | 显示 {start}-{end} / {total}",
            "prev_page": "上一页",
            "next_page": "下一页",
            "confirm_exec_title": "确认执行",
            "confirm_exec_msg": "即将执行以下任务:\n\n添加: {add} 个\n删除: {remove} 个\n更新: {update} 个\n\n确定要执行吗?",
            "project_saved": "项目已保存",
            "error": "错误",
            "info": "提示",
            "batch_add_complete": "输入 {total} 个，成功匹配并添加 {found} 个游戏到任务队列",
            "welcome_title": "欢迎使用天马G游戏筛选器",
            "welcome_desc": "快速筛选、管理您的天马G游戏库",
            "recent_projects": "最近打开项目:",
            "no_recent_projects": "无最近打开项目",
            "btn_new_project": "新建项目",
            "btn_open_project": "打开已有项目",
            "dialog_new_project": "新建项目",
            "dialog_project_name": "项目名称:",
            "dialog_select_source": "选择来源ROM根目录",
            "dialog_select_project": "选择收藏目录",
            "dialog_save_project": "保存项目文件",

            "msg_load_failed": "加载项目失败",
            "msg_init_failed": "初始化失败: {error}",
            "msg_no_pending_tasks": "没有待执行的任务",
            "batch_add_input_title": "批量添加",
            "batch_add_input_label": "请输入游戏名称列表(每行一个):",
            "batch_add_progress_title": "批量搜索进度",
            "batch_add_searching": "正在搜索匹配游戏...",
            "batch_add_searching_status": "正在搜索 ({current}/{total}): {name}",
            "cancel": "取消",
            "duplicate_warning": "收藏目录已存在同名游戏，无法选择。",
            "task_added": "已添加 {count} 个游戏到任务队列",

            "tasks_cleared": "任务队列已清空",
            "loading_games": "正在加载游戏...",
            "refreshing_platforms": "正在刷新平台列表...",
            "filtering": "正在筛选...",
            "please_wait": "请稍候",
            "media_preview": "媒体预览",
            "base_info_label": "基本信息",
            "title_label": "标题:",
            "sort_by_label": "排序(sort-by):",
            "platform_label_detail": "平台:",
            "developer_label": "开发商:",
            "description_label": "描述",
            "file_info_label": "文件信息",
            "rom_file_label": "ROM文件:",
            "dir_label": "目录:",
            "btn_save_changes": "保存修改",
            "no_cover": "无封面",
            "no_game": "无游戏",
            "menu_settings": "设置",
            "btn_browse": "浏览...",
            "btn_save": "保存",
            "btn_cancel": "取消",
            "btn_close": "关闭",
            "msg_enter_name": "请输入项目名称",

            "msg_select_roms": "请选择收藏目录",
            "msg_select_source": "请选择来源ROM目录",
            "msg_save_success": "项目设置已保存",

            "msg_save_failed": "保存项目失败",
            "log_title": "任务执行详情",
            "log_starting": "正在开始任务执行...",
            "log_finished": "任务执行完成",
            "log_failed": "任务执行失败: {error}",
            "warning": "警告",
            "success": "成功"
        },
        LANG_EN: {
            "app_title": "Pegasus Game Filter v1.0",
            "menu_file": "File(&F)",
            "menu_new_project": "New Project(&N)",
            "menu_open_project": "Open Project(&O)",
            "menu_recent_projects": "Recent Projects",
            "menu_save_project": "Save Project(&S)",
            "menu_project_settings": "Project Settings(&P)",
            "menu_exit": "Exit(&X)",
            "menu_help": "Help(&H)",
            "menu_about": "About(&A)",
            "menu_language": "Language",
            "menu_tools": "Tools(&T)",
            "menu_extract_metadata": "Extract Metadata(&E)",
            "menu_merge_metadata": "Merge Metadata(&M)",
            "menu_theme": "Theme",

            "menu_settings": "Settings(S)",



            "theme_light": "Light",

            "theme_dark": "Dark",
            "theme_blue": "Deep Blue",
            "theme_sepia": "Warm Sepia",

            "switch_view": "Switch View (Tab)",
            "delete_selection": "Delete Selection (F5)",
            "copy_selection": "Copy Selection (F5)",

            "clear_tasks": "Clear Tasks (Ctrl+Shift+C)",
            "batch_add": "Batch Add (Ctrl+B)",
            "edit_metadata": "Edit Metadata (Ctrl+E)",
            "view_metadata": "View Metadata (Ctrl+E)",



            "select_all": "Select All",

            "status_no_project": "Please create or open a project",
            "status_tasks": "Tasks: {count}",
            "status_project": "Project: {name}",
            "view_label": "Current View: ",
            "view_source": "Source Directory",
            "view_project": "Favorites",

            "hint_label": "<b>Nav</b> <span style='color: #2196F3;'>↑↓</span> Browse · <span style='color: #2196F3;'>Alt+↑↓</span> Platform · <span style='color: #2196F3;'>PgUp/Dn</span> Page<br><b>Find</b> <span style='color: #4CAF50;'>Ctrl+F</span> Search · <span style='color: #4CAF50;'>Ctrl+P</span> Platform · <span style='color: #4CAF50;'>Ctrl+L</span> List<br><b>Edit</b> <span style='color: #F44336;'>Space</span> Select · <span style='color: #F44336;'>Enter</span> Play · <span style='color: #F44336;'>Ctrl+B</span> Batch · <span style='color: #F44336;'>Ctrl+E</span> Edit",




            "search_label": "Search:",
            "platform_label": "Platform:",
            "all_platforms": "All Platforms",
            "search_placeholder": "Search by name, platform, or developer...",
            "game_count_label": "Games: {total} | Selected: {selected}",
            "pagination_label": "Page: {current}/{total_pages} | Showing {start}-{end} of {total}",
            "prev_page": "Previous",
            "next_page": "Next",
            "confirm_exec_title": "Confirm Execution",
            "confirm_exec_msg": "The following tasks will be executed:\n\nAdd: {add}\nRemove: {remove}\nUpdate: {update}\n\nDo you want to continue?",
            "project_saved": "Project saved",
            "error": "Error",
            "info": "Info",
            "batch_add_complete": "Input {total}, matched and added {found} games to task queue",
            "welcome_title": "Welcome to Pegasus Game Filter",
            "welcome_desc": "Quickly filter and manage your Pegasus game library",
            "recent_projects": "Recent Projects:",
            "no_recent_projects": "No recent projects",
            "btn_new_project": "New Project",
            "btn_open_project": "Open Existing Project",
            "dialog_new_project": "New Project",
            "dialog_project_name": "Project Name:",
            "dialog_select_source": "Select Source ROM Root Directory",
            "dialog_select_project": "Select Favorites Directory",
            "dialog_save_project": "Save Project File",

            "msg_load_failed": "Failed to load project",
            "msg_init_failed": "Initialization failed: {error}",
            "msg_no_pending_tasks": "No pending tasks",
            "batch_add_input_title": "Batch Add",
            "batch_add_input_label": "Enter game names (one per line):",
            "batch_add_progress_title": "Batch Search Progress",
            "batch_add_searching": "Searching for matching games...",
            "batch_add_searching_status": "Searching ({current}/{total}): {name}",
            "cancel": "Cancel",
            "duplicate_warning": "Same game already exists in favorites directory.",
            "task_added": "Added {count} games to task queue",

            "tasks_cleared": "Task queue cleared",
            "loading_games": "Loading games...",
            "refreshing_platforms": "Refreshing platforms...",
            "filtering": "Filtering...",
            "please_wait": "Please wait",
            "media_preview": "Media Preview",
            "base_info_label": "Basic Information",
            "title_label": "Title:",
            "sort_by_label": "Sort By:",
            "platform_label_detail": "Platform:",
            "developer_label": "Developer:",
            "description_label": "Description",
            "file_info_label": "File Information",
            "rom_file_label": "ROM File:",
            "dir_label": "Directory:",
            "btn_save_changes": "Save Changes",
            "no_cover": "No Cover",
            "no_game": "No Game",
            "menu_settings": "Settings",
            "btn_browse": "Browse...",
            "btn_save": "Save",
            "btn_cancel": "Cancel",
            "btn_close": "Close",
            "msg_enter_name": "Please enter project name",

            "msg_select_roms": "Please select favorites directory",
            "msg_select_source": "Please select source ROM directory",
            "msg_save_success": "Project settings saved",

            "msg_save_failed": "Failed to save project",
            "log_title": "Execution Details",
            "log_starting": "Starting execution...",
            "log_finished": "Execution finished",
            "log_failed": "Execution failed: {error}",
            "warning": "Warning",
            "success": "Success"
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Translator, cls).__new__(cls)
            cls._instance.settings = QSettings("PegasusGameFilter", "App")
            cls._instance.current_lang = cls._instance.settings.value("language", cls.LANG_ZH)
        return cls._instance

    def set_language(self, lang):
        if lang in self.TRANSLATIONS:
            self.current_lang = lang
            self.settings.setValue("language", lang)
            return True
        return False

    def get_language(self):
        return self.current_lang

    def translate(self, key, **kwargs):
        text = self.TRANSLATIONS.get(self.current_lang, {}).get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        return text

# 全局访问点
_translator = Translator()

def tr(key, **kwargs):
    return _translator.translate(key, **kwargs)

def set_lang(lang):
    return _translator.set_language(lang)

def get_lang():
    return _translator.get_language()
