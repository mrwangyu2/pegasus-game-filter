
import os
import shutil
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QRadioButton, 
                             QButtonGroup, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from core.i18n import tr
from core.theme import load_icon


from core.metadata_parser import MetadataParser

class MergeWorker(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, source_root, target_root, mode):
        super().__init__()
        self.source_root = Path(source_root)
        self.target_root = Path(target_root)
        self.mode = mode # 1: meta+media, 2: meta only, 3: media only, 4: launch only

    def run(self):
        try:
            # 判断来源目录是否符合天马G规则
            platform_dirs = MetadataParser.find_platform_directories(self.source_root)
            if not platform_dirs:
                self.finished.emit(False, "来源目录不符合天马G目录规则（未找到包含 metadata.pegasus.txt 的平台目录）")
                return

            total_platforms = len(platform_dirs)
            for i, p_dir in enumerate(platform_dirs):
                platform_name = p_dir.name
                self.progress.emit(i, total_platforms, f"正在整合平台: {platform_name}")
                
                target_platform_dir = self.target_root / platform_name
                # 如果目标平台目录不存在，则跳过或创建？根据用户需求“覆盖或替换”，通常应该已存在。
                # 但为了健壮性，如果不存在我们也创建它。
                target_platform_dir.mkdir(parents=True, exist_ok=True)

                source_meta_file = p_dir / "metadata.pegasus.txt"
                
                # 整合逻辑
                if self.mode in [1, 2, 4]:
                    if source_meta_file.exists():
                        if self.mode == 4:
                            # 仅整合 launch 字段
                            header, games = MetadataParser.parse_platform_directory(p_dir)
                            fields = MetadataParser.parse_header_fields(header)
                            launch_val = fields.get("launch", "")
                            
                            # 读取目标 metadata 保持其内容，仅替换 launch
                            target_meta_path = target_platform_dir / "metadata.pegasus.txt"
                            if target_meta_path.exists():
                                t_header, t_games = MetadataParser.parse_platform_directory(target_platform_dir)
                                t_fields = MetadataParser.parse_header_fields(t_header)
                                t_fields["launch"] = launch_val
                                # 重新构造 header
                                new_h_lines = []
                                for k, v in t_fields.items():
                                    new_h_lines.append(f"{k}: {v}")
                                new_h_str = "\n".join(new_h_lines)
                                MetadataParser.write_metadata(t_games, target_meta_path, new_h_str)
                            else:
                                # 目标不存在，直接写一个新的精简版
                                new_h = f"launch: {launch_val}" if launch_val else ""
                                MetadataParser.write_metadata(games, target_meta_path, new_h)
                        else:
                            # 覆盖 metadata.pegasus.txt
                            shutil.copy2(source_meta_file, target_platform_dir / "metadata.pegasus.txt")

                if self.mode in [1, 3]:
                    # 整合 media
                    source_media_dir = p_dir / "media"
                    if source_media_dir.exists():
                        target_media_dir = target_platform_dir / "media"
                        target_media_dir.mkdir(parents=True, exist_ok=True)
                        
                        # 递归拷贝 media 目录，覆盖目标
                        for root, dirs, files in os.walk(source_media_dir):
                            rel_path = Path(root).relative_to(source_media_dir)
                            t_root = target_media_dir / rel_path
                            t_root.mkdir(parents=True, exist_ok=True)
                            
                            for f in files:
                                if Path(f).suffix.lower() in ['.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mkv']:
                                    shutil.copy2(Path(root) / f, t_root / f)

            self.finished.emit(True, f"整合完成！共处理 {total_platforms} 个平台。")
        except Exception as e:
            self.finished.emit(False, f"整合过程中发生错误: {str(e)}")

class MetadataMergeDialog(QDialog):
    def __init__(self, default_target="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("整合元数据工具")
        icon_path = Path(__file__).parent.absolute() / "icon" / "pegasus.ico"
        self.setWindowIcon(load_icon(icon_path))
        self.resize(500, 380)



        self.init_ui(default_target)

    def init_ui(self, default_target):
        layout = QVBoxLayout(self)

        # 来源目录（即之前提取出的目录）
        layout.addWidget(QLabel("来源整合目录 (需符合天马G Roms 规则):"))
        src_layout = QHBoxLayout()
        self.src_edit = QLineEdit()
        src_layout.addWidget(self.src_edit)
        src_btn = QPushButton("浏览...")
        src_btn.clicked.connect(self.browse_source)
        src_layout.addWidget(src_btn)
        layout.addLayout(src_layout)

        # 目标目录（被整合目录，默认为项目路径）
        layout.addWidget(QLabel("目标整合目录 (被覆盖的目录):"))
        dst_layout = QHBoxLayout()
        self.dst_edit = QLineEdit(default_target)
        dst_layout.addWidget(self.dst_edit)
        dst_btn = QPushButton("浏览...")
        dst_btn.clicked.connect(self.browse_dest)
        dst_layout.addWidget(dst_btn)
        layout.addLayout(dst_layout)

        # 整合方式
        layout.addWidget(QLabel("选择整合方式 (参考提取元数据):"))
        self.mode_group = QButtonGroup(self)
        
        self.radio1 = QRadioButton("一、metadata.pegasus.txt 和 media 目录")
        self.radio1.setChecked(True)
        self.mode_group.addButton(self.radio1, 1)
        layout.addWidget(self.radio1)

        self.radio2 = QRadioButton("二、仅整合 metadata.pegasus.txt 文件")
        self.mode_group.addButton(self.radio2, 2)
        layout.addWidget(self.radio2)

        self.radio3 = QRadioButton("三、仅整合 media 目录")
        self.mode_group.addButton(self.radio3, 3)
        layout.addWidget(self.radio3)

        self.radio4 = QRadioButton("四、仅整合 launch 字段内容")
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
        self.run_btn = QPushButton("开始整合")
        self.run_btn.clicked.connect(self.start_merge)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

    def browse_source(self):
        path = QFileDialog.getExistingDirectory(self, "选择来源整合目录")
        if path:
            self.src_edit.setText(path)

    def browse_dest(self):
        path = QFileDialog.getExistingDirectory(self, "选择目标整合目录")
        if path:
            self.dst_edit.setText(path)

    def start_merge(self):
        src = self.src_edit.text()
        dst = self.dst_edit.text()
        if not src or not dst:
            QMessageBox.warning(self, "警告", "请先选择来源目录和目标目录")
            return
        
        if not os.path.exists(src):
            QMessageBox.warning(self, "警告", "来源目录不存在")
            return

        mode = self.mode_group.checkedId()
        
        # 二次确认
        reply = QMessageBox.question(
            self, "确认整合", 
            "整合操作将覆盖目标目录中的内容，是否继续？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        self.run_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = MergeWorker(src, dst, mode)
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
