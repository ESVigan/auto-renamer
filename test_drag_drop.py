#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的PyQt6拖拽测试程序
"""

import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class DragDropTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 拖拽测试")
        self.setGeometry(100, 100, 400, 300)
        
        # 启用拖拽
        self.setAcceptDrops(True)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        self.label = QLabel("拖拽文件到这里测试")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
                background-color: #f0f0f0;
            }
        """)
        
        layout.addWidget(self.label)
        
        self.result_label = QLabel("等待拖拽...")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.result_label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        print("拖拽进入事件触发")
        if event.mimeData().hasUrls():
            print("检测到URL数据，接受拖拽")
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #0078d7;
                    border-radius: 10px;
                    padding: 20px;
                    font-size: 16px;
                    background-color: #e6f2fa;
                    color: #0078d7;
                }
            """)
            self.label.setText("松开鼠标放下文件")
        else:
            print("没有URL数据，忽略拖拽")
            event.ignore()
    
    def dragMoveEvent(self, event):
        print("拖拽移动事件触发")
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        print("拖拽离开事件触发")
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
                background-color: #f0f0f0;
            }
        """)
        self.label.setText("拖拽文件到这里测试")
    
    def dropEvent(self, event: QDropEvent):
        print("拖拽放下事件触发")
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                print(f"获取到文件: {file_path}")
                if os.path.exists(file_path):
                    files.append(file_path)
            
            if files:
                self.result_label.setText(f"成功接收 {len(files)} 个文件:\n" + "\n".join(files[:5]))
                if len(files) > 5:
                    self.result_label.setText(self.result_label.text() + f"\n... 还有 {len(files) - 5} 个文件")
            else:
                self.result_label.setText("没有有效的文件")
            
            event.acceptProposedAction()
        else:
            event.ignore()
        
        # 恢复样式
        self.dragLeaveEvent(None)

def main():
    app = QApplication(sys.argv)
    window = DragDropTest()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
