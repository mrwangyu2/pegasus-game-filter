"""
游戏管理模块（重构版）
"""

import shutil
from pathlib import Path
from typing import List, Dict
from core.metadata_parser import Game, MetadataParser
from core.task_system import TaskQueue, TaskType, TaskStatus


class GameManager:
    """游戏管理器，负责游戏的增删改查"""
    
    def __init__(self, roms_root: Path):
        self.roms_root = roms_root
        self.platforms: Dict[str, List[Game]] = {}
        self.headers: Dict[str, str] = {}  # 存储各平台的 Header
        self.task_queue = TaskQueue()
    
    def load_all_platforms(self) -> bool:
        """加载所有平台的游戏"""
        self.platforms.clear()
        self.headers.clear()
        platform_dirs = MetadataParser.find_platform_directories(self.roms_root)
        
        for platform_path in platform_dirs:
            platform_name = platform_path.name
            header, games = MetadataParser.parse_platform_directory(platform_path)
            self.platforms[platform_name] = games
            self.headers[platform_name] = header
        
        return True
    
    def get_all_games(self) -> List[Game]:
        """获取所有游戏"""
        all_games = []
        for games in self.platforms.values():
            all_games.extend(games)
        return all_games
    
    def get_platform_games(self, platform: str) -> List[Game]:
        """获取指定平台的游戏"""
        return self.platforms.get(platform, [])
    
    def get_platform_names(self) -> List[str]:
        """获取Roms目录下的所有平台目录名称"""
        try:
            return sorted([item.name for item in self.roms_root.iterdir() if item.is_dir()])
        except FileNotFoundError:
            return []
    
    def has_game(self, game: Game) -> bool:
        """判断是否已存在相同游戏（按平台+文件名或名称匹配）"""
        platform_games = self.platforms.get(game.platform, [])
        for g in platform_games:
            if g.file == game.file or g.game == game.game:
                return True
        return False
    
    def execute_tasks(self) -> dict:
        """执行任务队列中的所有任务"""
        results = {
            'total': len(self.task_queue.tasks),
            'success': 0,
            'failed': 0
        }
        
        for task in self.task_queue.tasks:
            task.status = TaskStatus.RUNNING
            self.task_queue.log(f"开始执行: {task}", "info")
            
            try:
                if task.task_type == TaskType.ADD:
                    self._execute_add_task(task)
                elif task.task_type == TaskType.REMOVE:
                    self._execute_remove_task(task)
                elif task.task_type == TaskType.UPDATE:
                    self._execute_update_task(task)
                
                task.status = TaskStatus.SUCCESS
                results['success'] += 1
                self.task_queue.log(f"执行成功: {task.game.game}", "success")
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                results['failed'] += 1
                self.task_queue.log(f"执行失败: {task.game.game} - {e}", "error")
        
        # 清空已执行的任务
        self.task_queue.clear()
        return results
    
    def _execute_add_task(self, task):
        """执行添加任务"""
        source_game = task.game
        platform = source_game.platform
        
        # 确保平台目录存在
        platform_path = self.roms_root / platform
        platform_path.mkdir(parents=True, exist_ok=True)
        
        # 创建media目录（使用文件名去除扩展名作为目录名）
        media_dir_name = Path(source_game.file).stem or source_game.game
        media_dir = platform_path / "media" / media_dir_name
        media_dir.mkdir(parents=True, exist_ok=True)
        
        # 复制游戏文件
        source_file = source_game.platform_path / source_game.file
        dest_file = platform_path / source_game.file
        if source_file.exists():
            shutil.copy2(source_file, dest_file)
            self.task_queue.log(f"  复制游戏文件: {source_game.file}", "info")
        
        # 复制logo
        logo_path = source_game.get_logo_path()
        if logo_path and logo_path.exists():
            dest_logo = media_dir / logo_path.name
            shutil.copy2(logo_path, dest_logo)
            self.task_queue.log(f"  复制logo: {logo_path.name}", "info")
        
        # 复制封面
        boxfront_path = source_game.get_boxfront_path()
        if boxfront_path and boxfront_path.exists():
            dest_boxfront = media_dir / boxfront_path.name
            shutil.copy2(boxfront_path, dest_boxfront)
            self.task_queue.log(f"  复制封面: {boxfront_path.name}", "info")
        
        # 复制视频
        video_path = source_game.get_video_path()
        if video_path and video_path.exists():
            dest_video = media_dir / video_path.name
            shutil.copy2(video_path, dest_video)
            self.task_queue.log(f"  复制视频: {video_path.name}", "info")
        
        # 处理 Header 合并：如果项目 Header 缺失特定字段，从来源复制
        project_header = self.headers.get(platform, "")
        try:
            source_header, _ = MetadataParser.parse_platform_directory(source_game.platform_path)
            merged_header = MetadataParser.merge_header_fields(
                project_header, 
                source_header, 
                ["collection", "sort-by", "extensions", "launch"],
                platform
            )
            if merged_header != project_header:
                self.headers[platform] = merged_header
                self.task_queue.log(f"  合并平台配置 (Header)", "info")
        except Exception as e:
            self.task_queue.log(f"  合并平台配置失败: {e}", "warning")

        # 更新元数据文件
        if platform not in self.platforms:
            self.platforms[platform] = []
        
        # 创建新游戏对象，去重后插入
        new_game = self._create_game_copy(source_game, platform_path)
        self._upsert_platform_game(platform, new_game)
        
        # 写入元数据
        metadata_file = platform_path / "metadata.pegasus.txt"
        header = self.headers.get(platform, "")
        MetadataParser.write_metadata(self.platforms[platform], metadata_file, header)
    
    def _execute_remove_task(self, task):
        """执行删除任务"""
        game = task.game
        platform = game.platform
        platform_path = self.roms_root / platform
        
        # 删除游戏文件
        game_file = platform_path / game.file
        if game_file.exists():
            game_file.unlink()
            self.task_queue.log(f"  删除游戏文件: {game.file}", "info")
        
        # 删除media目录（使用文件名去除扩展名）
        media_dir_name = Path(game.file).stem or game.game
        media_dir = platform_path / "media" / media_dir_name
        if media_dir.exists():
            shutil.rmtree(media_dir)
            self.task_queue.log(f"  删除media目录: {media_dir_name}", "info")
        
        # 从列表中移除
        if platform in self.platforms:
            self.platforms[platform] = [
                g for g in self.platforms[platform] 
                if g.game != game.game
            ]
            
            # 更新元数据
            metadata_file = platform_path / "metadata.pegasus.txt"
            header = self.headers.get(platform, "")
            MetadataParser.write_metadata(self.platforms[platform], metadata_file, header)
    
    def _execute_update_task(self, task):
        """执行更新任务"""
        game = task.game
        platform = game.platform
        platform_path = self.roms_root / platform
        
        # 更新元数据文件
        if platform in self.platforms:
            metadata_file = platform_path / "metadata.pegasus.txt"
            header = self.headers.get(platform, "")
            MetadataParser.write_metadata(self.platforms[platform], metadata_file, header)
            self.task_queue.log(f"  更新元数据", "info")
    
    def _create_game_copy(self, source_game: Game, platform_path: Path) -> Game:
        """创建游戏副本"""
        new_game = Game()
        new_game.game = source_game.game
        new_game.file = source_game.file
        new_game.sort_by = source_game.sort_by
        new_game.developer = source_game.developer
        new_game.description = source_game.description
        new_game.platform = source_game.platform
        new_game.platform_path = platform_path
        return new_game

    def _upsert_platform_game(self, platform: str, new_game: Game):
        """在平台列表中去重插入/更新游戏，按文件或名称匹配"""
        if platform not in self.platforms:
            self.platforms[platform] = []
        games = self.platforms[platform]
        replaced = False
        for idx, g in enumerate(games):
            if g.file == new_game.file or g.game == new_game.game:
                games[idx] = new_game
                replaced = True
                break
        if not replaced:
            games.append(new_game)
    
    def search_games(self, keyword: str) -> List[Game]:
        """搜索游戏"""
        keyword = keyword.lower()
        results = []
        
        for games in self.platforms.values():
            for game in games:
                if (keyword in game.game.lower() or
                    keyword in game.platform.lower() or
                    keyword in game.developer.lower()):
                    results.append(game)
        
        return results
