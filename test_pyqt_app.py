#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyQt6批量重命名工具测试脚本
"""

import os
import tempfile
from pathlib import Path

def create_test_files():
    """创建测试文件"""
    # 创建临时目录
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文件
    test_files = [
        "洗衣店偷衣服-1.jpg",
        "洗衣店偷衣服-2.png", 
        "插队的补偿-1.mp4",
        "插队的补偿-4.avi",
        "无语言偷看1-2.txt"
    ]
    
    for filename in test_files:
        file_path = test_dir / filename
        file_path.write_text(f"测试文件: {filename}")
        print(f"创建测试文件: {file_path}")
    
    print(f"\n测试文件已创建在: {test_dir.absolute()}")
    print("您可以将这些文件拖拽到PyQt应用中进行测试")

if __name__ == "__main__":
    create_test_files()
