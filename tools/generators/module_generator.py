#!/usr/bin/env python3
"""
Hermes 模块代码生成器
自动生成框架、测试、文档的基础代码

设计文档: 12_设计方案落地执行指南.md
用法:
    python tools/generators/module_generator.py <framework> <module_name>
例子:
    python tools/generators/module_generator.py governance rbac
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ModuleGenerator:
    """生成 Hermes 模块的标准代码框架"""

    def __init__(self, framework: str, module_name: str):
        self.framework = framework
        self.module_name = module_name
        self.base_path = Path("agent") / framework / "core"
        self.test_path = Path("agent") / framework / "tests"

    def generate_module(self):
        """生成完整模块"""
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.test_path.mkdir(parents=True, exist_ok=True)

        # 1. 生成主模块文件
        self._generate_main_module()

        # 2. 生成测试文件
        self._generate_test_file()

        # 3. 生成类型提示文件
        self._generate_types()

        # 4. 更新 __init__.py
        self._update_init_file()

        print(f"✓ 模块生成完成: {self.framework}/{self.module_name}")

    def _generate_main_module(self):
        """生成主模块"""
        camel = self._to_camel_case(self.module_name)
        content = f'''"""
{self.framework.capitalize()} Framework - {self.module_name.capitalize()} Module

设计文档: {self.framework[0:2]}_{self.module_name}.md
创建时间: {datetime.now().isoformat()}
版本: 1.0
"""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class {camel}:
    """
    {self.module_name.upper()} 模块

    主要功能:
    - TODO: 添加功能说明

    使用示例:
        >>> instance = {camel}()
        >>> result = instance.execute()
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化模块"""
        self.config = config or {{}}
        logger.info(f"Initialized {self.module_name}")

    def execute(self, *args, **kwargs) -> Any:
        """执行主逻辑"""
        # TODO: 实现具体逻辑
        raise NotImplementedError("Subclass must implement execute()")


# 导出公共接口
__all__ = [
    '{camel}',
]
'''

        output_file = self.base_path / f"{self.module_name}.py"
        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Generated: {output_file}")

    def _generate_test_file(self):
        """生成测试文件"""
        camel = self._to_camel_case(self.module_name)
        content = f'''"""
{self.module_name} 模块测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agent.{self.framework}.core.{self.module_name} import {camel}


class Test{camel}:
    """测试 {self.module_name} 模块"""

    @pytest.fixture
    def instance(self):
        """创建实例"""
        return {camel}()

    def test_initialization(self, instance):
        """测试初始化"""
        assert instance is not None
        assert isinstance(instance.config, dict)

    def test_execute_basic(self, instance):
        """测试基本执行"""
        # TODO: 实现测试逻辑
        pass

    def test_error_handling(self, instance):
        """测试错误处理"""
        # TODO: 测试异常场景
        pass


class Test{camel}Integration:
    """集成测试"""

    def test_integration_with_framework(self):
        """测试与框架集成"""
        # TODO: 实现集成测试
        pass
'''

        output_file = self.test_path / f"test_{self.module_name}.py"
        output_file.write_text(content, encoding="utf-8")
        logger.info(f"Generated: {output_file}")

    def _generate_types(self):
        """生成类型提示文件"""
        camel = self._to_camel_case(self.module_name)
        content = f'''"""
{self.module_name} 模块的类型定义
"""

from typing import Protocol, Any, Dict


class I{camel}(Protocol):
    """
    {self.module_name} 模块接口
    """

    def execute(self) -> Any:
        """执行主逻辑"""
        ...
'''
        output_file = self.base_path / f"{self.module_name}_types.py"
        output_file.write_text(content, encoding="utf-8")

    def _update_init_file(self):
        """更新 __init__.py"""
        init_file = self.base_path / "__init__.py"
        if init_file.exists():
            content = init_file.read_text(encoding="utf-8")
        else:
            content = '"""Framework modules"""\n\n'

        camel = self._to_camel_case(self.module_name)
        import_line = f"from .{self.module_name} import {camel}\n"
        if import_line not in content:
            content += import_line

        init_file.write_text(content, encoding="utf-8")

    @staticmethod
    def _to_camel_case(snake_str: str) -> str:
        """转换蛇形命名为驼峰命名"""
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python module_generator.py <framework> <module_name>")
        print("例子: python module_generator.py governance rbac")
        sys.exit(1)

    framework = sys.argv[1]
    module_name = sys.argv[2]

    generator = ModuleGenerator(framework, module_name)
    generator.generate_module()
