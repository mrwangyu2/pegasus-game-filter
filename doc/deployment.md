# 天马G游戏筛选器 v1.0 - 部署和使用指南

## 快速开始

### Windows平台

#### 方法1：Python环境（推荐）

```cmd
# 1. 安装Python 3.7+ (从python.org下载)
#    安装时勾选 "Add Python to PATH"

# 2. 安装项目
cd pegasus-game-filter
pip install -r requirements.txt

# 3. 运行
python main.py
```

#### 方法2：打包为单文件版 EXE (推荐给普通用户)

如果你希望在没有安装 Python 的电脑上运行，可以使用 `PyInstaller` 将程序打包成一个独立的 `.exe` 文件。

**步骤：**

1.  安装打包工具：
    ```cmd
    pip install pyinstaller
    ```

2.  执行打包命令：
    ```cmd
    pyinstaller --noconfirm --onefile --windowed ^
        --name "天马G游戏筛选器" ^
        --icon "ui/icon/app.ico" ^
        --add-data "ui/icon;ui/icon" ^
        main.py
    ```

**参数说明：**
- `--onefile`: 将所有内容打包进一个 exe 文件。
- `--windowed`: 运行时不显示黑色命令行窗口。
- `--icon`: 指定程序图标。
- `--add-data`: 将图标等资源文件夹包含进打包文件。

**打包结果：**
- 打包完成后，在生成的 `dist/` 目录下可以找到 `天马G游戏筛选器.exe`。
- 你可以将这个 exe 文件发送给任何人，他们无需安装 Python 即可直接运行。

### macOS平台

```bash
# 1. 安装Homebrew (如未安装)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. 安装Python
brew install python3

# 3. 安装项目
cd pegasus-game-filter
pip3 install -r requirements.txt

# 4. 运行
python3 main.py
```

### Linux平台

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-pyqt5
pip3 install -r requirements.txt
python3 main.py

# Fedora
sudo dnf install python3 python3-pip python3-qt5
pip3 install -r requirements.txt
python3 main.py

# Arch
sudo pacman -S python python-pip python-pyqt5
pip install -r requirements.txt
python3 main.py
```

## 完整使用教程

### 1. 准备工作

确保你的ROM目录符合天马G规则：

```
Roms/
├── GBA/
│   ├── metadata.pegasus.txt   ← 必需
│   ├── media/                 ← 必需
│   │   └── 游戏名称/
│   │       ├── logo.png
│   │       ├── boxFront.png
│   │       └── video.mp4
│   └── *.gba/*.zip
├── GB/
└── ...
```

### 2. 创建第一个项目

1. 启动程序：`python main.py`
2. 点击"文件" -> "新建项目"
3. 输入项目名称（如："GBA精选"）
4. 选择**来源ROM根目录**（包含GBA、GB等平台目录的Roms文件夹）
5. 选择**项目ROM根目录**（新建一个空文件夹）
6. 保存项目文件（如："GBA精选.json"）

### 3. 基本操作流程

#### 流程A：单个游戏添加

```
1. 在来源视图中浏览游戏
2. 点击游戏查看详情（封面、视频）
3. 按【空格】选择游戏（背景变黄）
4. 按【A】键添加到任务队列
5. 按【F5】键执行任务
6. 查看日志窗口确认结果
```

#### 流程B：批量添加

```
1. 准备游戏名称列表（每行一个）
   例如：
   黄金太阳
   口袋妖怪
   最终幻想
   
2. 点击"批量添加"按钮
3. 粘贴游戏名称
4. 程序自动搜索并添加到任务队列
5. 按【F5】执行任务
```

#### 流程C：删除游戏

```
1. 按【Tab】切换到项目视图
2. 按【空格】选择要删除的游戏
3. 按【D】键添加删除任务
4. 按【F5】执行任务
```

#### 流程D：编辑游戏信息

```
1. 选择游戏
2. 在右侧编辑信息
3. 点击"保存修改"
4. 按【F5】应用更改
```

### 4. 快捷键完整列表

| 快捷键 | 功能 | 适用范围 |
|--------|------|----------|
| **Tab** | 切换视图 | 全局 |
| **Space** | 选择/取消选择 | 游戏列表 |
| **↑/↓** | 上一个/下一个 | 游戏列表 |
| **A** | 添加到任务 | 来源视图 |
| **D** | 删除任务 | 项目视图 |
| **F5** | 执行任务 | 全局 |
| **Ctrl+N** | 新建项目 | 全局 |
| **Ctrl+O** | 打开项目 | 全局 |
| **Ctrl+S** | 保存项目 | 全局 |

### 5. 任务队列系统

**核心概念**：
- 先规划操作（添加到队列）
- 再统一执行（F5键）
- 可以撤销（清空队列）

**任务类型**：
- 🟢 **添加任务**：从来源复制到项目
- 🔴 **删除任务**：从项目删除
- 🟡 **更新任务**：更新元数据

**状态显示**：
- 状态栏显示：`任务: 5`
- 执行时显示日志窗口
- 不同颜色表示不同状态

### 6. metadata.pegasus.txt 格式

```
game: 黄金太阳1 开启的封印
file: 黄金太阳1 开启的封印.zip
sort-by: 001
developer: 任天堂
description: 《黄金太阳1 开启的封印》是一款GBA平台的经典RPG游戏，
游戏围绕着传说中的炼金术展开...

game: 另一个游戏
file: 另一个游戏.gba
sort-by: 002
developer: 开发商名称
description: 游戏描述可以
分多行书写
```

**字段说明**：
- `game`: 游戏名称（**重要**：必须与media目录名一致）
- `file`: ROM文件名
- `sort-by`: 排序编号
- `developer`: 开发者
- `description`: 游戏描述（可多行）

### 7. media文件命名规则

在 `media/{游戏名称}/` 目录下：

```
logo.png / logo.jpg     # Logo图片
boxFront.png / ...      # 封面图片  
video.mp4 / video.avi   # 视频文件
```

**支持的格式**：
- 图片：.png, .jpg, .jpeg, .gif, .bmp
- 视频：.mp4, .avi, .mkv, .mov

### 8. 常见问题

#### Q: 找不到metadata.pegasus.txt

**A**: 
- 确认选择的是**Roms根目录**（不是平台目录）
- 检查平台目录（如GBA）下是否有此文件
- 文件名区分大小写

#### Q: 游戏没有显示logo

**A**:
- 检查 `media/{游戏名称}/logo.png` 是否存在
- 确认game字段与目录名**完全一致**
- 检查文件格式是否支持

#### Q: 任务执行失败

**A**:
- 查看日志窗口的红色错误信息
- 检查磁盘空间
- 确认有写入权限
- 验证源文件存在

#### Q: 批量添加找不到游戏

**A**:
- 使用游戏的准确名称
- 支持部分匹配（如"黄金太阳"可以找到"黄金太阳1"）
- 检查来源目录中是否真的有这个游戏

#### Q: 视频无法播放

**A**:
- 确认video文件存在
- 检查视频格式（推荐mp4）
- 尝试使用其他播放器测试视频文件

### 9. 最佳实践

#### 目录组织建议

```
我的游戏/
├── projects/              # 项目文件
│   ├── GBA精选.json
│   ├── RPG合集.json
│   └── 动作游戏.json
├── source/                # 来源ROM
│   └── Roms/
│       ├── GBA/
│       ├── GB/
│       └── ...
└── filtered/              # 筛选结果
    ├── GBA精选/
    │   └── Roms/
    ├── RPG合集/
    └── ...
```

#### 工作流程建议

1. **第一步**：整理来源ROM目录
   - 确保所有平台都有metadata.pegasus.txt
   - 检查media目录结构

2. **第二步**：创建项目
   - 按主题创建不同项目（平台、类型等）
   - 使用有意义的项目名称

3. **第三步**：筛选游戏
   - 使用搜索功能快速定位
   - 查看封面和视频做判断
   - 批量操作提高效率

4. **第四步**：执行和验证
   - 统一执行任务
   - 检查日志确认无误
   - 切换到项目视图验证

5. **第五步**：集成到天马G
   - 将项目ROM目录添加到天马G
   - 享受精心筛选的游戏库

### 10. 性能建议

- **大型ROM库**（>1000游戏）：使用搜索而非滚动
- **批量添加**：一次不超过100个游戏
- **定期清理**：删除不需要的游戏释放空间
- **备份重要**：定期备份项目JSON文件

### 11. 故障排除

#### 程序无法启动

```bash
# 检查Python版本
python --version  # 应该 >= 3.7

# 重新安装PyQt5
pip install PyQt5 --force-reinstall

# 查看错误信息
python main.py 2>&1 | tee error.log
```

#### 权限问题（Linux/macOS）

```bash
# 给予执行权限
chmod +x main.py

# 检查目录权限
ls -la /path/to/roms

# 如果需要，修改权限
chmod 755 /path/to/roms
```

#### 中文显示问题（Windows）

```cmd
# 设置控制台编码为UTF-8
chcp 65001

# 或在代码中设置
set PYTHONIOENCODING=utf-8
```

### 12. 卸载

```bash
# 删除项目目录
rm -rf pegasus-game-filter

# 卸载PyQt5（可选）
pip uninstall PyQt5
```

### 13. 更新

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 运行新版本
python main.py
```

## 开发者信息

- **版本**: 1.0.0
- **开发者**: 王宇
- **邮箱**: wangyuxxx@163.com
- **开发时间**: 2025年1月

## 获取帮助

1. 查看README.md了解功能
2. 查看IMPLEMENTATION.md了解技术细节
3. 通过邮件联系开发者

## 许可证

本项目仅供学习和个人使用。

---

**祝您使用愉快！如有问题，请随时联系开发者。**
