#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文件重命名工具 - PyQt6版本
现代化界面,专业级用户体验
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, 
    QTableWidgetItem, QTextEdit, QFileDialog, QMessageBox, 
    QSplitter, QGroupBox, QHeaderView, QCheckBox, QFrame,
    QScrollArea, QTabWidget, QProgressBar, QStatusBar, QListWidget,
    QDialog, QDialogButtonBox, QMenu
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QMimeData, QUrl, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QDragEnterEvent, 
    QDropEvent, QAction
)


class MemoryBankDialog(QDialog):
    """记忆库选择对话框"""
    
    def __init__(self, title, data_list, parent=None):
        super().__init__(parent)
        self.data_list = sorted(data_list)
        self.selected_value = None
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(450, 350)
        
        # 增强的对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #ffffff;
                border-radius: 12px;
            }
            QListWidget {
                background-color: rgba(30, 30, 46, 0.95);
                border: 2px solid #0f3460;
                border-radius: 10px;
                color: #e8e8e8;
                font-size: 12px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 12px 15px;
                border-bottom: 1px solid rgba(15, 52, 96, 0.3);
                border-radius: 6px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a085, stop:1 #1abc9c);
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(22, 160, 133, 0.2);
                border-left: 3px solid #1abc9c;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 说明标签
        info_label = QLabel("💡 双击选择项目,或选中后点击确定")
        info_label.setStyleSheet("""
            color: #95a5a6;
            font-size: 11px;
            padding: 10px;
            background-color: rgba(52, 73, 94, 0.3);
            border-radius: 6px;
            border-left: 3px solid #1abc9c;
        """)
        layout.addWidget(info_label)
        
        # 列表控件
        self.list_widget = QListWidget()
        self.list_widget.addItems(self.data_list)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept_selection)
        button_box.rejected.connect(self.reject)
        
        # 增强的按钮样式
        button_box.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a085, stop:1 #1abc9c);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 11px;
                min-width: 90px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #138d75, stop:1 #17a589);
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0e6655, stop:1 #117a65);
            }
        """)
        
        layout.addWidget(button_box)
    
    def on_item_double_clicked(self, item):
        """处理双击事件"""
        self.selected_value = item.text()
        self.accept()
    
    def accept_selection(self):
        """确认选择"""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_value = current_item.text()
            self.accept()
        else:
            QMessageBox.warning(self, "警告", "请先选择一个项目")
    
    def get_selected_value(self):
        """获取选中的值"""
        return self.selected_value


class ModernBatchRenamerApp(QMainWindow):
    """现代化批量重命名工具主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 配置文件路径
        self.window_config_file = "window_config.json"
        self.auto_config_file = "auto_config.json"
        self.memory_bank_file = "memory_bank.json"
        
        # 数据存储
        self.files_to_rename: List[Tuple[str, str]] = []
        self.last_renames: List[Tuple[str, str]] = []
        self.project_codes: Dict[str, str] = {}
        self.diff_rules: Dict[str, Tuple[str, str, str]] = {}
        
        # 记忆库存储
        self.memory_bank = {
            "version_names": set(),
            "abbreviations": set(),
            "languages": set()
        }
        
        # 初始化界面
        self.init_ui()
        self.setup_styles()
        self.load_default_data()
        self.load_window_config()
        self.load_auto_config()
        
        # 设置拖拽支持
        self.setAcceptDrops(True)
        
        # 加载记忆库
        self.load_memory_bank()
        
        # 设置表格右键菜单
        self.rules_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_table.customContextMenuRequested.connect(self.show_context_menu)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("LPX的批量命名小工具 v0.1")
        self.setMinimumSize(1200, 900)
        self.resize(1400, 1000)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # 创建标题栏
        self.create_header(main_layout)
        
        # 创建主要内容区域
        self.create_main_content(main_layout)
        
        # 创建状态栏
        self.create_status_bar()

    def create_header(self, parent_layout):
        """创建标题栏"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # 标题
        title_label = QLabel("🚀 智能批量重命名工具")
        title_label.setObjectName("titleLabel")
        title_font = QFont("Microsoft YaHei UI", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        
        # 版本标签
        version_label = QLabel("v0.1")
        version_label.setObjectName("versionLabel")
        version_font = QFont("Microsoft YaHei UI", 10)
        version_label.setFont(version_font)
        
        # 配置按钮
        config_layout = QHBoxLayout()
        config_layout.setSpacing(12)
        
        save_btn = QPushButton("💾 保存配置")
        save_btn.setObjectName("accentButton")
        save_btn.clicked.connect(self.save_all_config)
        
        load_btn = QPushButton("📂 加载配置")
        load_btn.setObjectName("secondaryButton")
        load_btn.clicked.connect(self.load_config_file)
        
        config_layout.addWidget(save_btn)
        config_layout.addWidget(load_btn)
        
        # 布局
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(version_label)
        header_layout.addSpacing(30)
        header_layout.addLayout(config_layout)
        
        parent_layout.addWidget(header_frame)

    def create_main_content(self, parent_layout):
        """创建主要内容区域"""
        # 使用分割器创建左右布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        
        # 左侧配置面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧文件处理面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setSizes([420, 800])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        parent_layout.addWidget(splitter)

    def create_left_panel(self):
        """创建左侧配置面板"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(18)
        
        # 全局设置
        global_group = self.create_global_settings()
        left_layout.addWidget(global_group)
        
        # 项目代号配置
        project_group = self.create_project_codes_section()
        left_layout.addWidget(project_group)
        
        # 差分规则配置
        rules_group = self.create_diff_rules_section()
        left_layout.addWidget(rules_group)
        
        left_layout.addStretch()
        return left_widget

    def create_right_panel(self):
        """创建右侧文件处理面板"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(18)
        
        # 文件列表区域
        file_group = self.create_file_section()
        right_layout.addWidget(file_group)
        
        # 执行区域
        execute_group = self.create_execute_section()
        right_layout.addWidget(execute_group)
        
        return right_widget

    def create_global_settings(self):
        """创建全局设置区域"""
        group = QGroupBox("🌐 全局设置")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(12)
        
        # 日期设置
        date_layout = QHBoxLayout()
        date_label = QLabel("日期 (YYMMDD):")
        date_label.setMinimumWidth(120)
        date_label.setStyleSheet("font-weight: 600; color: #ecf0f1;")
        
        self.date_edit = QLineEdit("251013")
        self.date_edit.setObjectName("modernLineEdit")
        self.date_edit.setMaximumWidth(160)
        self.date_edit.textChanged.connect(self.update_preview)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        return group

    def create_project_codes_section(self):
        """创建项目代号配置区域"""
        group = QGroupBox("📋 项目代号配置")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(12)
        
        # 说明文字
        help_label = QLabel("💡 直接在表格中编辑,支持多行配置")
        help_label.setObjectName("helpLabel")
        layout.addWidget(help_label)
        
        # 项目代号表格
        self.project_table = QTableWidget(0, 2)
        self.project_table.setObjectName("modernTable")
        self.project_table.setHorizontalHeaderLabels(["项目代号", "完整项目名"])
        
        # 设置表格属性
        header = self.project_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        self.project_table.setMaximumHeight(200)
        self.project_table.itemChanged.connect(self.update_project_config)
        
        layout.addWidget(self.project_table)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_project_btn = QPushButton("➕ 添加行")
        add_project_btn.setObjectName("accentButton")
        add_project_btn.clicked.connect(self.add_project_row)
        
        remove_project_btn = QPushButton("➖ 删除行")
        remove_project_btn.setObjectName("warningButton")
        remove_project_btn.clicked.connect(self.remove_project_row)
        
        btn_layout.addWidget(add_project_btn)
        btn_layout.addWidget(remove_project_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        return group

    def create_diff_rules_section(self):
        """创建差分规则配置区域"""
        group = QGroupBox("⚙️ 差分规则配置")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(12)
        
        # 说明文字
        help_label = QLabel("💡 直接在表格中编辑,所有项目共用。右键版本名全称、版本名缩写、语言列可使用记忆库功能")
        help_label.setObjectName("helpLabel")
        layout.addWidget(help_label)
        
        # 差分规则表格
        self.rules_table = QTableWidget(0, 4)
        self.rules_table.setObjectName("modernTable")
        self.rules_table.setHorizontalHeaderLabels(["差分号", "版本名全称", "版本名缩写", "语言"])
        
        # 设置表格属性
        header = self.rules_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.rules_table.setMaximumHeight(250)
        self.rules_table.itemChanged.connect(self.update_rule_config)
        
        layout.addWidget(self.rules_table)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_rule_btn = QPushButton("➕ 添加行")
        add_rule_btn.setObjectName("accentButton")
        add_rule_btn.clicked.connect(self.add_rule_row)
        
        remove_rule_btn = QPushButton("➖ 删除行")
        remove_rule_btn.setObjectName("warningButton")
        remove_rule_btn.clicked.connect(self.remove_rule_row)
        
        btn_layout.addWidget(add_rule_btn)
        btn_layout.addWidget(remove_rule_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        return group

    def create_file_section(self):
        """创建文件处理区域"""
        group = QGroupBox("📁 文件列表与预览")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        # 文件操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        add_files_btn = QPushButton("📁 添加文件")
        add_files_btn.setObjectName("accentButton")
        add_files_btn.clicked.connect(self.add_files)
        
        add_folder_btn = QPushButton("📂 添加文件夹")
        add_folder_btn.setObjectName("accentButton")
        add_folder_btn.clicked.connect(self.add_folder)
        
        refresh_btn = QPushButton("🔄 刷新识别")
        refresh_btn.setObjectName("secondaryButton")
        refresh_btn.clicked.connect(self.refresh_file_recognition)
        
        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setObjectName("warningButton")
        clear_btn.clicked.connect(self.clear_file_list)
        
        btn_layout.addWidget(add_files_btn)
        btn_layout.addWidget(add_folder_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 文件列表表格
        self.file_table = QTableWidget(0, 3)
        self.file_table.setObjectName("modernTable")
        self.file_table.setHorizontalHeaderLabels(["原始文件名", "新文件名", "状态"])
        
        # 设置表格属性
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.file_table)
        
        # 拖拽提示
        drop_label = QLabel("💡 支持拖拽文件到此处")
        drop_label.setObjectName("helpLabel")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(drop_label)
        
        return group

    def create_execute_section(self):
        """创建执行区域"""
        group = QGroupBox("🚀 执行与历史")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(20, 25, 20, 20)
        layout.setSpacing(15)
        
        # 执行按钮
        self.execute_btn = QPushButton("🚀 开始执行重命名")
        self.execute_btn.setObjectName("executeButton")
        self.execute_btn.setMinimumHeight(55)
        self.execute_btn.clicked.connect(self.execute_rename)
        layout.addWidget(self.execute_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("modernProgressBar")
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(8)
        layout.addWidget(self.progress_bar)
        
        # 历史记录
        history_label = QLabel("📜 操作历史:")
        history_label.setObjectName("sectionLabel")
        layout.addWidget(history_label)
        
        self.history_text = QTextEdit()
        self.history_text.setObjectName("modernTextEdit")
        self.history_text.setMaximumHeight(150)
        self.history_text.setReadOnly(True)
        layout.addWidget(self.history_text)
        
        # 撤销按钮
        self.undo_btn = QPushButton("⏪ 撤销上次操作")
        self.undo_btn.setObjectName("undoButton")
        self.undo_btn.setEnabled(False)
        self.undo_btn.clicked.connect(self.undo_rename)
        layout.addWidget(self.undo_btn)
        
        return group

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 文件计数标签
        self.file_count_label = QLabel("文件: 0")
        self.status_bar.addPermanentWidget(self.file_count_label)

    def setup_styles(self):
        """设置现代化样式"""
        style = """
        /* 主窗口样式 - 深色渐变背景 */
        QMainWindow {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #0f0c29, stop:0.5 #302b63, stop:1 #24243e);
            color: #ecf0f1;
        }
        
        QWidget {
            color: #ecf0f1;
        }
        
        /* 分组框样式 - 玻璃态效果 */
        QGroupBox {
            font-weight: bold;
            border: 2px solid rgba(22, 160, 133, 0.4);
            border-radius: 12px;
            margin-top: 1.2ex;
            padding-top: 15px;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(26, 26, 46, 0.85), stop:1 rgba(22, 33, 62, 0.85));
            backdrop-filter: blur(10px);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 10px 0 10px;
            color: #1abc9c;
            font-size: 13px;
            font-weight: bold;
        }
        
        QGroupBox#settingsGroup {
            border: 2px solid rgba(22, 160, 133, 0.5);
        }
        
        /* 标题栏样式 - 渐变卡片 */
        #headerFrame {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(22, 160, 133, 0.15), stop:1 rgba(52, 152, 219, 0.15));
            border-radius: 12px;
            padding: 15px;
            border: 2px solid rgba(22, 160, 133, 0.3);
        }
        
        #titleLabel {
            color: #1abc9c;
            font-weight: bold;
            text-shadow: 0 0 10px rgba(26, 188, 156, 0.5);
        }
        
        #versionLabel {
            color: #95a5a6;
            font-style: italic;
            background-color: rgba(52, 73, 94, 0.4);
            padding: 4px 12px;
            border-radius: 12px;
        }
        
        #sectionLabel {
            color: #1abc9c;
            font-weight: bold;
            font-size: 12px;
            padding: 5px 0;
        }
        
        #helpLabel {
            color: #95a5a6;
            font-size: 10px;
            font-style: italic;
            padding: 8px 12px;
            background-color: rgba(52, 73, 94, 0.3);
            border-radius: 6px;
            border-left: 3px solid #1abc9c;
        }
        
        /* 按钮样式 - 渐变和阴影 */
        QPushButton {
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: bold;
            font-size: 11px;
            min-width: 90px;
        }
        
        QPushButton#accentButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #16a085, stop:1 #1abc9c);
            color: white;
            border: 1px solid rgba(26, 188, 156, 0.3);
        }
        
        QPushButton#accentButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #138d75, stop:1 #17a589);
            border: 1px solid rgba(26, 188, 156, 0.6);
        }
        
        QPushButton#accentButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0e6655, stop:1 #117a65);
        }
        
        QPushButton#secondaryButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #34495e, stop:1 #2c3e50);
            color: #ecf0f1;
            border: 1px solid rgba(52, 73, 94, 0.5);
        }
        
        QPushButton#secondaryButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #415b76, stop:1 #34495e);
            border: 1px solid rgba(52, 73, 94, 0.8);
        }
        
        QPushButton#executeButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #27ae60, stop:1 #2ecc71);
            color: white;
            font-size: 14px;
            font-weight: bold;
            border: 2px solid rgba(46, 204, 113, 0.3);
        }
        
        QPushButton#executeButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #229954, stop:1 #27ae60);
            border: 2px solid rgba(46, 204, 113, 0.6);
        }
        
        QPushButton#warningButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #c0392b, stop:1 #e74c3c);
            color: white;
            border: 1px solid rgba(231, 76, 60, 0.3);
        }
        
        QPushButton#warningButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #a93226, stop:1 #cb4335);
            border: 1px solid rgba(231, 76, 60, 0.6);
        }
        
        QPushButton#undoButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #d35400, stop:1 #e67e22);
            color: white;
            border: 1px solid rgba(230, 126, 34, 0.3);
        }
        
        QPushButton#undoButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ba4a00, stop:1 #d35400);
            border: 1px solid rgba(230, 126, 34, 0.6);
        }
        
        QPushButton:disabled {
            background: rgba(44, 62, 80, 0.3);
            color: #7f8c8d;
            border: 1px solid rgba(127, 140, 141, 0.2);
        }
        
        /* 输入框样式 - 发光效果 */
        QLineEdit#modernLineEdit {
            background-color: rgba(26, 26, 46, 0.6);
            border: 2px solid rgba(22, 160, 133, 0.3);
            border-radius: 8px;
            padding: 10px 12px;
            color: #ecf0f1;
            font-size: 12px;
            font-weight: 500;
        }
        
        QLineEdit#modernLineEdit:focus {
            border: 2px solid #1abc9c;
            background-color: rgba(26, 26, 46, 0.8);
        }
        
        /* 表格样式 - 斑马纹和悬停效果 */
        QTableWidget#modernTable {
            background-color: rgba(26, 26, 46, 0.5);
            alternate-background-color: rgba(22, 33, 62, 0.5);
            border: 2px solid rgba(22, 160, 133, 0.2);
            border-radius: 10px;
            gridline-color: rgba(22, 160, 133, 0.15);
            color: #ecf0f1;
            selection-background-color: rgba(22, 160, 133, 0.4);
        }
        
        QTableWidget#modernTable::item {
            padding: 10px 8px;
            border: none;
        }
        
        QTableWidget#modernTable::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(22, 160, 133, 0.4), stop:1 rgba(26, 188, 156, 0.4));
            color: white;
        }
        
        QTableWidget#modernTable::item:hover {
            background-color: rgba(22, 160, 133, 0.15);
        }
        
        QHeaderView::section {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(22, 160, 133, 0.3), stop:1 rgba(22, 160, 133, 0.2));
            color: #1abc9c;
            padding: 10px 8px;
            border: none;
            border-right: 1px solid rgba(22, 160, 133, 0.2);
            border-bottom: 2px solid rgba(22, 160, 133, 0.4);
            font-weight: bold;
            font-size: 11px;
        }
        
        QHeaderView::section:first {
            border-top-left-radius: 8px;
        }
        
        QHeaderView::section:last {
            border-top-right-radius: 8px;
            border-right: none;
        }
        
        /* 文本编辑器样式 - 终端风格 */
        QTextEdit#modernTextEdit {
            background-color: rgba(15, 12, 41, 0.8);
            border: 2px solid rgba(22, 160, 133, 0.2);
            border-radius: 10px;
            color: #2ecc71;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 10px;
            padding: 10px;
        }
        
        /* 进度条样式 - 发光动画 */
        QProgressBar#modernProgressBar {
            border: none;
            border-radius: 4px;
            text-align: center;
            background-color: rgba(26, 26, 46, 0.6);
            color: #ecf0f1;
            font-weight: bold;
            font-size: 10px;
        }
        
        QProgressBar#modernProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #16a085, stop:0.5 #1abc9c, stop:1 #16a085);
            border-radius: 4px;
        }
        
        /* 分割器样式 */
        QSplitter#mainSplitter::handle {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(22, 160, 133, 0.2), stop:0.5 rgba(22, 160, 133, 0.4), stop:1 rgba(22, 160, 133, 0.2));
            width: 4px;
            border-radius: 2px;
        }
        
        QSplitter#mainSplitter::handle:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(26, 188, 156, 0.4), stop:0.5 rgba(26, 188, 156, 0.8), stop:1 rgba(26, 188, 156, 0.4));
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(26, 26, 46, 0.9), stop:1 rgba(22, 33, 62, 0.9));
            border-top: 2px solid rgba(22, 160, 133, 0.3);
            color: #95a5a6;
            padding: 5px;
        }
        
        QStatusBar QLabel {
            color: #95a5a6;
            padding: 0 10px;
        }
        
        /* 滚动条样式 - 细长现代风格 */
        QScrollBar:vertical {
            background: rgba(26, 26, 46, 0.3);
            width: 10px;
            border-radius: 5px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #16a085, stop:1 #1abc9c);
            border-radius: 5px;
            min-height: 30px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #138d75, stop:1 #17a589);
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        
        QScrollBar:horizontal {
            background: rgba(26, 26, 46, 0.3);
            height: 10px;
            border-radius: 5px;
            margin: 0;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #16a085, stop:1 #1abc9c);
            border-radius: 5px;
            min-width: 30px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #138d75, stop:1 #17a589);
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }
        """
        
        self.setStyleSheet(style)

    def load_default_data(self):
        """加载默认数据"""
        # 默认项目数据
        default_projects = [
            ("洗衣店偷衣服", "Pre-shoot-洗衣店偷衣服-C02---华容道平铺02-tileflower"),
            ("插队的补偿", "Pre-shoot-插队的补偿-C01-华容道平铺02tileflower"), 
            ("无语言偷看1", "pre-shoot-无语言偷看1"),
        ]
        
        for code, name in default_projects:
            self.add_project_row(code, name)
            self.project_codes[code] = name
        
        # 添加空行
        for _ in range(3):
            self.add_project_row()
        
        # 默认差分规则
        default_rules = [
            ("1", "核玩翻页", "HWFY", "cn"),
            ("2", "动画quiz-批量化", "BVC", "es"), 
            ("4", "核玩新版", "SLT", "en"),
        ]
        
        for diff, full, abbr, lang in default_rules:
            self.add_rule_row(diff, full, abbr, lang)
            if diff:
                self.diff_rules[diff] = (full, abbr, lang)
        
        # 添加空行
        for _ in range(3):
            self.add_rule_row()

    def add_project_row(self, code="", name=""):
        """添加项目行"""
        row = self.project_table.rowCount()
        self.project_table.insertRow(row)
        
        code_item = QTableWidgetItem(code)
        name_item = QTableWidgetItem(name)
        
        self.project_table.setItem(row, 0, code_item)
        self.project_table.setItem(row, 1, name_item)

    def add_rule_row(self, diff="", full="", abbr="", lang=""):
        """添加差分规则行"""
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        
        diff_item = QTableWidgetItem(diff)
        full_item = QTableWidgetItem(full)
        abbr_item = QTableWidgetItem(abbr)
        lang_item = QTableWidgetItem(lang)
        
        self.rules_table.setItem(row, 0, diff_item)
        self.rules_table.setItem(row, 1, full_item)
        self.rules_table.setItem(row, 2, abbr_item)
        self.rules_table.setItem(row, 3, lang_item)

    def remove_project_row(self):
        """删除选中的项目行"""
        current_row = self.project_table.currentRow()
        if current_row >= 0:
            self.project_table.removeRow(current_row)
            self.update_project_config()

    def remove_rule_row(self):
        """删除选中的差分规则行"""
        current_row = self.rules_table.currentRow()
        if current_row >= 0:
            self.rules_table.removeRow(current_row)
            self.update_rule_config()

    def update_project_config(self):
        """更新项目配置"""
        self.project_codes.clear()
        
        for row in range(self.project_table.rowCount()):
            code_item = self.project_table.item(row, 0)
            name_item = self.project_table.item(row, 1)
            
            if code_item and name_item:
                code = code_item.text().strip()
                name = name_item.text().strip()
                if code and name:
                    self.project_codes[code] = name
        
        self.update_preview()

    def update_rule_config(self):
        """更新差分规则配置"""
        self.diff_rules.clear()
        
        for row in range(self.rules_table.rowCount()):
            diff_item = self.rules_table.item(row, 0)
            full_item = self.rules_table.item(row, 1)
            abbr_item = self.rules_table.item(row, 2)
            lang_item = self.rules_table.item(row, 3)
            
            if all([diff_item, full_item, abbr_item, lang_item]):
                diff = diff_item.text().strip()
                full = full_item.text().strip()
                abbr = abbr_item.text().strip()
                lang = lang_item.text().strip()
                
                if diff and full and abbr and lang:
                    self.diff_rules[diff] = (full, abbr, lang)
                    # 更新记忆库
                    self.update_memory_bank(full, abbr, lang)
        
        self.update_preview()


    def add_files(self):
        """添加文件"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", "", "所有文件 (*.*)"
        )
        if files:
            self.add_files_to_list(files)

    def add_folder(self):
        """添加文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            files = []
            for file_path in Path(folder).iterdir():
                if file_path.is_file():
                    files.append(str(file_path))
            self.add_files_to_list(files)

    def add_files_to_list(self, file_paths):
        """添加文件到列表"""
        for file_path in file_paths:
            if not any(f[0] == file_path for f in self.files_to_rename):
                self.files_to_rename.append((file_path, os.path.basename(file_path)))
        
        self.update_preview()
        self.update_file_count()

    def refresh_file_recognition(self):
        """重新识别文件名"""
        updated_files = []
        for file_path, _ in self.files_to_rename:
            if os.path.exists(file_path):
                current_name = os.path.basename(file_path)
                updated_files.append((file_path, current_name))
            else:
                dir_path = os.path.dirname(file_path)
                if os.path.exists(dir_path):
                    updated_files.append((file_path, os.path.basename(file_path)))
        
        self.files_to_rename = updated_files
        self.update_preview()
        self.update_file_count()

    def clear_file_list(self):
        """清空文件列表"""
        self.files_to_rename.clear()
        self.update_preview()
        self.update_file_count()

    def update_preview(self):
        """更新预览"""
        self.file_table.setRowCount(0)
        
        for i, (file_path, original_name) in enumerate(self.files_to_rename):
            name_no_ext, ext = os.path.splitext(original_name)
            result = self.generate_new_name(name_no_ext)
            
            if isinstance(result, tuple):
                new_name_no_ext, status = result
                new_name = new_name_no_ext + ext if not new_name_no_ext.startswith("[") else new_name_no_ext
            else:
                new_name = result + ext if not result.startswith("[") else result
                status = "✅" if not result.startswith("[") else "❌"
            
            # 添加行到表格
            row = self.file_table.rowCount()
            self.file_table.insertRow(row)
            
            # 设置单元格内容
            original_item = QTableWidgetItem(original_name)
            new_item = QTableWidgetItem(new_name)
            status_item = QTableWidgetItem(status)
            
            # 设置颜色
            if status == "✅":
                new_item.setForeground(QColor("#2ecc71"))
                status_item.setForeground(QColor("#2ecc71"))
            else:
                new_item.setForeground(QColor("#e74c3c"))
                status_item.setForeground(QColor("#e74c3c"))
            
            self.file_table.setItem(row, 0, original_item)
            self.file_table.setItem(row, 1, new_item)
            self.file_table.setItem(row, 2, status_item)

    def generate_new_name(self, original_name_no_ext):
        """生成新文件名"""
        matched_code = None
        matched_project = None
        
        sorted_codes = sorted(self.project_codes.items(), key=lambda x: len(x[0]), reverse=True)
        
        for code, project_name in sorted_codes:
            if code and original_name_no_ext.startswith(code):
                matched_code = code
                matched_project = project_name
                break
        
        if not matched_code:
            return "[无匹配项目]", "❌"
        
        remaining = original_name_no_ext[len(matched_code):]
        
        if remaining.startswith('-'):
            diff_num = remaining[1:]
        else:
            diff_num = remaining
        
        if not diff_num:
            return "[缺少差分号]", "❌"
        
        if not diff_num.isdigit():
            return f"[差分号格式错误: {diff_num}]", "❌"
        
        if diff_num not in self.diff_rules:
            return f"[差分号{diff_num}无规则]", "❌"
        
        rule_data = self.diff_rules[diff_num]
        if len(rule_data) != 3:
            return f"[差分号{diff_num}规则不完整]", "❌"
        
        full_name, abbr, lang = rule_data
        
        if not all([full_name.strip(), abbr.strip(), lang.strip()]):
            return f"[差分号{diff_num}规则数据不完整]", "❌"
        
        date = self.date_edit.text()
        final_name = f"{date}_{matched_project}+{full_name}_{lang}_{abbr}_1080x1920"
        
        return final_name, "✅"

    def update_file_count(self):
        """更新文件计数"""
        count = len(self.files_to_rename)
        self.file_count_label.setText(f"文件: {count}")

    def execute_rename(self):
        """执行重命名"""
        if not self.files_to_rename:
            QMessageBox.information(self, "提示", "文件列表为空,请先添加文件")
            return
        
        self.last_renames.clear()
        self.log_history("开始执行重命名操作...\n")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.files_to_rename))
        self.progress_bar.setValue(0)
        
        success_count = 0
        fail_count = 0
        
        for i, (file_path, original_name) in enumerate(self.files_to_rename):
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
            
            if i < self.file_table.rowCount():
                new_name_item = self.file_table.item(i, 1)
                status_item = self.file_table.item(i, 2)
                
                if not new_name_item or not status_item:
                    continue
                
                new_name = new_name_item.text()
                status = status_item.text()
                
                if status != "✅":
                    self.log_history(f"跳过: {original_name} ({status})\n")
                    fail_count += 1
                    continue
                
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                
                try:
                    os.rename(file_path, new_path)
                    self.log_history(f"✅ 成功: {original_name} -> {new_name}\n")
                    self.last_renames.append((new_path, file_path))
                    success_count += 1
                except OSError as e:
                    self.log_history(f"❌ 失败: {original_name} -> {str(e)}\n")
                    fail_count += 1
        
        self.progress_bar.setVisible(False)
        
        self.log_history(f"\n操作完成!成功: {success_count}, 失败/跳过: {fail_count}\n")
        
        self.files_to_rename.clear()
        self.update_preview()
        self.update_file_count()
        
        if self.last_renames:
            self.undo_btn.setEnabled(True)

    def undo_rename(self):
        """撤销重命名"""
        if not self.last_renames:
            QMessageBox.information(self, "提示", "没有可撤销的操作")
            return
        
        self.log_history("开始撤销上次操作...\n")
        success_count = 0
        fail_count = 0
        
        for new_path, original_path in reversed(self.last_renames):
            try:
                os.rename(new_path, original_path)
                self.log_history(f"✅ 撤销成功: {os.path.basename(new_path)} -> {os.path.basename(original_path)}\n")
                success_count += 1
            except OSError as e:
                self.log_history(f"❌ 撤销失败: {os.path.basename(new_path)} -> {str(e)}\n")
                fail_count += 1
        
        self.log_history(f"\n撤销完成!成功: {success_count}, 失败: {fail_count}\n")
        
        self.last_renames.clear()
        self.undo_btn.setEnabled(False)

    def log_history(self, message):
        """记录历史日志"""
        self.history_text.append(message.rstrip())
        cursor = self.history_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.history_text.setTextCursor(cursor)

    def save_all_config(self):
        """保存完整配置到JSON文件"""
        config_data = {
            "date": self.date_edit.text(),
            "project_codes": {},
            "diff_rules": {}
        }
        
        for row in range(self.project_table.rowCount()):
            code_item = self.project_table.item(row, 0)
            name_item = self.project_table.item(row, 1)
            
            if code_item and name_item:
                code = code_item.text().strip()
                name = name_item.text().strip()
                if code and name:
                    config_data["project_codes"][code] = name
        
        for row in range(self.rules_table.rowCount()):
            diff_item = self.rules_table.item(row, 0)
            full_item = self.rules_table.item(row, 1)
            abbr_item = self.rules_table.item(row, 2)
            lang_item = self.rules_table.item(row, 3)
            
            if all([diff_item, full_item, abbr_item, lang_item]):
                diff = diff_item.text().strip()
                full = full_item.text().strip()
                abbr = abbr_item.text().strip()
                lang = lang_item.text().strip()
                
                if diff and full and abbr and lang:
                    config_data["diff_rules"][diff] = {
                        "full_name": full,
                        "abbr": abbr,
                        "lang": lang
                    }
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", f"配置已保存到:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置失败:\n{str(e)}")

    def load_config_file(self):
        """从JSON文件加载配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "加载配置文件", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if "date" in config_data:
                    self.date_edit.setText(config_data["date"])
                
                self.project_table.setRowCount(0)
                self.project_codes.clear()
                
                if "project_codes" in config_data:
                    for code, name in config_data["project_codes"].items():
                        self.add_project_row(code, name)
                        self.project_codes[code] = name
                
                for _ in range(3):
                    self.add_project_row()
                
                self.rules_table.setRowCount(0)
                self.diff_rules.clear()
                
                if "diff_rules" in config_data:
                    for diff_num, rule_data in config_data["diff_rules"].items():
                        self.add_rule_row(
                            diff_num,
                            rule_data["full_name"],
                            rule_data["abbr"],
                            rule_data["lang"]
                        )
                        self.diff_rules[diff_num] = (
                            rule_data["full_name"],
                            rule_data["abbr"],
                            rule_data["lang"]
                        )
                
                for _ in range(3):
                    self.add_rule_row()
                
                QMessageBox.information(self, "成功", f"配置已从以下文件加载:\n{file_path}")
                self.update_preview()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载配置失败:\n{str(e)}")

    def load_window_config(self):
        """加载窗口配置"""
        try:
            if os.path.exists(self.window_config_file):
                with open(self.window_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if "geometry" in config:
                    geometry = config["geometry"]
                    if "x" in geometry and "y" in geometry and "width" in geometry and "height" in geometry:
                        self.setGeometry(geometry["x"], geometry["y"], geometry["width"], geometry["height"])
                
                if "maximized" in config and config["maximized"]:
                    self.showMaximized()
                    
        except Exception as e:
            print(f"加载窗口配置失败: {e}")

    def save_window_config(self):
        """保存窗口配置"""
        try:
            config = {
                "geometry": {
                    "x": self.x(),
                    "y": self.y(),
                    "width": self.width(),
                    "height": self.height()
                },
                "maximized": self.isMaximized()
            }
            
            with open(self.window_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存窗口配置失败: {e}")

    def load_auto_config(self):
        """加载自动保存的配置"""
        try:
            if os.path.exists(self.auto_config_file):
                with open(self.auto_config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if "date" in config_data:
                    self.date_edit.setText(config_data["date"])
                
                self.project_table.setRowCount(0)
                self.project_codes.clear()
                
                if "project_codes" in config_data:
                    for code, name in config_data["project_codes"].items():
                        self.add_project_row(code, name)
                        self.project_codes[code] = name
                
                for _ in range(3):
                    self.add_project_row()
                
                self.rules_table.setRowCount(0)
                self.diff_rules.clear()
                
                if "diff_rules" in config_data:
                    for diff_num, rule_data in config_data["diff_rules"].items():
                        self.add_rule_row(
                            diff_num,
                            rule_data["full_name"],
                            rule_data["abbr"],
                            rule_data["lang"]
                        )
                        self.diff_rules[diff_num] = (
                            rule_data["full_name"],
                            rule_data["abbr"],
                            rule_data["lang"]
                        )
                
                for _ in range(3):
                    self.add_rule_row()
                
                print("自动加载配置成功")
                
        except Exception as e:
            print(f"自动加载配置失败: {e}")

    def save_auto_config(self):
        """自动保存当前配置"""
        try:
            config_data = {
                "date": self.date_edit.text(),
                "project_codes": {},
                "diff_rules": {}
            }
            
            for row in range(self.project_table.rowCount()):
                code_item = self.project_table.item(row, 0)
                name_item = self.project_table.item(row, 1)
                
                if code_item and name_item:
                    code = code_item.text().strip()
                    name = name_item.text().strip()
                    if code and name:
                        config_data["project_codes"][code] = name
            
            for row in range(self.rules_table.rowCount()):
                diff_item = self.rules_table.item(row, 0)
                full_item = self.rules_table.item(row, 1)
                abbr_item = self.rules_table.item(row, 2)
                lang_item = self.rules_table.item(row, 3)
                
                if all([diff_item, full_item, abbr_item, lang_item]):
                    diff = diff_item.text().strip()
                    full = full_item.text().strip()
                    abbr = abbr_item.text().strip()
                    lang = lang_item.text().strip()
                    
                    if diff and full and abbr and lang:
                        config_data["diff_rules"][diff] = {
                            "full_name": full,
                            "abbr": abbr,
                            "lang": lang
                        }
            
            with open(self.auto_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"自动保存配置失败: {e}")

    def load_memory_bank(self):
        """加载记忆库"""
        try:
            if os.path.exists(self.memory_bank_file):
                with open(self.memory_bank_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.memory_bank = {
                    "version_names": set(data.get("version_names", [])),
                    "abbreviations": set(data.get("abbreviations", [])),
                    "languages": set(data.get("languages", []))
                }
                print("记忆库加载成功")
        except Exception as e:
            print(f"加载记忆库失败: {e}")
            self.memory_bank = {
                "version_names": set(),
                "abbreviations": set(),
                "languages": set()
            }

    def save_memory_bank(self):
        """保存记忆库"""
        try:
            data = {
                "version_names": list(self.memory_bank["version_names"]),
                "abbreviations": list(self.memory_bank["abbreviations"]),
                "languages": list(self.memory_bank["languages"])
            }
            
            with open(self.memory_bank_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存记忆库失败: {e}")

    def update_memory_bank(self, full_name, abbr, lang):
        """更新记忆库"""
        if full_name.strip():
            self.memory_bank["version_names"].add(full_name.strip())
        if abbr.strip():
            self.memory_bank["abbreviations"].add(abbr.strip())
        if lang.strip():
            self.memory_bank["languages"].add(lang.strip())
        
        self.save_memory_bank()

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.rules_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        column = item.column()
        
        if column not in [1, 2, 3]:
            return
        
        menu = QMenu(self)
        
        if column == 1:
            memory_data = list(self.memory_bank["version_names"])
            menu_title = "📝 选择版本名全称"
        elif column == 2:
            memory_data = list(self.memory_bank["abbreviations"])
            menu_title = "🔤 选择版本名缩写"
        elif column == 3:
            memory_data = list(self.memory_bank["languages"])
            menu_title = "🌐 选择语言"
        
        if not memory_data:
            no_data_action = QAction("💡 记忆库中暂无数据", self)
            no_data_action.setEnabled(False)
            menu.addAction(no_data_action)
        else:
            title_action = QAction(menu_title, self)
            title_action.setEnabled(False)
            menu.addAction(title_action)
            menu.addSeparator()
            
            sorted_data = sorted(memory_data)[:10]
            for data in sorted_data:
                action = QAction(data, self)
                action.triggered.connect(lambda checked, value=data: self.set_cell_value(row, column, value))
                menu.addAction(action)
            
            if len(memory_data) > 10:
                menu.addSeparator()
                more_action = QAction("📋 查看更多...", self)
                more_action.triggered.connect(lambda: self.show_memory_dialog_for_cell(row, column))
                menu.addAction(more_action)
        
        menu.setStyleSheet("""
            QMenu {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a1a2e, stop:1 #16213e);
                color: #ecf0f1;
                border: 2px solid rgba(22, 160, 133, 0.5);
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 10px 20px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #16a085, stop:1 #1abc9c);
                color: white;
            }
            QMenu::item:disabled {
                color: #7f8c8d;
            }
            QMenu::separator {
                height: 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, stop:0.5 rgba(22, 160, 133, 0.5), stop:1 transparent);
                margin: 6px 10px;
            }
        """)
        
        menu.exec(self.rules_table.mapToGlobal(position))
    
    def set_cell_value(self, row, column, value):
        """设置单元格的值"""
        item = self.rules_table.item(row, column)
        if item:
            item.setText(value)
        else:
            self.rules_table.setItem(row, column, QTableWidgetItem(value))
        
        self.update_rule_config()
    
    def show_memory_dialog_for_cell(self, row, column):
        """为特定单元格显示记忆库对话框"""
        if column == 1:
            memory_data = list(self.memory_bank["version_names"])
            title = "选择版本名全称"
        elif column == 2:
            memory_data = list(self.memory_bank["abbreviations"])
            title = "选择版本名缩写"
        elif column == 3:
            memory_data = list(self.memory_bank["languages"])
            title = "选择语言"
        else:
            return
        
        if not memory_data:
            QMessageBox.information(self, "提示", "记忆库中暂无相关数据")
            return
        
        selected_value = self.show_memory_dialog(title, memory_data)
        if selected_value:
            self.set_cell_value(row, column, selected_value)

    def show_memory_dialog(self, title, data_list):
        """显示记忆库选择对话框"""
        dialog = MemoryBankDialog(title, data_list, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_value()
        return None

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        self.save_window_config()
        self.save_auto_config()
        self.save_memory_bank()
        event.accept()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """拖拽进入事件"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """拖拽放下事件"""
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
            elif os.path.isdir(file_path):
                for file in Path(file_path).iterdir():
                    if file.is_file():
                        files.append(str(file))
        
        if files:
            self.add_files_to_list(files)
            self.status_label.setText(f"已添加 {len(files)} 个文件")
            QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    app.setApplicationName("智能批量重命名工具")
    app.setApplicationVersion("5.0")
    app.setOrganizationName("PyQt6 Tools")
    
    window = ModernBatchRenamerApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
