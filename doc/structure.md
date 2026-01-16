# 项目结构说明

## 完整目录结构

```
pegasus-game-filter/
│
├── main.py                           # 程序入口文件
│
├── requirements.txt                  # Python依赖包列表
├── run.bat                           # Windows 启动脚本
│
├── doc/                              # 项目文档目录
│   ├── readme.md                     # 项目说明文档
│   ├── implementation.md             # 技术实现文档
│   ├── deployment.md                 # 部署和使用指南
│   └── structure.md                  # 本文件
│
├── core/                             # 核心业务逻辑模块
│   ├── __init__.py                  # 模块初始化
│   ├── project.py                   # 项目管理与配置
│   ├── metadata_parser.py           # 天马G元数据解析与写入
│   ├── game_manager.py              # 游戏列表维护与任务执行
│   ├── task_system.py               # 异步任务队列系统
│   ├── i18n.py                      # 多语言国际化支持
│   └── theme.py                     # UI主题与图标加载逻辑
│
└── ui/                               # 用户界面模块
    ├── __init__.py                  # 模块初始化
    ├── main_window.py               # 主窗口逻辑
    ├── game_list_widget.py          # 游戏列表组件
    ├── game_detail_widget.py        # 游戏详情与媒体预览组件
    ├── log_window.py                # 任务执行日志窗口
    ├── about_dialog.py              # 关于对话框
    ├── project_settings_dialog.py   # 项目设置对话框
    ├── startup_dialog.py            # 启动项目选择对话框
    ├── metadata_edit_dialog.py      # 元数据/配置编辑对话框
    ├── metadata_extract_dialog.py   # 元数据提取工具对话框
    ├── metadata_merge_dialog.py     # 元数据合并工具对话框
    └── icon/                        # 程序图标资源
```

## 文件说明

### 根目录文件

#### main.py
- **作用**: 程序入口文件
- **功能**: 
  - 启动Qt应用
  - 创建主窗口
  - 设置应用属性
- **代码量**: ~30行

#### requirements.txt
- **作用**: Python依赖包列表
- **内容**: 
  ```
  PyQt5==5.15.9
  ```

#### README.md
- **作用**: 项目说明和使用手册
- **内容**:
  - 功能介绍
  - 安装步骤
  - 使用指南
  - 快捷键列表
  - 常见问题

#### IMPLEMENTATION.md
- **作用**: 技术实现文档
- **内容**:
  - 架构设计
  - 核心算法
  - 数据流图
  - 代码规范

#### DEPLOYMENT.md
- **作用**: 部署和使用指南
- **内容**:
  - 各平台部署方法
  - 完整使用教程
  - 故障排除
  - 最佳实践

#### PROJECT_STRUCTURE.md
- **作用**: 本文件，项目结构说明

### core/ 核心模块

#### core/__init__.py
- **作用**: 模块初始化，导出核心类
- **导出**:
  - Project
  - Game
  - MetadataParser
  - GameManager
  - TaskQueue
  - TaskType
  - TaskStatus

#### core/project.py
- **作用**: 项目管理
- **核心类**:
  - `Project`: 项目信息管理
- **主要方法**:
  - `save()`: 保存项目到JSON
  - `load()`: 从JSON加载项目
  - `is_valid()`: 验证项目有效性
- **代码量**: ~70行

#### core/metadata_parser.py
- **作用**: 天马G元数据解析
- **核心类**:
  - `Game`: 游戏元数据对象
  - `MetadataParser`: 元数据解析器
- **主要方法**:
  - `parse_platform_directory()`: 解析平台目录
  - `write_metadata()`: 写入元数据文件
  - `find_platform_directories()`: 查找平台目录
  - `get_logo_path()`: 获取logo路径
  - `get_boxfront_path()`: 获取封面路径
  - `get_video_path()`: 获取视频路径
- **代码量**: ~150行

#### core/game_manager.py
- **作用**: 游戏增删改查管理
- **核心类**:
  - `GameManager`: 游戏管理器
- **主要方法**:
  - `load_all_platforms()`: 加载所有平台
  - `execute_tasks()`: 执行任务队列
  - `_execute_add_task()`: 执行添加任务
  - `_execute_remove_task()`: 执行删除任务
  - `_execute_update_task()`: 执行更新任务
  - `search_games()`: 搜索游戏
- **代码量**: ~180行

#### core/task_system.py
- **作用**: 任务队列管理系统
- **核心类**:
  - `TaskType`: 任务类型枚举
  - `TaskStatus`: 任务状态枚举
  - `Task`: 任务数据类
  - `TaskQueue`: 任务队列
- **主要方法**:
  - `add_task()`: 添加任务
  - `remove_task()`: 移除任务
  - `clear()`: 清空队列
  - `get_task_count()`: 获取任务统计
  - `has_pending_tasks()`: 检查待执行任务
  - `set_log_callback()`: 设置日志回调
- **代码量**: ~90行

### ui/ 界面模块

#### ui/__init__.py
- **作用**: UI模块初始化，导出UI类
- **导出**:
  - MainWindow
  - GameListWidget
  - GameDetailWidget
  - LogWindow
  - AboutDialog
  - ProjectSettingsDialog

#### ui/main_window.py
- **作用**: 主窗口界面和控制逻辑
- **核心类**:
  - `MainWindow`: 主窗口
- **主要方法**:
  - `create_menu_bar()`: 创建菜单栏
  - `create_toolbar()`: 创建工具栏
  - `new_project()`: 新建项目
  - `open_project()`: 打开项目
  - `switch_view()`: 切换视图
  - `add_to_task_queue()`: 添加到任务队列
  - `execute_tasks()`: 执行任务
  - `batch_add_games()`: 批量添加
- **代码量**: ~350行

#### ui/game_list_widget.py
- **作用**: 游戏列表显示组件
- **核心类**:
  - `GameListWidget`: 游戏列表
- **主要方法**:
  - `set_games()`: 设置游戏列表
  - `update_list()`: 更新显示
  - `filter_games()`: 过滤游戏
  - `toggle_selection()`: 切换选择状态
  - `get_selected_games()`: 获取选中游戏
- **特性**:
  - 显示logo图标
  - 多选功能（黄色背景）
  - 实时搜索
- **代码量**: ~150行

#### ui/game_detail_widget.py
- **作用**: 游戏详情显示和编辑
- **核心类**:
  - `GameDetailWidget`: 游戏详情
- **主要方法**:
  - `set_game()`: 设置当前游戏
  - `load_cover()`: 加载封面图片
  - `load_video()`: 加载视频
  - `toggle_video()`: 切换播放
  - `save_changes()`: 保存修改
- **特性**:
  - 图片预览
  - 视频播放
  - 元数据编辑
- **代码量**: ~250行

#### ui/log_window.py
- **作用**: 任务执行日志窗口
- **核心类**:
  - `TaskExecutor`: 任务执行线程
  - `LogWindow`: 日志窗口
- **主要方法**:
  - `log()`: 添加日志
  - `start_execution()`: 开始执行
  - `on_execution_finished()`: 执行完成
- **特性**:
  - 彩色日志
  - 多线程执行
  - 进度显示
- **代码量**: ~120行

#### ui/about_dialog.py
- **作用**: 关于对话框
- **核心类**:
  - `AboutDialog`: 关于对话框
- **显示内容**:
  - 应用名称和版本
  - 开发时间
  - 功能介绍
  - 开发者信息
- **代码量**: ~80行

#### ui/project_settings_dialog.py
- **作用**: 项目设置对话框
- **核心类**:
  - `ProjectSettingsDialog`: 项目设置
- **主要方法**:
  - `browse_roms_path()`: 浏览ROM目录
  - `browse_source_path()`: 浏览来源目录
  - `save_settings()`: 保存设置
- **可编辑内容**:
  - 项目名称
  - 项目ROM目录
  - 来源ROM目录
- **代码量**: ~100行

#### ui/startup_dialog.py
- **作用**: 启动时的项目导航
- **功能**: 展示最近项目，提供新建和打开入口

#### ui/metadata_edit_dialog.py
- **作用**: 元数据/平台配置编辑
- **功能**: 提供文本编辑界面，支持编辑平台 Header 和查看元数据

#### ui/metadata_extract_dialog.py
- **作用**: 元数据提取工具
- **功能**: 批量扫描目录并提取生成元数据文件

#### ui/metadata_merge_dialog.py
- **作用**: 元数据合并工具
- **功能**: 合并不同来源的元数据文件

## 模块关系图

```
┌──────────────┐
│   main.py    │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│      MainWindow              │
│  (ui/main_window.py)         │
└────┬─────────────────────┬───┘
     │                     │
     ▼                     ▼
┌─────────────┐      ┌─────────────┐
│ GameList    │      │ GameDetail  │
│ Widget      │      │ Widget      │
└─────────────┘      └─────────────┘
     │                     │
     └──────────┬──────────┘
                ▼
        ┌──────────────┐
        │ GameManager  │
        │ TaskQueue    │
        └──────┬───────┘
               │
               ▼
        ┌──────────────┐
        │ Metadata     │
        │ Parser       │
        └──────────────┘
```

## 代码统计

| 模块 | 文件数 | 代码行数 | 说明 |
|------|--------|----------|------|
| core/ | 4 | ~490 | 核心业务逻辑 |
| ui/ | 6 | ~1050 | 用户界面 |
| 根目录 | 1 | ~30 | 程序入口 |
| **总计** | **11** | **~1570** | 纯Python代码 |

*注：不包括空行和注释*

## 依赖关系

### core模块内部依赖
```
project.py          -> (无依赖)
metadata_parser.py  -> (无依赖)
task_system.py      -> metadata_parser
game_manager.py     -> metadata_parser, task_system
```

### ui模块依赖
```
about_dialog.py             -> PyQt5
project_settings_dialog.py  -> PyQt5, core.project
log_window.py               -> PyQt5, core.game_manager
game_detail_widget.py       -> PyQt5, core.metadata_parser
game_list_widget.py         -> PyQt5, core.metadata_parser
main_window.py              -> PyQt5, 所有ui组件, 所有core模块
```

## 如何添加新功能

### 添加新的UI组件

1. 在`ui/`目录创建新文件
2. 继承合适的Qt类
3. 在`ui/__init__.py`中导出
4. 在`main_window.py`中集成

### 添加新的任务类型

1. 在`task_system.py`的`TaskType`枚举中添加
2. 在`game_manager.py`中实现执行逻辑
3. 在`main_window.py`中添加UI操作

### 添加新的元数据字段

1. 在`metadata_parser.py`的`Game`类中添加属性
2. 在`_parse_game_block()`中添加解析逻辑
3. 在`write_metadata()`中添加写入逻辑
4. 在UI中添加编辑界面

## 测试文件结构（建议）

```
tests/
├── __init__.py
├── test_project.py
├── test_metadata_parser.py
├── test_game_manager.py
├── test_task_system.py
└── fixtures/
    └── sample_metadata.txt
```

## 打包结构

使用PyInstaller打包后：

```
dist/
└── 天马G游戏筛选器.exe  # Windows
    或
    天马G游戏筛选器.app  # macOS
    或
    天马G游戏筛选器      # Linux
```

## 配置文件

运行时生成的文件：

```
项目文件.json           # 项目配置
```

JSON格式：
```json
{
  "name": "项目名称",
  "roms_path": "/path/to/project/roms",
  "source_path": "/path/to/source/roms"
}
```

## 总结

本项目采用清晰的模块化设计：

- **core**: 纯Python业务逻辑，不依赖PyQt5
- **ui**: 所有界面代码，依赖PyQt5
- **分离关注点**: 数据处理和界面展示完全分离
- **易于测试**: 核心逻辑可独立测试
- **易于扩展**: 新增功能只需添加新模块

代码遵循PEP 8规范，使用snake_case命名，注释完整，结构清晰。
