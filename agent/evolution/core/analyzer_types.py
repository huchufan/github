"""
analyzer 模块的类型定义
"""

from typing import Protocol, Any, Dict


class IAnalyzer(Protocol):
    """
    analyzer 模块接口
    """

    def execute(self) -> Any:
        """执行主逻辑"""
        ...
