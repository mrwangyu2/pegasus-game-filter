"""
项目管理模块
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any


class Project:
    """项目类，管理项目信息和ROM目录"""
    
    def __init__(self, name: str = "", roms_path: str = "", source_path: str = "", pegasus_path: str = ""):
        self.name = name
        self.roms_path = Path(roms_path) if roms_path else None
        self.source_path = Path(source_path) if source_path else None
        self.pegasus_path = Path(pegasus_path) if pegasus_path else None
        self.project_file = None
    
    def save(self, filepath: Path) -> bool:
        """保存项目到JSON文件"""
        try:
            data = {
                "name": self.name,
                "roms_path": str(self.roms_path) if self.roms_path else "",
                "source_path": str(self.source_path) if self.source_path else "",
                "pegasus_path": str(self.pegasus_path) if self.pegasus_path else ""
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.project_file = filepath
            return True
        except Exception as e:
            print(f"保存项目失败: {e}")
            return False
    
    @classmethod
    def load(cls, filepath: Path) -> Optional['Project']:
        """从JSON文件加载项目"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            project = cls(
                name=data.get("name", ""),
                roms_path=data.get("roms_path", ""),
                source_path=data.get("source_path", ""),
                pegasus_path=data.get("pegasus_path", "")
            )
            project.project_file = filepath
            return project
        except Exception as e:
            print(f"加载项目失败: {e}")
            return None
    
    def is_valid(self) -> bool:
        """检查项目是否有效"""
        return bool(self.name and self.roms_path and self.source_path)
