"""
任务系统模块
"""

from enum import Enum
from typing import List, Callable
from dataclasses import dataclass
from core.metadata_parser import Game


class TaskType(Enum):
    """任务类型枚举"""
    ADD = "添加"
    REMOVE = "删除"
    UPDATE = "更新"


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "待执行"
    SUCCESS = "成功"
    FAILED = "失败"
    RUNNING = "执行中"


@dataclass
class Task:
    """任务数据类"""
    task_type: TaskType
    game: Game
    status: TaskStatus = TaskStatus.PENDING
    error_message: str = ""
    
    def __str__(self):
        return f"[{self.task_type.value}] {self.game.game}"


class TaskQueue:
    """任务队列"""
    
    def __init__(self):
        self.tasks: List[Task] = []
        self.log_callback: Callable = None
    
    def add_task(self, task_type: TaskType, game: Game):
        """添加任务"""
        # 检查是否已存在相同游戏的任务
        for task in self.tasks:
            if task.game.game == game.game and task.game.platform == game.platform:
                # 更新任务类型
                task.task_type = task_type
                task.status = TaskStatus.PENDING
                task.error_message = ""
                return
        
        # 添加新任务
        task = Task(task_type=task_type, game=game)
        self.tasks.append(task)
    
    def remove_task(self, game: Game):
        """移除任务"""
        self.tasks = [t for t in self.tasks 
                      if not (t.game.game == game.game and t.game.platform == game.platform)]
    
    def clear(self):
        """清空任务队列"""
        self.tasks.clear()
    
    def get_task_count(self) -> dict:
        """获取任务统计"""
        count = {
            TaskType.ADD: 0,
            TaskType.REMOVE: 0,
            TaskType.UPDATE: 0
        }
        for task in self.tasks:
            count[task.task_type] += 1
        return count
    
    def has_pending_tasks(self) -> bool:
        """是否有待执行的任务"""
        return len(self.tasks) > 0
    
    def set_log_callback(self, callback: Callable):
        """设置日志回调函数"""
        self.log_callback = callback
    
    def log(self, message: str, level: str = "info"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)
