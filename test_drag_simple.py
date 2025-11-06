#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的拖拽测试程序
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class DragDropLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setText("拖拽文件到这里测试")
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 50px;
                text-align: center;
                font-size: 16px;
                background-color: #f0f0f0;
            }
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        print("dragEnterEvent 触发")
        if event.mimeData().hasUrls():
            print("检测到URL数据")
            event.accept()
            self.setStyleSheet("""
                QLabel {
                    border: 2px dashed #0f0;
                    border-radius: 10px;
                    padding: 50px;
                    text-align: center;
                    font-size: 16px;
                    background-color: #e0ffe0;
                }
            """)
        else:
            print("没有URL数据")
            event.ignore()
    
    def dragMoveEvent(self, event):
        print("dragMoveEvent 触发")
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        print("dragLeaveEvent 触发")
        self.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 50px;
                text-align: center;
                font-size: 16px;
                background-color: #f0f0f0;
            }
        """)
    
    def dropEvent(self, event: QDropEvent):
        print("dropEvent 触发")
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"文件路径: {file_path}")
                files.append(file_path)
            
            self.setText(f"成功拖入 {len(files)} 个文件:\n" + "\n".join(files[:5]))
            event.accept()
        else:
            event.ignore()

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拖拽测试")
        self.setGeometry(300, 300, 400, 300)
        
        # 启用窗口拖拽
        self.setAcceptDrops(True)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.drag_label = DragDropLabel()
        layout.addWidget(self.drag_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        print("主窗口 dragEnterEvent 触发")
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        print("主窗口 dropEvent 触发")
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"主窗口文件路径: {file_path}")
                files.append(file_path)
            event.accept()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
