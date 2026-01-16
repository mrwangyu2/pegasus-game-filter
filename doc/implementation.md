# 天马G游戏筛选器 - 实现文档 v1.0

## 1. 整体架构

### 1.1 架构设计

采用MVC架构模式，增加了任务队列层：

```
┌─────────────────────────────────────┐
│         UI Layer (View)             │
│  - MainWindow (主窗口)               │
│  - GameListWidget (游戏列表)         │
│  - GameDetailWidget (游戏详情)       │
│  - LogWindow (日志窗口)              │
│  - AboutDialog (关于窗口)            │
│  - ProjectSettingsDialog (设置)     │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Controller Layer               │
│  - 事件处理                          │
│  - 用户交互逻辑                       │
│  - 任务队列管理                       │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│     Task Queue Layer                │
│  - TaskQueue (任务队列)              │
│  - Task (任务对象)                   │
│  - TaskType (任务类型)               │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│      Core Layer (Model)             │
│  - Project (项目管理)                │
│  - GameManager (游戏管理)            │
│  - MetadataParser (元数据解析)       │
└─────────────────────────────────────┘
```

### 1.2 天马G目录结构

```
Roms/                          # ROM根目录
├── GBA/                       # 平台目录
│   ├── metadata.pegasus.txt  # 元数据文件
│   ├── media/                # 媒体目录
│   │   └── {游戏名称}/       # 游戏媒体目录
│   │       ├── logo.png      # Logo图片
│   │       ├── boxFront.png  # 封面图片
│   │       └── video.mp4     # 视频文件
│   └── *.gba / *.zip         # 游戏ROM文件
├── GB/                        # 其他平台
└── ...
```

## 2. 核心模块实现

### 2.1 元数据解析器 (metadata_parser.py)

**Game类**：

```python
class Game:
    - game: str          # 游戏名称（用于media目录）
    - file: str          # 游戏文件名
    - sort_by: str       # 排序
    - developer: str     # 开发者
    - description: str   # 游戏描述
    - platform: str      # 平台名称
    - platform_path: Path # 平台目录路径
```

**关键方法**：

1. `get_logo_path()`: 根据game名称和platform_path构建logo路径
2. `get_boxfront_path()`: 构建封面图片路径
3. `get_video_path()`: 构建视频文件路径

**MetadataParser类**：

```python
parse_platform_directory(platform_path):
    """解析单个平台目录"""
    1. 检查metadata.pegasus.txt是否存在
    2. 检查media目录是否存在
    3. 读取并解析元数据文件
    4. 按空行分割游戏块
    5. 解析每个游戏块
    6. 返回游戏列表
```

**字段解析规则**：

```
game: 游戏名称        -> game
file: 文件名          -> file
sort-by: 排序         -> sort_by
developer: 开发者     -> developer
description: 描述     -> description (支持多行)
```

### 2.2 任务系统 (task_system.py)

**任务类型枚举**：

```python
class TaskType(Enum):
    ADD = "添加"      # 添加游戏到项目
    REMOVE = "删除"   # 从项目删除游戏
    UPDATE = "更新"   # 更新游戏元数据
```

**任务状态枚举**：

```python
class TaskStatus(Enum):
    PENDING = "待执行"
    SUCCESS = "成功"
    FAILED = "失败"
    RUNNING = "执行中"
```

**Task数据类**：

```python
@dataclass
class Task:
    task_type: TaskType
    game: Game
    status: TaskStatus = PENDING
    error_message: str = ""
```

**TaskQueue类**：

核心方法：
- `add_task()`: 添加任务，自动去重
- `remove_task()`: 移除任务
- `clear()`: 清空队列
- `get_task_count()`: 获取任务统计
- `has_pending_tasks()`: 检查是否有待执行任务
- `set_log_callback()`: 设置日志回调
- `log()`: 记录日志

去重逻辑：
```python
# 如果已存在相同游戏的任务，更新任务类型而不是添加新任务
for task in self.tasks:
    if task.game.game == game.game and task.game.platform == game.platform:
        task.task_type = task_type
        return
```

### 2.3 游戏管理器 (game_manager.py)

**GameManager类**：

数据结构：
```python
self.roms_root: Path                      # ROM根目录
self.platforms: Dict[str, List[Game]]     # 平台->游戏列表映射
self.task_queue: TaskQueue                # 任务队列
```

**任务执行流程**：

```python
execute_tasks():
    1. 遍历任务队列
    2. 根据任务类型调用对应方法
    3. 更新任务状态
    4. 记录日志
    5. 统计结果
    6. 清空队列
```

**添加任务执行** (_execute_add_task):

```
1. 创建平台目录
2. 创建media/{游戏名称}目录
3. 复制游戏ROM文件
4. 复制logo图片
5. 复制boxFront图片
6. 复制video视频
7. 更新内存中的游戏列表
8. 写入metadata.pegasus.txt
```

**删除任务执行** (_execute_remove_task):

```
1. 删除游戏ROM文件
2. 删除整个media/{游戏名称}目录
3. 从内存列表中移除
4. 更新metadata.pegasus.txt
```

**更新任务执行** (_execute_update_task):

```
1. 直接写入metadata.pegasus.txt
   (内存中的Game对象已在UI中更新)
```

### 2.4 项目管理 (project.py)

**Project类**：

```python
class Project:
    name: str              # 项目名称
    roms_path: Path        # 项目ROM根目录
    source_path: Path      # 来源ROM根目录
    project_file: Path     # 项目文件路径
```

**JSON格式**：

```json
{
  "name": "我的项目",
  "roms_path": "/path/to/project/roms",
  "source_path": "/path/to/source/roms"
}
```

## 3. UI模块实现

### 3.1 主窗口 (main_window.py)

**视图切换机制**：

```python
current_view: str  # "source" 或 "project"

switch_view():
    if current_view == "source":
        # 切换到项目视图
        - 显示project_manager的游戏
        - 启用删除按钮
        - 禁用批量添加
    else:
        # 切换到来源视图
        - 显示source_manager的游戏
        - 禁用删除按钮
        - 启用批量添加
```

**任务管理流程**：

```
用户选择游戏 (空格键)
    ↓
添加到任务队列 (A键)
    ↓
任务计数更新
    ↓
执行任务 (F5键)
    ↓
显示日志窗口
    ↓
任务执行完成
    ↓
刷新游戏列表
```

### 3.2 游戏列表 (game_list_widget.py)

**Logo显示实现**：

```python
for game in games:
    item = QListWidgetItem(game.game)
    
    # 加载logo
    logo_path = game.get_logo_path()
    if logo_path and logo_path.exists():
        icon = QIcon(str(logo_path))
        item.setIcon(icon)
    
    # 设置图标大小
    list_widget.setIconSize(QSize(48, 48))
```

**多选功能实现**：

```python
selected_games: Set[Game]  # 使用Set存储选中的游戏

toggle_selection():
    current_game = get_current_game()
    if current_game in selected_games:
        selected_games.remove(current_game)
    else:
        selected_games.add(current_game)
    
    update_list()  # 更新显示（黄色背景）
```

**空格键处理**：

```python
def keyPressEvent(self, event):
    if event.key() == Qt.Key_Space:
        self.toggle_selection()
        event.accept()
```

### 3.3 日志窗口 (log_window.py)

**多线程执行**：

```python
class TaskExecutor(QThread):
    def run(self):
        results = game_manager.execute_tasks()
        self.finished.emit(results)
```

**彩色日志实现**：

```python
color_map = {
    "info": "#d4d4d4",      # 白色
    "success": "#4ec9b0",   # 青色
    "error": "#f48771",     # 红色
    "warning": "#dcdcaa",   # 黄色
}

def log(message, level):
    color = color_map[level]
    cursor.insertHtml(f'<span style="color: {color};">{message}</span><br>')
```

**日志窗口流程**：

```
start_execution(game_manager)
    ↓
创建TaskExecutor线程
    ↓
设置日志回调
    ↓
启动线程执行任务
    ↓
实时显示日志
    ↓
执行完成
    ↓
显示统计结果
    ↓
启用关闭按钮
```

### 3.4 游戏详情 (game_detail_widget.py)

**媒体加载**：

```python
def set_game(game):
    # 加载基本信息
    load_metadata()
    
    # 加载封面
    boxfront_path = game.get_boxfront_path()
    pixmap = QPixmap(str(boxfront_path))
    scaled = pixmap.scaled(width, height, Qt.KeepAspectRatio)
    label.setPixmap(scaled)
    
    # 加载视频
    video_path = game.get_video_path()
    media_player.setMedia(QMediaContent(QUrl.fromLocalFile(str(video_path))))
```

**视频控制**：

```python
toggle_video():
    if player.state() == QMediaPlayer.PlayingState:
        player.pause()
        button.setText("播放视频")
    else:
        player.play()
        button.setText("暂停视频")
```

## 4. 关键算法

### 4.1 游戏搜索算法

```python
def search_games(keyword):
    keyword = keyword.lower()
    results = []
    
    for platform_games in platforms.values():
        for game in platform_games:
            if (keyword in game.game.lower() or
                keyword in game.platform.lower() or
                keyword in game.developer.lower()):
                results.append(game)
    
    return results
```

### 4.2 批量添加算法

```python
def batch_add_games(game_names):
    all_games = get_all_games()
    
    for name in game_names:
        for game in all_games:
            if name.lower() in game.game.lower():
                task_queue.add_task(TaskType.ADD, game)
                break  # 找到第一个匹配就停止
```

### 4.3 文件复制算法

```python
def copy_game_files(source_game):
    # 1. 复制ROM文件
    shutil.copy2(source_file, dest_file)
    
    # 2. 创建media目录
    media_dir = roms_path / "media" / game.game
    media_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. 复制media文件（logo, boxFront, video）
    for file_type in ['logo', 'boxFront', 'video']:
        source_file = find_media_file(source_game, file_type)
        if source_file:
            dest_file = media_dir / source_file.name
            shutil.copy2(source_file, dest_file)
```

## 5. 数据流

### 5.1 添加游戏流程

```
用户在来源视图选择游戏
    ↓
按空格键标记（黄色背景）
    ↓
按A键添加到任务队列
    ↓
task_queue.add_task(ADD, game)
    ↓
更新任务计数显示
    ↓
用户按F5执行任务
    ↓
显示确认对话框
    ↓
打开日志窗口
    ↓
TaskExecutor线程执行
    ↓
逐个执行任务：
    - 创建目录
    - 复制文件
    - 更新元数据
    - 记录日志
    ↓
执行完成
    ↓
刷新项目视图
    ↓
清空任务队列
```

### 5.2 删除游戏流程

```
切换到项目视图 (Tab)
    ↓
选择要删除的游戏 (空格)
    ↓
按D键添加删除任务
    ↓
task_queue.add_task(REMOVE, game)
    ↓
按F5执行任务
    ↓
确认删除
    ↓
执行删除：
    - 删除ROM文件
    - 删除media目录
    - 更新元数据
    - 记录日志
    ↓
刷新显示
```

### 5.3 批量添加流程

```
点击"批量添加"
    ↓
输入游戏名称列表
    ↓
解析名称列表
    ↓
for each 名称:
    在source_manager中搜索
    if 找到:
        添加到任务队列
    ↓
显示找到数量
    ↓
用户按F5执行
```

## 6. 错误处理

### 6.1 文件操作错误

```python
try:
    shutil.copy2(source, dest)
except PermissionError:
    log("权限不足", "error")
except FileNotFoundError:
    log("文件不存在", "error")
except Exception as e:
    log(f"复制失败: {e}", "error")
```

### 6.2 解析错误

```python
try:
    games = MetadataParser.parse_platform_directory(path)
except FileNotFoundError as e:
    QMessageBox.warning(self, "错误", f"找不到文件: {e}")
except Exception as e:
    QMessageBox.critical(self, "错误", f"解析失败: {e}")
```

### 6.3 任务执行错误

```python
for task in tasks:
    try:
        execute_task(task)
        task.status = SUCCESS
    except Exception as e:
        task.status = FAILED
        task.error_message = str(e)
        log(f"任务失败: {e}", "error")
```

## 7. 性能优化

### 7.1 图片缓存

考虑对logo图片进行缓存，避免重复加载：

```python
logo_cache: Dict[str, QIcon] = {}

def get_logo_icon(logo_path):
    if logo_path in logo_cache:
        return logo_cache[logo_path]
    
    icon = QIcon(str(logo_path))
    logo_cache[logo_path] = icon
    return icon
```

### 7.2 延迟加载

游戏详情的媒体文件只在需要时加载：

```python
def set_game(game):
    load_basic_info()  # 立即加载
    # 媒体文件在用户滚动到时再加载
```

### 7.3 多线程

任务执行使用独立线程，避免UI冻结：

```python
class TaskExecutor(QThread):
    def run(self):
        # 在后台线程执行耗时操作
        execute_all_tasks()
```

## 8. 扩展性

### 8.1 新增字段支持

在Game类中添加新字段：

```python
class Game:
    # 现有字段...
    new_field: str = ""
```

在解析器中添加解析逻辑：

```python
elif key == 'new-field':
    game.new_field = value
```

### 8.2 新增任务类型

```python
class TaskType(Enum):
    ADD = "添加"
    REMOVE = "删除"
    UPDATE = "更新"
    COPY = "复制"  # 新增
```

### 8.3 插件系统

未来可以添加插件系统：

```python
class Plugin:
    def on_game_added(self, game):
        pass
    
    def on_game_removed(self, game):
        pass
```

## 9. 测试策略

### 9.1 单元测试

```python
def test_metadata_parser():
    game = parse_game_block(sample_block)
    assert game.game == "黄金太阳1"
    assert game.file == "黄金太阳1.zip"

def test_task_queue():
    queue = TaskQueue()
    queue.add_task(TaskType.ADD, game)
    assert queue.get_task_count()[TaskType.ADD] == 1
```

### 9.2 集成测试

测试完整的添加流程：

```python
def test_add_game_flow():
    1. 创建测试项目
    2. 加载测试游戏
    3. 添加到任务队列
    4. 执行任务
    5. 验证文件已复制
    6. 验证元数据已更新
```

### 9.3 UI测试

使用pytest-qt进行UI测试：

```python
def test_main_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    # 模拟用户操作
    qtbot.mouseClick(window.add_task_btn, Qt.LeftButton)
```

## 10. 代码规范

### 10.1 命名规范

```python
# 类名：PascalCase
class GameManager:
    pass

# 函数/变量：snake_case
def load_games():
    game_count = 0

# 常量：UPPER_SNAKE_CASE
MAX_GAME_COUNT = 1000

# 私有方法：_开头
def _internal_method():
    pass
```

### 10.2 文档字符串

```python
def parse_game_block(block: str) -> Game:
    """
    解析游戏元数据块
    
    Args:
        block: 元数据文本块
        
    Returns:
        Game: 游戏对象
        
    Raises:
        ValueError: 如果块格式无效
    """
```

### 10.3 类型提示

```python
from typing import List, Dict, Optional

def get_games(platform: str) -> List[Game]:
    pass

def find_game(name: str) -> Optional[Game]:
    pass
```

## 11. 部署注意事项

### 11.1 依赖管理

确保requirements.txt包含所有依赖：

```
PyQt5==5.15.9
```

### 11.2 打包

使用PyInstaller打包：

```bash
pyinstaller --name="天马G游戏筛选器" \
            --windowed \
            --onefile \
            main.py
```

### 11.3 配置文件

项目文件使用JSON格式，易于编辑和迁移。

## 12. 未来改进

1. **数据库支持**: 使用SQLite缓存游戏信息
2. **云同步**: 支持项目文件云端同步
3. **主题系统**: 可切换的UI主题
4. **快速过滤**: 按平台、类型快速过滤
5. **撤销/重做**: 支持操作撤销
6. **导入/导出**: 支持游戏列表导入导出
7. **统计功能**: 显示游戏统计信息
8. **自动更新**: 检查并更新应用程序

## 总结

本实现文档详细描述了天马G游戏筛选器的技术实现细节，包括架构设计、核心算法、数据流和扩展方案。遵循PEP 8规范和单一职责原则，代码结构清晰，易于维护和扩展。
