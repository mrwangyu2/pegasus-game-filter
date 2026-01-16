
import os
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QRadioButton, 
                             QButtonGroup, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from core.i18n import tr
from core.theme import load_icon
from core.metadata_parser import MetadataParser


class ExtractionWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_root, target_root, mode):
        super().__init__()
        self.source_root = Path(source_root)
        self.target_root = Path(target_root)
        self.mode = mode # 1: meta+media, 2: meta only, 3: media only, 4: launch only

    def run(self):
        try:
            platform_dirs = MetadataParser.find_platform_directories(self.source_root)
            if not platform_dirs:
                self.finished.emit(False, "来源目录中未找到有效的平台目录 (metadata.pegasus.txt)")
                return

            total_platforms = len(platform_dirs)
            for i, p_dir in enumerate(platform_dirs):
                platform_name = p_dir.name
                self.progress.emit(i, total_platforms, f"正在处理平台: {platform_name}")
                
                target_platform_dir = self.target_root / platform_name
                target_platform_dir.mkdir(parents=True, exist_ok=True)

                source_meta_file = p_dir / "metadata.pegasus.txt"
                
                # 提取逻辑
                if self.mode in [1, 2, 4]:
                    # 需要解析 metadata
                    header, games = MetadataParser.parse_platform_directory(p_dir)
                    
                    if self.mode == 4:
                        # 仅提取 launch 字段，我们需要过滤掉其他字段，只保留 header 中的 launch 和游戏的 launch
                        # 实际上 MetadataParser 现在的 write_metadata 并不支持过滤
                        # 这里简单处理：构造只有 game, file 和 launch 相关的 metadata
                        # 注意：目前的 Game 对象没有 launch 属性，launch 在 header 中
                        # 如果用户是想提取整个 metadata.pegasus.txt 但只保留 launch 逻辑，比较复杂
                        # 这里我们实现为：提取 metadata.pegasus.txt，但 Header 只保留 launch
                        fields = MetadataParser.parse_header_fields(header)
                        launch_val = fields.get("launch", "")
                        new_header = f"launch: {launch_val}" if launch_val else ""
                        MetadataParser.write_metadata(games, target_platform_dir / "metadata.pegasus.txt", new_header)
                    else:
                        # 完整 metadata 或仅 metadata
                        shutil.copy2(source_meta_file, target_platform_dir / "metadata.pegasus.txt")

                if self.mode in [1, 3]:
                    # 提取 media
                    source_media_dir = p_dir / "media"
                    if source_media_dir.exists():
                        target_media_dir = target_platform_dir / "media"
                        target_media_dir.mkdir(parents=True, exist_ok=True)
                        # 遍历每个游戏的 media 目录
                        for game_media in source_media_dir.iterdir():
                            if game_media.is_dir():
                                target_game_media = target_media_dir / game_media.name
                                target_game_media.mkdir(parents=True, exist_ok=True)
                                # 拷贝 png, jpg, mp4 等符合 Pegasus 规则的文件
                                for f in game_media.iterdir():
                                    if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mkv']:
                                        shutil.copy2(f, target_game_media / f.name)

            self.finished.emit(True, f"提取完成！共处理 {total_platforms} 个平台。")
        except Exception as e:
            self.finished.emit(False, f"提取过程中发生错误: {str(e)}")

class MetadataExtractDialog(QDialog):
    def __init__(self, default_source="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("提取元数据工具")
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.resize(500, 350)



        self.init_ui(default_source)

    def init_ui(self, default_source):
        layout = QVBoxLayout(self)

        # 来源目录
        layout.addWidget(QLabel("来源 Roms 目录 (包含各平台子目录):"))
        src_layout = QHBoxLayout()
        self.src_edit = QLineEdit(default_source)
        src_layout.addWidget(self.src_edit)
        src_btn = QPushButton("浏览...")
        src_btn.clicked.connect(self.browse_source)
        src_layout.addWidget(src_btn)
        layout.addLayout(src_layout)

        # 存放目录
        layout.addWidget(QLabel("存放目录:"))
        dst_layout = QHBoxLayout()
        self.dst_edit = QLineEdit()
        dst_layout.addWidget(self.dst_edit)
        dst_btn = QPushButton("浏览...")
        dst_btn.clicked.connect(self.browse_dest)
        dst_layout.addWidget(dst_btn)
        layout.addLayout(dst_layout)

        # 提取方式
        layout.addWidget(QLabel("选择提取方式:"))
        self.mode_group = QButtonGroup(self)
        
        self.radio1 = QRadioButton("一、metadata.pegasus.txt 和 media 目录")
        self.radio1.setChecked(True)
        self.mode_group.addButton(self.radio1, 1)
        layout.addWidget(self.radio1)

        self.radio2 = QRadioButton("二、仅提取 metadata.pegasus.txt 文件")
        self.mode_group.addButton(self.radio2, 2)
        layout.addWidget(self.radio2)

        self.radio3 = QRadioButton("三、仅提取 media 目录")
        self.mode_group.addButton(self.radio3, 3)
        layout.addWidget(self.radio3)

        self.radio4 = QRadioButton("四、仅提取 launch 字段内容")
        self.mode_group.addButton(self.radio4, 4)
        layout.addWidget(self.radio4)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton("开始提取")
        self.run_btn.clicked.connect(self.start_extraction)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def browse_source(self):
        path = QFileDialog.getExistingDirectory(self, "选择来源 Roms 目录")
        if path:
            self.src_edit.setText(path)

    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "选择存放目录")
        if path:
            self.dst_edit.setText(path)

    def start_extraction(self):
        src = self.src_edit.text()
        dst = self.dst_edit.text()
        if not src or not dst:
            QMessageBox.warning(self, "警告", "请先选择来源目录和存放目录")
            return
        
        if not os.path.exists(src):
            QMessageBox.warning(self, "警告", "来源目录不存在")
            return

        mode = self.mode_group.checkedId()
        
        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = ExtractionWorker(src, dst, mode)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, current, total, text):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(text)

    def on_finished(self, success, message):
        self.run_btn.setEnabled(True)
        if success:
            QMessageBox.information(self, "成功", message)
            self.accept()
        else:
            QMessageBox.critical(self, "错误", message)
            self.progress_bar.setVisible(False)
            self.status_label.setText("")
