"""
天马G元数据解析模块（重构版）
"""

from pathlib import Path
from typing import List, Dict, Optional, Any


class Game:
    """游戏元数据类"""
    
    def __init__(self):
        self.game: str = ""  # 游戏名称（用于显示）
        self.file: str = ""  # 游戏文件名
        self.sort_by: str = ""  # 排序
        self.developer: str = ""  # 开发者
        self.description: str = ""  # 游戏描述
        self.platform: str = ""  # 平台名称（从目录结构获取）
        self.platform_path: Optional[Path] = None  # 平台目录路径

    @property
    def is_file_missing(self) -> bool:
        """检查元数据中指定的游戏文件在磁盘上是否存在"""
        if self.platform_path and self.file:
            # 处理可能的路径分隔符
            file_path = self.platform_path / self.file
            return not file_path.exists()
        return True
    
    def _media_key(self) -> Optional[str]:
        """media目录使用的基名，优先用file去掉扩展名"""
        if self.file:
            stem = Path(self.file).stem
            if stem:
                return stem
        return self.game or None
        
    def get_logo_path(self) -> Optional[Path]:
        """获取logo图片路径，media子目录按文件名去扩展"""
        if not self.platform_path:
            return None
        media_key = self._media_key()
        if not media_key:
            return None
        logo_dir = self.platform_path / "media" / media_key
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            logo_file = logo_dir / f"logo{ext}"
            if logo_file.exists():
                return logo_file
        return None
    
    def get_boxfront_path(self) -> Optional[Path]:
        """获取封面图片路径"""
        if not self.platform_path:
            return None
        media_key = self._media_key()
        if not media_key:
            return None
        boxfront_dir = self.platform_path / "media" / media_key
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            boxfront_file = boxfront_dir / f"boxFront{ext}"
            if boxfront_file.exists():
                return boxfront_file
        return None
    
    def get_video_path(self) -> Optional[Path]:
        """获取视频路径"""
        if not self.platform_path:
            return None
        media_key = self._media_key()
        if not media_key:
            return None
        video_dir = self.platform_path / "media" / media_key
        for ext in ['.mp4', '.avi', '.mkv', '.mov']:
            video_file = video_dir / f"video{ext}"
            if video_file.exists():
                return video_file
        return None


class MetadataParser:
    """天马G metadata.pegasus.txt 解析器"""
    
    SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mkv', '.mov'}
    
    @staticmethod
    def parse_platform_directory(platform_path: Path) -> tuple:
        """解析平台目录，返回 (header, 游戏列表)"""
        metadata_file = platform_path / "metadata.pegasus.txt"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"找不到元数据文件: {metadata_file}")
        
        media_dir = platform_path / "media"
        if not media_dir.exists():
            raise FileNotFoundError(f"找不到media目录: {media_dir}")
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 分离 Header 和 Game 块
            # 找到第一个 "game:" 出现的位置
            import re
            # 改进正则：确保匹配的是行首的 game: 字段，防止匹配到 description 里的内容
            match = re.search(r'^game\s*:', content, re.MULTILINE | re.IGNORECASE)
            if match:
                header = content[:match.start()].strip()
                game_content = content[match.start():]
            else:
                header = content.strip()
                game_content = ""

            games = []
            game_blocks = game_content.split('\n\n')
            platform_name = platform_path.name
            
            for block in game_blocks:
                block = block.strip()
                if not block or block.startswith('#'):
                    continue
                
                game = MetadataParser._parse_game_block(block, platform_path, platform_name)
                if game:
                    games.append(game)
            
            return header, games
        except Exception as e:
            raise Exception(f"解析元数据文件失败: {e}")
    
    @staticmethod
    def _parse_game_block(block: str, platform_path: Path, platform_name: str) -> Optional[Game]:
        """解析单个游戏块"""
        import re
        game = Game()
        game.platform = platform_name
        game.platform_path = platform_path
        
        # 使用正则表达式匹配字段，支持多行延续
        pattern = r'^([a-zA-Z0-9_-]+)\s*:(.*?)(?=\n[a-zA-Z0-9_-]+\s*:|\Z)'
        matches = re.finditer(pattern, block, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        field_data = {}
        for m in matches:
            key = m.group(1).lower()
            value = m.group(2).strip()
            # 合并多行并清理前导空格
            val_lines = [line.strip() for line in value.splitlines()]
            field_data[key] = '\n'.join(val_lines)
            
        if 'game' in field_data:
            game.game = field_data['game']
        
        if 'file' in field_data:
            value = field_data['file']
            # 去除包裹的引号
            if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                value = value[1:-1].strip()
            game.file = value
            
        if 'sort-by' in field_data:
            game.sort_by = field_data['sort-by']
            
        if 'developer' in field_data:
            game.developer = field_data['developer']
            
        if 'description' in field_data:
            game.description = field_data['description']
        
        return game if game.game and game.file else None
    
    @staticmethod
    def parse_header_fields(header_text: str) -> Dict[str, str]:
        """解析 Header 中的字段，支持多行延续字段 (如 launch)"""
        import re
        fields = {}
        
        # 预处理：去除纯注释行，保持空行（空行可能在多行字段中）
        lines = []
        for line in header_text.splitlines():
            if line.strip().startswith('#'):
                continue
            lines.append(line)
        clean_text = '\n'.join(lines)
        
        # 改进正则：
        # 1. 匹配行首的 key:
        # 2. 内容 (.*?) 非贪婪匹配
        # 3. 停止条件：遇到 下一个行首的 key: (前面可能有多个换行符) 或者 字符串结束
        pattern = r'^([a-zA-Z0-9_-]+)\s*:(.*?)(?=\n+\s*[a-zA-Z0-9_-]+\s*:|\Z)'
        matches = re.finditer(pattern, clean_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        for m in matches:
            key = m.group(1).lower()
            value = m.group(2).strip()
            
            # 处理多行延续：合并行并清理多余空格
            val_lines = [line.strip() for line in value.splitlines()]
            fields[key] = '\n'.join(val_lines)
            
        return fields

    @staticmethod
    def merge_header_fields(target_header: str, source_header: str, field_names: List[str], platform_name: str = "") -> str:
        """合并 Header 字段：确保 target 中包含 field_names 中的所有字段"""
        target_fields = MetadataParser.parse_header_fields(target_header)
        source_fields = MetadataParser.parse_header_fields(source_header)
        
        # 合并所有字段
        merged_fields = target_fields.copy()
        for field in field_names:
            f_lower = field.lower()
            if f_lower not in merged_fields:
                if f_lower in source_fields:
                    merged_fields[f_lower] = source_fields[f_lower]
                else:
                    # 如果来源也没有，给个默认值
                    if f_lower == "collection":
                        merged_fields[f_lower] = platform_name or "Unknown Collection"
                    else:
                        merged_fields[f_lower] = ""
        
        # 构建新的 header 字符串
        final_lines = []
        processed_keys = set()
        
        # 为了美观，先按 field_names 的顺序排放核心字段
        for field in field_names:
            f_lower = field.lower()
            if f_lower in merged_fields:
                value = merged_fields[f_lower]
                if '\n' in value:
                    lines = value.split('\n')
                    formatted = lines[0]
                    for l in lines[1:]:
                        formatted += '\n  ' + l
                    final_lines.append(f"{field}: {formatted}")
                else:
                    final_lines.append(f"{field}: {value}")
                processed_keys.add(f_lower)
        
        # 再添加其他字段
        for key, value in merged_fields.items():
            if key not in processed_keys:
                # 尝试找回原始的大小写（如果有的话，这里简单处理）
                if '\n' in value:
                    lines = value.split('\n')
                    formatted = lines[0]
                    for l in lines[1:]:
                        formatted += '\n  ' + l
                    final_lines.append(f"{key}: {formatted}")
                else:
                    final_lines.append(f"{key}: {value}")
        
        return '\n'.join(final_lines)

    @staticmethod
    def write_metadata(games: List[Game], output_file: Path, header: str = "") -> bool:
        """写入元数据到文件"""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                if header:
                    f.write(header)
                    f.write('\n\n')
                
                for i, game in enumerate(games):
                    if i > 0:
                        f.write('\n\n')
                    
                    f.write(f'game: {game.game}\n')
                    f.write(f'file: {game.file}\n')
                    if game.sort_by:
                        f.write(f'sort-by: {game.sort_by}\n')
                    if game.developer:
                        f.write(f'developer: {game.developer}\n')
                    if game.description:
                        # 处理描述的多行缩进
                        desc = game.description.strip()
                        if '\n' in desc:
                            desc = desc.replace('\n', '\n  ')
                        f.write(f'description: {desc}\n')
            
            return True
        except Exception as e:
            raise Exception(f"写入元数据失败: {e}")
    
    @staticmethod
    def find_platform_directories(roms_root: Path) -> List[Path]:
        """查找Roms根目录下的所有平台目录"""
        platform_dirs = []
        
        for item in roms_root.iterdir():
            if item.is_dir():
                metadata_file = item / "metadata.pegasus.txt"
                media_dir = item / "media"
                if metadata_file.exists() and media_dir.exists():
                    platform_dirs.append(item)
        
        return platform_dirs
