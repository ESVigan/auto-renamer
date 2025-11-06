#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量文件重命名工具 - PyQt6版本
现代化界面，专业级用户体验
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QLabel, QLineEdit, QPushButton, QTableWidget, 
    QTableWidgetItem, QTextEdit, QFileDialog, QMessageBox, 
    QSplitter, QGroupBox, QHeaderView, QCheckBox, QFrame,
    QScrollArea, QTabWidget, QProgressBar, QStatusBar, QListWidget,
    QDialog, QDialogButtonBox, QMenu, QStyledItemDelegate, QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QMimeData, QUrl
)
from PyQt6.QtGui import (
    QFont, QIcon, QPalette, QColor, QPixmap, QDragEnterEvent, 
    QDropEvent, QAction, QKeySequence
)


class TriStateSortTableWidget(QTableWidget):
    """支持三态排序的表格控件（升序、降序、不排序）"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_sort_column = -1
        self._last_sort_order = Qt.SortOrder.AscendingOrder
        self.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

    def on_header_clicked(self, logical_index):
        """处理表头点击事件"""
        if self._last_sort_column == logical_index:
            # 循环切换排序状态
            if self._last_sort_order == Qt.SortOrder.AscendingOrder:
                self._last_sort_order = Qt.SortOrder.DescendingOrder
            else:
                # 切换到不排序状态
                self._last_sort_column = -1
                self.restore_original_order()
                return
        else:
            # 新的列，从升序开始
            self._last_sort_column = logical_index
            self._last_sort_order = Qt.SortOrder.AscendingOrder
        
        self.sort_with_row_numbers(self._last_sort_column, self._last_sort_order)

    def sort_with_row_numbers(self, column, order):
        """排序时保持行编号与内容同步"""
        if column < 0 or column >= self.columnCount():
            return
        
        # 收集所有行的数据
        rows_data = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            rows_data.append(row_data)
        
        # 根据指定列进行排序（跳过第0列的行号）
        if column > 0:  # 只有非行号列才进行排序
            def sort_key(row_data):
                text = row_data[column].strip()
                # 空值排序逻辑：空值应该排在最后
                if text == "":
                    return (1, "")  # 空值排在后面
                
                # 尝试进行数值比较
                try:
                    return (0, float(text))
                except (ValueError, TypeError):
                    # 字符串比较
                    return (0, text.lower())
            
            rows_data.sort(key=sort_key, reverse=(order == Qt.SortOrder.DescendingOrder))
        
        # 更新表格内容并重新编号
        for row, row_data in enumerate(rows_data):
            # 更新行号（第0列）
            row_num_item = CustomTableWidgetItem(str(row + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, row_num_item)
            
            # 更新其他列的内容
            for col in range(1, self.columnCount()):
                if col < len(row_data):
                    item = CustomTableWidgetItem(row_data[col])
                    self.setItem(row, col, item)

    def restore_original_order(self):
        """恢复原始顺序（按行号排序）"""
        # 收集所有行的数据
        rows_data = []
        for row in range(self.rowCount()):
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            rows_data.append((row, row_data))  # 保存原始行号
        
        # 按原始行号排序
        rows_data.sort(key=lambda x: x[0])
        
        # 更新表格内容并重新编号
        for new_row, (original_row, row_data) in enumerate(rows_data):
            # 更新行号（第0列）
            row_num_item = CustomTableWidgetItem(str(new_row + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(new_row, 0, row_num_item)
            
            # 更新其他列的内容
            for col in range(1, self.columnCount()):
                if col < len(row_data):
                    item = CustomTableWidgetItem(row_data[col])
                    self.setItem(new_row, col, item)

    def mousePressEvent(self, event):
        """重写鼠标按下事件，确保编辑能够正确触发"""
        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                item = self.item(index.row(), index.column())
                if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                    # 设置当前项并立即进入编辑模式
                    self.setCurrentItem(item)
                    self.setFocus()
                    # 使用定时器确保状态更新后再编辑
                    QTimer.singleShot(10, lambda: self.editItem(item))
                    return
        
        # 调用父类方法处理其他情况
        super().mousePressEvent(event)
    




class CustomTableWidgetItem(QTableWidgetItem):
    """自定义表格项，用于排序时将空值置底"""
    def __lt__(self, other):
        self_text = self.text().strip()
        other_text = other.text().strip()
        
        # 空值排序逻辑：空值应该排在最后（升序时在底部，降序时在顶部）
        if self_text == "" and other_text != "":
            return False  # 空值不小于非空值，所以排在后面
        if self_text != "" and other_text == "":
            return True   # 非空值小于空值，所以排在前面
        if self_text == "" and other_text == "":
            return False  # 两个空值相等，不需要交换位置

        # 尝试进行数值比较
        try:
            return float(self_text) < float(other_text)
        except (ValueError, TypeError):
            # 字符串比较
            return self_text.lower() < other_text.lower()


class LineEditDelegate(QStyledItemDelegate):
    """自定义委托，用于在表格中创建填满单元格的QLineEdit"""
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        # 简化样式，减少渲染时间
        editor.setStyleSheet("QLineEdit { background-color: #f8f9fa; border: 1px solid #0078d7; }")
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        if value is None:
            editor.setText("")
        else:
            editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class ImportDialog(QDialog):
    """从数据源导入项目代号的对话框"""
    def __init__(self, initial_ignore_list=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从数据源导入项目")
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        info_label = QLabel("在此处粘贴从网页复制的文本数据：")
        layout.addWidget(info_label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("例如：\npre-shoot-项目名A1+差分规则-完成订单...\nmysterytown\n制作中...")
        layout.addWidget(self.text_edit)
        
        # 新增：忽略规则输入框
        ignore_layout = QHBoxLayout()
        ignore_label = QLabel("忽略文本 (用逗号分隔):")
        self.ignore_edit = QLineEdit()
        self.ignore_edit.setPlaceholderText("例如：-C01, -C02, ...")
        if initial_ignore_list:
            self.ignore_edit.setText(", ".join(initial_ignore_list))
        ignore_layout.addWidget(ignore_label)
        ignore_layout.addWidget(self.ignore_edit)
        layout.addLayout(ignore_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_data(self):
        """获取输入框的文本和忽略规则"""
        text = self.text_edit.toPlainText()
        ignore_text = self.ignore_edit.text().strip()
        ignore_list = [item.strip() for item in ignore_text.split(',') if item.strip()]
        return text, ignore_list


class MemoryBankDialog(QDialog):
    """记忆库选择对话框"""
    
    def __init__(self, title, data_list, parent=None):
        super().__init__(parent)
        self.data_list = sorted(data_list)  # 排序显示
        self.selected_value = None
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(450, 350)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                color: #333333;
            }
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 8px;
                color: #333333;
                font-size: 12px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #e6f2fa;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        info_label = QLabel("💡 双击选择项目，或选中后点击确定")
        info_label.setStyleSheet("""
            color: #666666; 
            font-size: 11px; 
            padding: 8px 12px;
            background-color: #e9e9e9;
            border-radius: 6px;
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
        
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 12px;
                min-width: 90px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
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
        self.configs_dir = "configs"  # 配置文件保存目录
        self.current_config_name = "默认配置"  # 当前配置名称
        
        # 确保配置目录存在
        if not os.path.exists(self.configs_dir):
            os.makedirs(self.configs_dir)
        
        # 数据存储
        self.files_to_rename: List[Tuple[str, str]] = []
        self.last_renames: List[Tuple[str, str]] = []
        self.project_codes: Dict[str, str] = {}
        self.diff_rules: Dict[str, Tuple[str, str, str, str]] = {}
        self.undo_stack = []
        self.ignore_list: List[str] = []
        
        # 记忆库存储
        self.memory_bank = {
            "version_names": set(),
            "abbreviations": set(),
            "languages": set()
        }

        # 初始化界面
        self.init_ui()
        self.setup_styles()
        self.load_window_config()
        self.setup_shortcuts()
        self.setup_date_timer()  # 自动更新日期
        
        # 延迟初始数据加载，确保UI完全准备就绪，避免启动时加载不完整的问题
        QTimer.singleShot(0, self.initial_data_load)
        
        # 加载记忆库
        self.load_memory_bank()
        
        # 设置表格右键菜单
        self.rules_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.rules_table.customContextMenuRequested.connect(self.show_context_menu)

        # 设置默认排序状态为不排序
        self.project_table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        self.rules_table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        self.file_table.sortByColumn(-1, Qt.SortOrder.AscendingOrder)
        
        # 启用拖拽功能
        self.setAcceptDrops(True)

    def setup_shortcuts(self):
        """设置快捷键"""
        undo_action = QAction("撤销", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)  # Ctrl+Z
        undo_action.triggered.connect(self.undo_last_action)
        self.addAction(undo_action)

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("LPX的批量命名小工具 v1.42")
        self.setMinimumSize(1200, 900)
        self.resize(1400, 1000)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)
        
        # 创建主要内容区域
        self.create_main_content(main_layout)
        
        # 创建状态栏
        self.create_status_bar()

    def create_main_content(self, parent_layout):
        """创建主要内容区域"""
        # 使用分割器创建左右布局
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setHandleWidth(4)
        
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
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
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
        right_layout.setSpacing(16)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
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
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 日期设置
        date_layout = QHBoxLayout()
        date_label = QLabel("日期 (YYMMDD):")
        date_label.setMinimumWidth(120)
        date_label.setStyleSheet("font-weight: 500; color: #333333;")
        
        # 自动获取当前日期（格式：YYMMDD）
        current_date = datetime.now().strftime("%y%m%d")
        self.date_edit = QLineEdit(current_date)
        self.date_edit.setObjectName("modernLineEdit")
        self.date_edit.setMinimumWidth(180)
        
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        # 配置管理区域
        config_layout = QHBoxLayout()
        config_layout.setSpacing(8)
        
        # 当前配置显示
        config_name_label = QLabel("当前配置:")
        config_name_label.setStyleSheet("font-weight: 500; color: #333333;")
        self.current_config_label = QLabel(self.current_config_name)
        self.current_config_label.setStyleSheet("""
            color: #0078d7; 
            font-weight: 600;
            padding: 4px 8px;
            background-color: #e6f2fa;
            border-radius: 4px;
        """)
        
        config_layout.addWidget(config_name_label)
        config_layout.addWidget(self.current_config_label)
        config_layout.addStretch()
        
        # 配置按钮
        save_config_btn = QPushButton("💾 保存配置")
        save_config_btn.setObjectName("accentButton")
        save_config_btn.setMaximumWidth(100)
        save_config_btn.clicked.connect(self.save_current_config)
        
        load_config_btn = QPushButton("📂 切换配置")
        load_config_btn.setObjectName("normalButton")
        load_config_btn.setMaximumWidth(100)
        load_config_btn.clicked.connect(self.switch_config)
        
        manage_config_btn = QPushButton("⚙️ 管理")
        manage_config_btn.setObjectName("normalButton")
        manage_config_btn.setMaximumWidth(80)
        manage_config_btn.clicked.connect(self.manage_configs)

        update_history_btn = QPushButton("📜 更新历史")
        update_history_btn.setObjectName("normalButton")
        update_history_btn.setMaximumWidth(100)
        update_history_btn.clicked.connect(self.show_update_history)
        
        check_update_btn = QPushButton("🔍 检查更新")
        check_update_btn.setObjectName("accentButton")
        check_update_btn.setMaximumWidth(100)
        check_update_btn.clicked.connect(self.check_for_updates)
        
        config_layout.addWidget(save_config_btn)
        config_layout.addWidget(load_config_btn)
        config_layout.addWidget(manage_config_btn)
        config_layout.addWidget(update_history_btn)
        config_layout.addWidget(check_update_btn)
        
        layout.addLayout(date_layout)
        layout.addLayout(config_layout)
        return group

    def create_project_codes_section(self):
        """创建项目代号配置区域"""
        group = QGroupBox("📋 项目代号配置")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 说明文字
        help_label = QLabel("💡 直接在表格中编辑，支持多行配置")
        help_label.setObjectName("helpLabel")
        layout.addWidget(help_label)
        
        # 项目代号表格
        self.project_table = TriStateSortTableWidget(0, 3)
        self.project_table.setObjectName("project_table")
        self.project_table.setHorizontalHeaderLabels(["#", "项目代号", "项目名前缀"])
        
        # 设置表格属性
        self.project_table.setSortingEnabled(True)
        self.project_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.project_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        header = self.project_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 40)  # 设置行号列宽度为40像素
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.project_table.setMaximumHeight(200)
        self.project_table.cellClicked.connect(self.on_table_cell_clicked)
        
        # 设置自定义委托
        project_delegate = LineEditDelegate(self.project_table)
        self.project_table.setItemDelegate(project_delegate)
        
        layout.addWidget(self.project_table)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_project_btn = QPushButton("➕ 添加行")
        add_project_btn.setObjectName("accentButton")
        add_project_btn.clicked.connect(self.add_project_row)
        
        remove_project_btn = QPushButton("➖ 删除行")
        remove_project_btn.setObjectName("normalButton")
        remove_project_btn.clicked.connect(self.remove_project_row)
        
        import_btn = QPushButton("📥 从数据源导入")
        import_btn.setObjectName("normalButton")
        import_btn.clicked.connect(self.import_from_data_source)

        btn_layout.addWidget(add_project_btn)
        btn_layout.addWidget(remove_project_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        return group

    def create_diff_rules_section(self):
        """创建差分规则配置区域"""
        group = QGroupBox("⚙️ 差分规则配置")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 说明文字
        help_label = QLabel("💡 直接在表格中编辑，所有项目共用。右键版本名全称、版本名缩写、语言列可使用记忆库功能")
        help_label.setObjectName("helpLabel")
        help_label.setWordWrap(True)
        layout.addWidget(help_label)
        
        # 差分规则表格
        self.rules_table = TriStateSortTableWidget(0, 6)
        self.rules_table.setObjectName("rules_table")
        self.rules_table.setHorizontalHeaderLabels(["#", "差分号", "连接符", "版本名全称", "版本名缩写", "语言"])
        
        # 设置表格属性
        self.rules_table.setSortingEnabled(True)
        self.rules_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.rules_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        header = self.rules_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        self.rules_table.setMaximumHeight(250)
        self.rules_table.cellClicked.connect(self.on_table_cell_clicked)
        
        # 设置自定义委托
        rules_delegate = LineEditDelegate(self.rules_table)
        self.rules_table.setItemDelegate(rules_delegate)
        
        layout.addWidget(self.rules_table)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_rule_btn = QPushButton("➕ 添加行")
        add_rule_btn.setObjectName("accentButton")
        add_rule_btn.clicked.connect(self.add_rule_row)
        
        remove_rule_btn = QPushButton("➖ 删除行")
        remove_rule_btn.setObjectName("normalButton")
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
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 添加拖拽提示
        drag_help_label = QLabel("💡 支持直接拖拽文件或文件夹到窗口中添加，也可使用下方按钮手动添加")
        drag_help_label.setObjectName("helpLabel")
        drag_help_label.setWordWrap(True)
        layout.addWidget(drag_help_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        add_files_btn = QPushButton("📁 添加文件")
        add_files_btn.setObjectName("accentButton")
        add_files_btn.clicked.connect(self.add_files)
        
        add_folder_btn = QPushButton("📂 添加文件夹")
        add_folder_btn.setObjectName("accentButton")
        add_folder_btn.clicked.connect(self.add_folder)
        
        remove_file_btn = QPushButton("➖ 删除行")
        remove_file_btn.setObjectName("normalButton")
        remove_file_btn.clicked.connect(self.remove_file_row)
        
        refresh_btn = QPushButton("🔄 刷新预览")
        refresh_btn.setObjectName("normalButton")
        refresh_btn.clicked.connect(self.refresh_preview)
        
        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.setObjectName("warningButton")
        clear_btn.clicked.connect(self.clear_file_list)
        
        btn_layout.addWidget(add_files_btn)
        btn_layout.addWidget(add_folder_btn)
        btn_layout.addWidget(remove_file_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 查找/替换功能区域
        find_replace_layout = QHBoxLayout()
        find_replace_layout.setSpacing(10)
        
        find_label = QLabel("查找:")
        find_label.setStyleSheet("font-weight: 500; color: #333333;")
        self.find_edit = QLineEdit()
        self.find_edit.setObjectName("modernLineEdit")
        self.find_edit.setPlaceholderText("输入要查找的文本...")
        
        replace_label = QLabel("替换:")
        replace_label.setStyleSheet("font-weight: 500; color: #333333;")
        self.replace_edit = QLineEdit()
        self.replace_edit.setObjectName("modernLineEdit")
        self.replace_edit.setPlaceholderText("输入替换后的文本...")
        
        find_replace_btn = QPushButton("🔍 查找并替换")
        find_replace_btn.setObjectName("accentButton")
        find_replace_btn.clicked.connect(self.find_and_replace_in_table)
        
        find_replace_layout.addWidget(find_label)
        find_replace_layout.addWidget(self.find_edit, 2)
        find_replace_layout.addWidget(replace_label)
        find_replace_layout.addWidget(self.replace_edit, 2)
        find_replace_layout.addWidget(find_replace_btn)
        
        layout.addLayout(find_replace_layout)
        
        # 文件列表表格
        self.file_table = TriStateSortTableWidget(0, 4)
        self.file_table.setObjectName("file_table")
        self.file_table.setHorizontalHeaderLabels(["#", "原始文件名", "新文件名", "状态"])
        
        # 设置表格属性
        self.file_table.setSortingEnabled(True)
        header = self.file_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 40)  # 设置行号列宽度为40像素
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.file_table.setAlternatingRowColors(True)
        self.file_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        
        
        # 设置自定义委托
        file_delegate = LineEditDelegate(self.file_table)
        self.file_table.setItemDelegateForColumn(0, file_delegate)
        
        # 连接单元格编辑完成信号
        self.file_table.itemChanged.connect(self.on_file_name_edited)
        self.file_table.cellClicked.connect(self.on_table_cell_clicked)
        
        layout.addWidget(self.file_table)
        
        
        return group

    def create_execute_section(self):
        """创建执行区域"""
        group = QGroupBox("🚀 执行与历史")
        group.setObjectName("settingsGroup")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(12)
        
        # 执行按钮
        self.execute_btn = QPushButton("🚀 开始执行重命名")
        self.execute_btn.setObjectName("executeButton")
        self.execute_btn.setMinimumHeight(54)
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
        self.undo_btn.setObjectName("warningButton")
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
        /* 主窗口样式 */
        QMainWindow {
            background-color: #f0f0f0;
            color: #333333;
        }
        
        /* 分组框样式 */
        QGroupBox {
            font-weight: 600;
            font-size: 13px;
            border: 1px solid #cccccc;
            border-radius: 10px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #ffffff;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 10px;
            color: #0078d7;
            font-size: 13px;
        }
        
        QGroupBox#settingsGroup {
            border: 1px solid #dcdcdc;
        }
        
        /* 标题样式 */
        #sectionLabel {
            color: #0078d7;
            font-weight: 600;
            font-size: 12px;
            padding: 4px 0;
        }
        
        #helpLabel {
            color: #666666;
            font-size: 11px;
            padding: 8px 12px;
            background-color: #e9e9e9;
            border-radius: 6px;
            border-left: 3px solid #0078d7;
        }
        
        /* 按钮样式 */
        QPushButton {
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
            font-size: 12px;
            min-width: 90px;
        }
        
        QPushButton#accentButton {
            background-color: #0078d7;
            color: white;
        }
        
        QPushButton#accentButton:hover {
            background-color: #005a9e;
        }
        
        QPushButton#accentButton:pressed {
            background-color: #004578;
        }
        
        QPushButton#normalButton {
            background-color: #e1e1e1;
            color: #333333;
            border: 1px solid #cccccc;
        }
        
        QPushButton#normalButton:hover {
            background-color: #d1d1d1;
            border-color: #bbbbbb;
        }
        
        QPushButton#executeButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #28a745, stop:1 #218838);
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
        
        QPushButton#executeButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #218838, stop:1 #1e7e34);
        }
        
        QPushButton#warningButton {
            background-color: #dc3545;
            color: white;
        }
        
        QPushButton#warningButton:hover {
            background-color: #c82333;
        }
        
        QPushButton:disabled {
            background-color: #e9ecef;
            color: #6c757d;
            border: 1px solid #ced4da;
        }
        
        /* 输入框样式 */
        QLineEdit#modernLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 8px;
            padding: 10px 12px;
            color: #333333;
            font-size: 12px;
        }
        
        QLineEdit#modernLineEdit:focus {
            border-color: #0078d7;
            background-color: #f8f9fa;
        }
        
        /* 表格样式 */
        QTableWidget#project_table, QTableWidget#rules_table, QTableWidget#file_table {
            background-color: #ffffff;
            alternate-background-color: #f8f9fa;
            border: 1px solid #cccccc;
            border-radius: 8px;
            gridline-color: #e0e0e0;
            color: #333333;
            font-size: 11px;
        }
        
        QTableWidget#project_table::item, QTableWidget#rules_table::item, QTableWidget#file_table::item {
            padding: 10px 8px;
            border: none;
        }
        
        QTableWidget#project_table::item:selected, QTableWidget#rules_table::item:selected, QTableWidget#file_table::item:selected {
            background-color: #dbeafe;
            color: #1e40af;
            font-weight: 600;
        }
        
        QHeaderView::section {
            background-color: #e9ecef;
            color: #495057;
            padding: 10px 8px;
            border: none;
            border-bottom: 1px solid #cccccc;
            border-right: 1px solid #cccccc;
            font-weight: 600;
            font-size: 11px;
        }
        
        QHeaderView::section:first {
            border-top-left-radius: 8px;
        }
        
        QHeaderView::section:last {
            border-top-right-radius: 8px;
            border-right: none;
        }
        
        /* 文本编辑器样式 */
        QTextEdit#modernTextEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 8px;
            color: #333333;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 11px;
            padding: 8px;
        }
        
        /* 进度条样式 */
        QProgressBar#modernProgressBar {
            border: none;
            border-radius: 4px;
            text-align: center;
            background-color: #e9ecef;
            color: #495057;
            font-weight: 600;
            font-size: 11px;
        }
        
        QProgressBar#modernProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #0078d7, stop:1 #005a9e);
            border-radius: 4px;
        }
        
        /* 分割器样式 */
        QSplitter#mainSplitter::handle {
            background-color: #e0e0e0;
            width: 4px;
        }
        
        QSplitter#mainSplitter::handle:hover {
            background-color: #0078d7;
        }
        
        /* 状态栏样式 */
        QStatusBar {
            background-color: #e9ecef;
            border-top: 1px solid #cccccc;
            color: #6c757d;
            font-size: 11px;
            padding: 4px 8px;
        }
        
        QStatusBar QLabel {
            padding: 2px 8px;
        }
        
        /* 滚动条样式 */
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 14px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #0078d7;
            border-radius: 6px;
            min-height: 30px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #005a9e;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #f0f0f0;
            height: 14px;
            border-radius: 7px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #0078d7;
            border-radius: 6px;
            min-width: 30px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #005a9e;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
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
            if code and name:
                self.project_codes[code] = name
        
        # 默认差分规则
        default_rules = [
            ("1", "+", "核玩翻页", "HWFY", "cn"),
            ("2", "+", "动画quiz-批量化", "BVC", "es"),
            ("4", "-", "核玩新版", "SLT", "en"),
        ]
        
        for diff, connector, full, abbr, lang in default_rules:
            self.add_rule_row(diff, connector, full, abbr, lang)
            if diff:
                self.diff_rules[diff] = (connector, full, abbr, lang)

    def initial_data_load(self):
        """在UI稳定后执行初始数据加载"""
        if os.path.exists(self.auto_config_file):
            self.load_auto_config()
        else:
            self.load_default_data()

    def add_project_row(self, code="", name=""):
        """添加项目行"""
        row = self.project_table.rowCount()
        self.project_table.insertRow(row)
        
        # 行号（不可编辑）
        row_num_item = CustomTableWidgetItem(str(row + 1))
        row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        code_item = CustomTableWidgetItem(code)
        name_item = CustomTableWidgetItem(name)
        
        self.project_table.setItem(row, 0, row_num_item)
        self.project_table.setItem(row, 1, code_item)
        self.project_table.setItem(row, 2, name_item)

    def add_rule_row(self, diff="", connector="+", full="", abbr="", lang=""):
        """添加差分规则行"""
        row = self.rules_table.rowCount()
        self.rules_table.insertRow(row)
        
        # 行号（不可编辑）
        row_num_item = CustomTableWidgetItem(str(row + 1))
        row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        diff_item = CustomTableWidgetItem(diff)
        connector_item = CustomTableWidgetItem(connector)
        full_item = CustomTableWidgetItem(full)
        abbr_item = CustomTableWidgetItem(abbr)
        lang_item = CustomTableWidgetItem(lang)
        
        self.rules_table.setItem(row, 0, row_num_item)
        self.rules_table.setItem(row, 1, diff_item)
        self.rules_table.setItem(row, 2, connector_item)
        self.rules_table.setItem(row, 3, full_item)
        self.rules_table.setItem(row, 4, abbr_item)
        self.rules_table.setItem(row, 5, lang_item)

    def remove_project_row(self):
        """删除选中的项目行"""
        self.remove_selected_rows(self.project_table)

    def remove_rule_row(self):
        """删除选中的差分规则行"""
        self.remove_selected_rows(self.rules_table)

    def remove_file_row(self):
        """删除选中的文件行"""
        self.remove_selected_rows(self.file_table)

    def remove_selected_rows(self, table):
        """通用删除行逻辑"""
        selected_rows = sorted(list(set(index.row() for index in table.selectedIndexes())), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的行")
            return

        deleted_data = []
        for row in selected_rows:
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            
            # 存储被删除行的数据
            deleted_data.append({
                "row": row,
                "data": row_data
            })
            table.removeRow(row)

        # 记录到撤销栈
        self.undo_stack.append({
            "action": "remove_rows",
            "table_name": table.objectName(),
            "data": deleted_data
        })
        self.log_history(f"🗑️ 从 {table.objectName()} 中删除了 {len(deleted_data)} 行\n")

    def undo_last_action(self):
        """撤销上一步操作"""
        if not self.undo_stack:
            self.log_history("⏪ 已经没什么好撤销的了\n")
            return

        last_action = self.undo_stack.pop()
        
        if last_action["action"] == "remove_rows":
            table_name = last_action["table_name"]
            table = self.findChild(QTableWidget, table_name)
            if table:
                deleted_data = sorted(last_action["data"], key=lambda x: x['row'])
                for item_data in deleted_data:
                    row = item_data["row"]
                    data = item_data["data"]
                    table.insertRow(row)
                    for col, text in enumerate(data):
                        table.setItem(row, col, CustomTableWidgetItem(text))
                self.log_history(f"⏪ 撤销删除操作，恢复了 {len(deleted_data)} 行\n")
        
        # 未来可以扩展其他撤销操作
        # elif last_action["action"] == "rename":
        #     ...

    def import_from_data_source(self):
        """打开对话框，从数据源导入项目代号"""
        dialog = ImportDialog(self.ignore_list, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        text_data, ignore_list = dialog.get_data()
        self.ignore_list = ignore_list  # 保存新的忽略列表
        if not text_data.strip():
            return

        # 1. 获取所有现有的差分规则（版本名全称）
        self._do_rule_config_update() # 确保内存中的规则是新的
        diff_rules = [rule[1] for rule in self.diff_rules.values()]
        if not diff_rules:
            QMessageBox.warning(self, "导入失败", "请先在“差分规则配置”中至少配置一条规则。")
            return

        # 按长度倒序排序，优先匹配更长的规则
        diff_rules.sort(key=len, reverse=True)

        # 2. 解析文本并提取信息
        lines = text_data.strip().split('\n')
        added_count = 0
        existing_codes = {self.project_table.item(r, 1).text() for r in range(self.project_table.rowCount())}

        for line in lines:
            line = line.strip()
            if not (line.lower().startswith("pre-shoot-") or line.lower().startswith("pre-kol-")):
                continue

            matched_rule = None
            original_rule_in_line = None
            # 查找匹配的规则
            for rule in diff_rules:
                # 使用正则表达式进行不区分大小写的搜索
                match = re.search(re.escape(rule), line, re.IGNORECASE)
                if match:
                    matched_rule = rule  # 这是来自 diff_rules 的键
                    original_rule_in_line = match.group(0) # 这是在行中实际匹配到的文本
                    break  # 找到第一个匹配就停止

            if not matched_rule:
                continue

            # 使用匹配到的规则分割字符串
            parts = line.split(original_rule_in_line)
            if len(parts) < 2:
                continue
            
            prefix_part = parts[0] # 规则之前的所有内容
            if not prefix_part:
                continue

            # 提取连接符和项目前缀
            connector = prefix_part[-1]
            if connector not in ['+', '-']:
                # 如果连接符不紧挨着规则，可能规则本身包含了连接符，需要更复杂的逻辑
                # 暂时跳过这种情况
                continue

            # 根据用户反馈，从数据源更新差分规则中的连接符
            for r in range(self.rules_table.rowCount()):
                full_name_item = self.rules_table.item(r, 3)  # "版本名全称" is at column 3
                if full_name_item and full_name_item.text() == matched_rule:
                    connector_item = self.rules_table.item(r, 2)  # "连接符" is at column 2
                    if connector_item:
                        connector_item.setText(connector)
                    else:
                        self.rules_table.setItem(r, 2, CustomTableWidgetItem(connector))
                    break  # 找到并更新后即可退出循环

            project_prefix = prefix_part[:-1]
            
            # 从项目前缀中提取项目代号
            # 逻辑：从 "pre-shoot-" 或 "pre-kol-" 之后开始提取
            code_match = re.search(r'pre-(?:shoot|kol)-(.*)', project_prefix)
            if not code_match:
                continue
            
            project_code = code_match.group(1).strip()
            
            # 应用忽略规则
            for ignored in ignore_list:
                project_code = project_code.replace(ignored, "")

            # 检查代号是否已存在
            if project_code and project_code not in existing_codes:
                self.add_project_row(project_code, project_prefix)
                existing_codes.add(project_code)
                added_count += 1
        
        if added_count > 0:
            self.log_history(f"📥 从数据源成功导入 {added_count} 个新项目。\n")
            QMessageBox.information(self, "导入成功", f"成功添加了 {added_count} 个新项目。")
            self._do_project_config_update() # 更新内存
        else:
            QMessageBox.information(self, "导入完成", "没有发现可添加的新项目。")

    def _do_project_config_update(self):
        """从表格实时更新项目配置到内存"""
        self.project_codes.clear()
        for row in range(self.project_table.rowCount()):
            code_item = self.project_table.item(row, 1)
            name_item = self.project_table.item(row, 2)
            if code_item and name_item:
                code = code_item.text().strip()
                name = name_item.text().strip()
                if code and name:
                    self.project_codes[code] = name

    def _do_rule_config_update(self):
        """从表格实时更新差分规则到内存"""
        self.diff_rules.clear()
        for row in range(self.rules_table.rowCount()):
            diff_item = self.rules_table.item(row, 1)
            connector_item = self.rules_table.item(row, 2)
            full_item = self.rules_table.item(row, 3)
            abbr_item = self.rules_table.item(row, 4)
            lang_item = self.rules_table.item(row, 5)
            
            if diff_item and connector_item and full_item and abbr_item and lang_item:
                diff = diff_item.text().strip()
                connector = connector_item.text().strip()
                full = full_item.text().strip()
                abbr = abbr_item.text().strip()
                lang = lang_item.text().strip()
                
                if diff and full and abbr and lang:
                    self.diff_rules[diff] = (connector, full, abbr, lang)
                    self.update_memory_bank(full, abbr, lang)

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

    def refresh_preview(self):
        """刷新文件列表和预览"""
        # 从表格更新内存中的配置
        self._do_project_config_update()
        self._do_rule_config_update()

        # 首先，检查文件系统中的文件状态
        self.check_file_status()
        # 然后，根据当前配置更新预览
        self.update_preview()
        
        # 更新状态栏
        self.status_label.setText("文件和预览已刷新")
        QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))

    def check_file_status(self):
        """检查文件列表中的文件是否存在和被修改"""
        if not self.files_to_rename:
            return
        
        updated_files = []
        changed_count = 0
        missing_count = 0
        
        for file_path, old_name in self.files_to_rename:
            dir_path = os.path.dirname(file_path)
            
            if os.path.exists(file_path):
                # 文件仍然存在，检查文件名是否有变化
                current_name = os.path.basename(file_path)
                if current_name != old_name:
                    changed_count += 1
                updated_files.append((file_path, current_name))
            else:
                # 文件不存在，可能已被重命名，尝试在同目录下查找
                if os.path.exists(dir_path):
                    # 获取目录中的所有文件
                    dir_files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                    
                    # 尝试找到可能的重命名文件（基于文件大小和修改时间）
                    old_file_found = False
                    original_stat = None
                    
                    # 如果原文件路径记录了统计信息，可以用来匹配
                    for new_file in dir_files:
                        new_file_path = os.path.join(dir_path, new_file)
                        # 简单的启发式匹配：如果找到了，就使用新的文件名
                        # 这里可以根据需要添加更复杂的匹配逻辑
                        if not any(nf[0] == new_file_path for nf in updated_files):
                            # 假设这是重命名后的文件
                            updated_files.append((new_file_path, new_file))
                            changed_count += 1
                            old_file_found = True
                            break
                    
                    if not old_file_found:
                        # 文件确实丢失了
                        missing_count += 1
                        # 保留原记录，但标记为丢失
                        updated_files.append((file_path, f"[文件丢失] {old_name}"))
                else:
                    missing_count += 1
                    updated_files.append((file_path, f"[目录不存在] {old_name}"))
        
        # 更新文件列表
        self.files_to_rename = updated_files
        self.update_file_count()
        
        # 显示刷新结果
        if changed_count > 0 or missing_count > 0:
            message = f"文件状态检查完成！\n"
            if changed_count > 0:
                message += f"检测到 {changed_count} 个文件名变化。\n"
            if missing_count > 0:
                message += f"发现 {missing_count} 个文件丢失。"
            # QMessageBox.information(self, "文件状态", message)

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
            
            # 行号（不可编辑）
            row_num_item = CustomTableWidgetItem(str(row + 1))
            row_num_item.setFlags(row_num_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            row_num_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # 设置单元格内容
            original_name_no_ext, original_ext = os.path.splitext(original_name)
            original_item = QTableWidgetItem(original_name_no_ext)
            original_item.setData(Qt.ItemDataRole.UserRole, file_path)  # 存储完整路径
            original_item.setData(Qt.ItemDataRole.UserRole + 1, original_ext) # 存储原始扩展名
            new_item = QTableWidgetItem(new_name)
            status_item = QTableWidgetItem(status)
            
            # 设置状态列为不可编辑
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            # 设置颜色
            if status == "✅":
                new_item.setForeground(QColor("#27ae60"))
                status_item.setForeground(QColor("#27ae60"))
            else:
                new_item.setForeground(QColor("#e74c3c"))
                status_item.setForeground(QColor("#e74c3c"))
            
            self.file_table.setItem(row, 0, row_num_item)
            self.file_table.setItem(row, 1, original_item)
            self.file_table.setItem(row, 2, new_item)
            self.file_table.setItem(row, 3, status_item)

    def generate_new_name(self, original_name_no_ext):
        """生成新文件名"""
        # 新的解析逻辑：基于项目代号匹配
        matched_code = None
        matched_project_info = None
        
        # 寻找匹配的项目代号（按长度从长到短排序，避免短代号误匹配长代号）
        sorted_codes = sorted(self.project_codes.items(), key=lambda x: len(x[0]), reverse=True)
        
        for code, project_info in sorted_codes:
            if code and original_name_no_ext.lower().startswith(code.lower()):
                matched_code = code
                matched_project_info = project_info
                break
        
        if not matched_code:
            return "[无匹配项目]", "❌"
        
        project_prefix = matched_project_info
        
        # 提取剩余部分并查找差分号
        remaining = original_name_no_ext[len(matched_code):]
        
        # 处理不同的分隔符格式：直接连接数字或用-分隔
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
        if len(rule_data) != 4:
            return f"[差分号{diff_num}规则不完整]", "❌"
        
        connector, full_name, abbr, lang = rule_data
        
        if not all([full_name.strip(), abbr.strip(), lang.strip()]):
            return f"[差分号{diff_num}规则数据不完整]", "❌"
        
        # 使用新的拼接逻辑
        date = self.date_edit.text()
        # 最终的文件名现在由 项目前缀 + 连接符 + 差分规则全称 构成
        final_name_part = f"{project_prefix}{connector}{full_name}"
        final_name = f"{date}_{final_name_part}_{lang}_{abbr}_1080x1920"
        
        return final_name, "✅"

    def on_file_name_edited(self, item):
        """处理文件名编辑事件"""
        if not item:
            return
        
        row = item.row()
        column = item.column()
        
        # 只处理第二列(原始文件名)的编辑,第一列是行号
        if column != 1:
            return

        # 暂时断开信号，避免循环触发
        self.file_table.itemChanged.disconnect(self.on_file_name_edited)
        
        try:
            # 从单元格的用户数据中获取原始文件路径和扩展名
            old_file_path = item.data(Qt.ItemDataRole.UserRole)
            if not old_file_path:
                return

            original_ext = item.data(Qt.ItemDataRole.UserRole + 1)
            old_file_name_no_ext = os.path.splitext(os.path.basename(old_file_path))[0]
            new_file_name_no_ext = item.text().strip()
            
            # 如果文件名没有变化,直接返回
            if new_file_name_no_ext == old_file_name_no_ext:
                return
            
            new_file_name = new_file_name_no_ext + original_ext
            old_file_name = old_file_name_no_ext + original_ext
        
            # 检查新文件名是否有效
            if not new_file_name_no_ext:
                QMessageBox.warning(self, "警告", "文件名不能为空")
                item.setText(old_file_name_no_ext)  # 恢复原文件名
                return
            
            # 检查文件名是否包含非法字符
            invalid_chars = '<>:"/\\|?*'
            if any(char in new_file_name_no_ext for char in invalid_chars):
                QMessageBox.warning(self, "警告", f"文件名不能包含以下字符: {invalid_chars}")
                item.setText(old_file_name_no_ext)  # 恢复原文件名
                return
        
            # 构建新的文件路径
            dir_path = os.path.dirname(old_file_path)
            new_file_path = os.path.join(dir_path, new_file_name)
            
            # 检查新文件是否已存在
            if os.path.exists(new_file_path) and new_file_path != old_file_path:
                reply = QMessageBox.question(
                    self, "文件已存在", 
                    f"文件 '{new_file_name}' 已存在,是否覆盖?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    item.setText(old_file_name_no_ext)  # 恢复原文件名
                    return
        
            # 尝试重命名文件
            try:
                if os.path.exists(old_file_path):
                    os.rename(old_file_path, new_file_path)
                    
                    # 更新表格项中的文件路径
                    item.setData(Qt.ItemDataRole.UserRole, new_file_path)

                    # 更新内部文件列表(为了保持数据一致性)
                    for i, (f_path, f_name) in enumerate(self.files_to_rename):
                        if f_path == old_file_path:
                            self.files_to_rename[i] = (new_file_path, new_file_name)
                            break
                    
                    # 记录操作历史
                    self.log_history(f"📝 直接编辑: {old_file_name} -> {new_file_name}\n")
                    
                    # 更新状态栏
                    self.status_label.setText(f"文件已重命名: {new_file_name}")
                    QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
                    
                    # 自动刷新预览,更新新文件名和状态列
                    self.refresh_preview()
                    
                else:
                    QMessageBox.warning(self, "错误", f"原文件不存在: {old_file_path}")
                    item.setText(old_file_name_no_ext)  # 恢复原文件名
                    
            except OSError as e:
                QMessageBox.critical(self, "重命名失败", f"无法重命名文件:\n{str(e)}")
                item.setText(old_file_name_no_ext)  # 恢复原文件名
        finally:
            # 重新连接信号
            self.file_table.itemChanged.connect(self.on_file_name_edited)

    def on_table_cell_clicked(self, row, column):
        """处理表格单元格点击事件"""
        table = self.sender()
        if not isinstance(table, QTableWidget):
            return

        # 如果点击的是行号列，则选中整行
        if column == 0:
            table.selectRow(row)
            return

        # 对于文件列表，只有第二列（原始文件名）是可编辑的
        if table is self.file_table and column != 1:
            return

        item = table.item(row, column)
        if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
            # 确保单元格被选中并获得焦点
            table.setCurrentItem(item)
            table.setFocus()
            # 立即进入编辑模式
            table.editItem(item)

    def update_file_count(self):
        """更新文件计数"""
        count = len(self.files_to_rename)
        self.file_count_label.setText(f"文件: {count}")

    def execute_rename(self):
        """执行重命名"""
        if not self.files_to_rename:
            QMessageBox.information(self, "提示", "文件列表为空，请先添加文件")
            return
        
        self.last_renames.clear()
        self.log_history("开始执行重命名操作...\n")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.files_to_rename))
        self.progress_bar.setValue(0)
        
        success_count = 0
        fail_count = 0
        
        # 遍历文件表格的可见行
        for i in range(self.file_table.rowCount()):
            # 更新进度
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()  # 更新界面

            # 从表格行中获取所有需要的信息
            original_item = self.file_table.item(i, 1)  # 原始文件名在第1列
            new_name_item = self.file_table.item(i, 2)  # 新文件名在第2列
            status_item = self.file_table.item(i, 3)    # 状态在第3列

            if not all([original_item, new_name_item, status_item]):
                continue

            file_path = original_item.data(Qt.ItemDataRole.UserRole)
            original_name_no_ext = original_item.text()
            original_ext = original_item.data(Qt.ItemDataRole.UserRole + 1)
            new_name_no_ext = new_name_item.text()
            
            # 确保新文件名包含扩展名
            if original_ext and not new_name_no_ext.endswith(original_ext):
                new_name = new_name_no_ext + original_ext
            else:
                new_name = new_name_no_ext

            original_name = original_name_no_ext + original_ext
            status = status_item.text()

            if not file_path:
                self.log_history(f"跳过: {original_name} (无法获取文件路径)\n")
                fail_count += 1
                continue
                
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
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        self.log_history(f"\n操作完成！成功: {success_count}, 失败/跳过: {fail_count}\n")
        
        # 清空文件列表并刷新
        self.files_to_rename.clear()
        self.update_preview()
        self.update_file_count()
        
        # 启用撤销按钮
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
        
        self.log_history(f"\n撤销完成！成功: {success_count}, 失败: {fail_count}\n")
        
        self.last_renames.clear()
        self.undo_btn.setEnabled(False)

    def log_history(self, message):
        """记录历史日志"""
        self.history_text.append(message.rstrip())
        # 滚动到底部
        cursor = self.history_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.history_text.setTextCursor(cursor)

    def get_current_config_data(self):
        """获取当前配置数据"""
        config_data = {
            "date": self.date_edit.text(),
            "project_codes": [],
            "diff_rules": [],
            "ignore_list": self.ignore_list
        }
        
        # 收集项目代号配置
        for row in range(self.project_table.rowCount()):
            code_item = self.project_table.item(row, 1)
            name_item = self.project_table.item(row, 2)
            
            code = code_item.text().strip() if code_item else ""
            name = name_item.text().strip() if name_item else ""
            
            # 只要有一项不为空就保存
            if code or name:
                config_data["project_codes"].append({
                    "code": code, 
                    "name": name
                })
        
        # 收集差分规则配置
        for row in range(self.rules_table.rowCount()):
            diff_item = self.rules_table.item(row, 1)
            connector_item = self.rules_table.item(row, 2)
            full_item = self.rules_table.item(row, 3)
            abbr_item = self.rules_table.item(row, 4)
            lang_item = self.rules_table.item(row, 5)
            
            diff = diff_item.text().strip() if diff_item else ""
            connector = connector_item.text().strip() if connector_item else "+"
            full = full_item.text().strip() if full_item else ""
            abbr = abbr_item.text().strip() if abbr_item else ""
            lang = lang_item.text().strip() if lang_item else ""
            
            # 只要有一项不为空就保存
            if diff or full or abbr or lang:
                config_data["diff_rules"].append({
                    "diff": diff,
                    "connector": connector,
                    "full_name": full,
                    "abbr": abbr,
                    "lang": lang
                })
        
        return config_data

    def save_current_config(self):
        """保存当前配置"""
        from PyQt6.QtWidgets import QInputDialog
        
        # 询问配置名称
        config_name, ok = QInputDialog.getText(
            self, "保存配置", 
            "请输入配置名称:",
            text=self.current_config_name
        )
        
        if ok and config_name.strip():
            config_name = config_name.strip()
            config_file = os.path.join(self.configs_dir, f"{config_name}.json")
            
            # 如果文件已存在,询问是否覆盖
            if os.path.exists(config_file):
                reply = QMessageBox.question(
                    self, "确认覆盖",
                    f"配置 '{config_name}' 已存在,是否覆盖?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            try:
                config_data = self.get_current_config_data()
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                
                self.current_config_name = config_name
                self.current_config_label.setText(config_name)
                QMessageBox.information(self, "成功", f"配置 '{config_name}' 已保存")
                self.log_history(f"💾 保存配置: {config_name}\n")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存配置失败:\n{str(e)}")

    def switch_config(self):
        """切换配置"""
        # 获取所有配置文件
        config_files = []
        if os.path.exists(self.configs_dir):
            for file in os.listdir(self.configs_dir):
                if file.endswith('.json'):
                    config_files.append(file[:-5])  # 去掉.json后缀
        
        if not config_files:
            QMessageBox.information(self, "提示", "暂无保存的配置,请先保存配置")
            return
        
        # 显示配置选择对话框
        dialog = MemoryBankDialog("选择配置", config_files, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_config = dialog.get_selected_value()
            if selected_config:
                self.load_config_by_name(selected_config)

    def load_config_by_name(self, config_name):
        """根据配置名称加载配置"""
        config_file = os.path.join(self.configs_dir, f"{config_name}.json")
        
        if not os.path.exists(config_file):
            QMessageBox.warning(self, "错误", f"配置文件不存在: {config_name}")
            return
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 加载日期
            if "date" in config_data:
                self.date_edit.setText(config_data["date"])
            
            self.ignore_list = config_data.get("ignore_list", [])

            # 清空并重新加载项目代号
            self.project_table.setRowCount(0)
            self.project_codes.clear()
            
            if "project_codes" in config_data and isinstance(config_data["project_codes"], list):
                for item in config_data["project_codes"]:
                    code = item.get("code", "")
                    name = item.get("name", "")
                    self.add_project_row(code, name)
                    if code and name:
                        self.project_codes[code] = name
            
            # 清空并重新加载差分规则
            self.rules_table.setRowCount(0)
            self.diff_rules.clear()
            
            if "diff_rules" in config_data and isinstance(config_data["diff_rules"], list):
                for item in config_data["diff_rules"]:
                    diff = item.get("diff", "")
                    connector = item.get("connector", "+")
                    full = item.get("full_name", "")
                    abbr = item.get("abbr", "")
                    lang = item.get("lang", "")
                    self.add_rule_row(diff, connector, full, abbr, lang)
                    if diff and full and abbr and lang:
                        self.diff_rules[diff] = (connector, full, abbr, lang)
            
            # 添加一些空行
            for _ in range(3):
                self.add_rule_row()
            
            # 更新当前配置名称
            self.current_config_name = config_name
            self.current_config_label.setText(config_name)
            
            self.log_history(f"📂 加载配置: {config_name}\n")
            self.update_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载配置失败:\n{str(e)}")

    def manage_configs(self):
        """管理配置"""
        # 获取所有配置文件
        config_files = []
        if os.path.exists(self.configs_dir):
            for file in os.listdir(self.configs_dir):
                if file.endswith('.json'):
                    config_files.append(file[:-5])
        
        if not config_files:
            QMessageBox.information(self, "提示", "暂无保存的配置")
            return
        
        # 创建管理对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("配置管理")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 说明标签
        info_label = QLabel("💡 选择配置进行操作")
        info_label.setStyleSheet("""
            color: #666666; 
            font-size: 11px; 
            padding: 8px 12px;
            background-color: #e9e9e9;
            border-radius: 6px;
        """)
        layout.addWidget(info_label)
        
        # 配置列表
        config_list = QListWidget()
        config_list.addItems(sorted(config_files))
        config_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:selected {
                background-color: #0078d7;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #e6f2fa;
            }
        """)
        layout.addWidget(config_list)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        rename_btn = QPushButton("✏️ 重命名")
        rename_btn.setObjectName("normalButton")
        rename_btn.clicked.connect(lambda: self.rename_config(config_list, dialog))
        
        delete_btn = QPushButton("🗑️ 删除")
        delete_btn.setObjectName("warningButton")
        delete_btn.clicked.connect(lambda: self.delete_config(config_list, dialog))
        
        export_btn = QPushButton("📤 导出")
        export_btn.setObjectName("accentButton")
        export_btn.clicked.connect(lambda: self.export_config(config_list))
        
        close_btn = QPushButton("关闭")
        close_btn.setObjectName("normalButton")
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout.addWidget(rename_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def show_update_history(self):
        """显示更新历史对话框"""
        update_log = {
            "1.42": [
                "【修复】大小写识别更智能了！现在程序能正确识别不同大小写的文件名（例如，`LION` 和 `lion` 都能被正确匹配），并且在从外部导入配置时，不会再意外地改变字母的大小写。",
                "【新增】更新历史功能！您现在可以点击“更新历史”按钮，随时查看软件的新功能和修复记录。"
            ]
        }

        dialog = QDialog(self)
        dialog.setWindowTitle("更新历史")
        dialog.setModal(True)
        dialog.resize(550, 400)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        history_text = QTextEdit()
        history_text.setReadOnly(True)
        
        html_content = ""
        for version, changes in sorted(update_log.items(), reverse=True):
            html_content += f"<h2>版本 {version}</h2>"
            html_content += "<ul>"
            for change in changes:
                html_content += f"<li>{change}</li>"
            html_content += "</ul>"
            html_content += "<hr>"

        history_text.setHtml(html_content)
        history_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 8px;
                font-size: 13px;
                padding: 10px;
            }
            h2 {
                color: #0078d7;
                font-size: 16px;
                font-weight: 600;
                border-bottom: 1px solid #e0e0e0;
                padding-bottom: 5px;
                margin-top: 10px;
            }
            ul {
                list-style-type: none;
                padding-left: 0px;
            }
            li {
                margin-bottom: 10px;
                line-height: 1.5;
            }
            hr {
                border: none;
                border-top: 1px solid #e0e0e0;
                margin: 15px 0;
            }
        """)
        
        layout.addWidget(history_text)

        close_btn = QPushButton("关闭")
        close_btn.setObjectName("accentButton")
        close_btn.clicked.connect(dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        dialog.exec()

    def rename_config(self, config_list, parent_dialog):
        """重命名配置"""
        from PyQt6.QtWidgets import QInputDialog
        
        current_item = config_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "提示", "请先选择一个配置")
            return
        
        old_name = current_item.text()
        new_name, ok = QInputDialog.getText(
            parent_dialog, "重命名配置",
            "请输入新的配置名称:",
            text=old_name
        )
        
        if ok and new_name.strip() and new_name != old_name:
            new_name = new_name.strip()
            old_file = os.path.join(self.configs_dir, f"{old_name}.json")
            new_file = os.path.join(self.configs_dir, f"{new_name}.json")
            
            if os.path.exists(new_file):
                QMessageBox.warning(parent_dialog, "错误", f"配置 '{new_name}' 已存在")
                return
            
            try:
                os.rename(old_file, new_file)
                current_item.setText(new_name)
                
                # 如果重命名的是当前配置,更新显示
                if self.current_config_name == old_name:
                    self.current_config_name = new_name
                    self.current_config_label.setText(new_name)
                
                QMessageBox.information(parent_dialog, "成功", f"配置已重命名为 '{new_name}'")
                self.log_history(f"✏️ 重命名配置: {old_name} -> {new_name}\n")
            except Exception as e:
                QMessageBox.critical(parent_dialog, "错误", f"重命名失败:\n{str(e)}")

    def delete_config(self, config_list, parent_dialog):
        """删除配置"""
        current_item = config_list.currentItem()
        if not current_item:
            QMessageBox.warning(parent_dialog, "提示", "请先选择一个配置")
            return
        
        config_name = current_item.text()
        
        reply = QMessageBox.question(
            parent_dialog, "确认删除",
            f"确定要删除配置 '{config_name}' 吗?\n此操作不可恢复!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            config_file = os.path.join(self.configs_dir, f"{config_name}.json")
            try:
                os.remove(config_file)
                config_list.takeItem(config_list.row(current_item))
                QMessageBox.information(parent_dialog, "成功", f"配置 '{config_name}' 已删除")
                self.log_history(f"🗑️ 删除配置: {config_name}\n")
                
                # 如果删除的是当前配置,重置为默认
                if self.current_config_name == config_name:
                    self.current_config_name = "默认配置"
                    self.current_config_label.setText("默认配置")
            except Exception as e:
                QMessageBox.critical(parent_dialog, "错误", f"删除失败:\n{str(e)}")

    def export_config(self, config_list):
        """导出配置到外部文件"""
        current_item = config_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一个配置")
            return
        
        config_name = current_item.text()
        config_file = os.path.join(self.configs_dir, f"{config_name}.json")
        
        # 选择导出位置
        export_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", f"{config_name}.json",
            "JSON文件 (*.json);;所有文件 (*.*)"
        )
        
        if export_path:
            try:
                import shutil
                shutil.copy2(config_file, export_path)
                QMessageBox.information(self, "成功", f"配置已导出到:\n{export_path}")
                self.log_history(f"📤 导出配置: {config_name} -> {export_path}\n")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败:\n{str(e)}")

    def save_all_config(self):
        """保存完整配置到外部JSON文件(保留原有功能)"""
        config_data = self.get_current_config_data()
        
        # 选择保存位置
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
                
                # 加载日期
                if "date" in config_data:
                    self.date_edit.setText(config_data["date"])
                
                self.ignore_list = config_data.get("ignore_list", [])

                # 清空并重新加载项目代号
                self.project_table.setRowCount(0)
                self.project_codes.clear()
                
                if "project_codes" in config_data and isinstance(config_data["project_codes"], list):
                    for item in config_data["project_codes"]:
                        code = item.get("code", "")
                        name = item.get("name", "")
                        self.add_project_row(code, name)
                        if code and name:
                            self.project_codes[code] = name
                
                # 清空并重新加载差分规则
                self.rules_table.setRowCount(0)
                self.diff_rules.clear()
                
                if "diff_rules" in config_data and isinstance(config_data["diff_rules"], list):
                    for item in config_data["diff_rules"]:
                        diff = item.get("diff", "")
                        connector = item.get("connector", "+")
                        full = item.get("full_name", "")
                        abbr = item.get("abbr", "")
                        lang = item.get("lang", "")
                        self.add_rule_row(diff, connector, full, abbr, lang)
                        if diff and full and abbr and lang:
                            self.diff_rules[diff] = (connector, full, abbr, lang)
                
                # 添加一些空行
                for _ in range(3):
                    self.add_rule_row()
                
                QMessageBox.information(self, "成功", f"配置已从以下文件加载：\n{file_path}")
                self.update_preview()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载配置失败：\n{str(e)}")

    def load_window_config(self):
        """加载窗口配置"""
        try:
            if os.path.exists(self.window_config_file):
                with open(self.window_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 设置窗口大小和位置
                if "geometry" in config:
                    geometry = config["geometry"]
                    if "x" in geometry and "y" in geometry and "width" in geometry and "height" in geometry:
                        self.setGeometry(geometry["x"], geometry["y"], geometry["width"], geometry["height"])
                
                # 设置窗口状态（最大化等）
                if "maximized" in config and config["maximized"]:
                    self.showMaximized()
                    
        except Exception as e:
            # 如果加载失败，使用默认配置
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
                
                # 加载上次使用的配置名称
                last_config_name = config_data.get("last_config_name", "默认配置")
                
                # 如果存在上次使用的配置,则加载它
                if last_config_name != "默认配置" and os.path.exists(os.path.join(self.configs_dir, f"{last_config_name}.json")):
                    self.load_config_by_name(last_config_name)
                else:
                    # 否则,加载默认的 auto_config.json
                    self.load_config_data(config_data)

                print("自动加载配置成功")
                
        except Exception as e:
            print(f"自动加载配置失败: {e}")

    def load_config_data(self, config_data):
        """加载配置数据到UI"""
        # 不加载日期,保持使用当前系统日期
        self.ignore_list = config_data.get("ignore_list", [])
        
        # 清空并重新加载项目代号
        self.project_table.setRowCount(0)
        self.project_codes.clear()
        
        if "project_codes" in config_data and isinstance(config_data["project_codes"], list):
            for item in config_data["project_codes"]:
                code = item.get("code", "")
                name = item.get("name", "")
                self.add_project_row(code, name)
                if code and name:
                    self.project_codes[code] = name
        
        # 清空并重新加载差分规则
        self.rules_table.setRowCount(0)
        self.diff_rules.clear()
        
        if "diff_rules" in config_data and isinstance(config_data["diff_rules"], list):
            for item in config_data["diff_rules"]:
                diff = item.get("diff", "")
                connector = item.get("connector", "+")
                full = item.get("full_name", "")
                abbr = item.get("abbr", "")
                lang = item.get("lang", "")
                self.add_rule_row(diff, connector, full, abbr, lang)
                if diff and full and abbr and lang:
                    self.diff_rules[diff] = (connector, full, abbr, lang)

        # 恢复表格的排序状态
        if "tables_sort_state" in config_data:
            states = config_data["tables_sort_state"]
            if "project_table" in states:
                state = states["project_table"]
                self.project_table.sortByColumn(state['column'], Qt.SortOrder(state['order']))
            if "rules_table" in states:
                state = states["rules_table"]
                self.rules_table.sortByColumn(state['column'], Qt.SortOrder(state['order']))
            if "file_table" in states:
                state = states["file_table"]
                self.file_table.sortByColumn(state['column'], Qt.SortOrder(state['order']))

        # 添加一些空行以保持与手动加载一致的体验
        for _ in range(3):
            self.add_rule_row()

    def save_auto_config(self):
        """自动保存当前配置"""
        try:
            # 获取当前配置数据
            config_data = self.get_current_config_data()

            # 如果当前配置不是“默认配置”，则保存到对应的配置文件
            if self.current_config_name != "默认配置":
                config_file = os.path.join(self.configs_dir, f"{self.current_config_name}.json")
                try:
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=2)
                    print(f"自动更新配置: {self.current_config_name}")
                except Exception as e:
                    print(f"自动更新配置 '{self.current_config_name}' 失败: {e}")
            
            # 添加上次使用的配置名称
            config_data["last_config_name"] = self.current_config_name
            
            # 保存表格的排序状态
            try:
                config_data['tables_sort_state'] = {
                    'project_table': {
                        'column': self.project_table.horizontalHeader().sortIndicatorSection(),
                        'order': int(self.project_table.horizontalHeader().sortIndicatorOrder().value)
                    },
                    'rules_table': {
                        'column': self.rules_table.horizontalHeader().sortIndicatorSection(),
                        'order': int(self.rules_table.horizontalHeader().sortIndicatorOrder().value)
                    },
                    'file_table': {
                        'column': self.file_table.horizontalHeader().sortIndicatorSection(),
                        'order': int(self.file_table.horizontalHeader().sortIndicatorOrder().value)
                    }
                }
            except Exception as sort_error:
                print(f"保存排序状态失败: {sort_error}")
                config_data['tables_sort_state'] = {
                    'project_table': {'column': -1, 'order': 0},
                    'rules_table': {'column': -1, 'order': 0},
                    'file_table': {'column': -1, 'order': 0}
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
                
                # 转换为set类型
                self.memory_bank = {
                    "version_names": set(data.get("version_names", [])),
                    "abbreviations": set(data.get("abbreviations", [])),
                    "languages": set(data.get("languages", []))
                }
                print("记忆库加载成功")
        except Exception as e:
            print(f"加载记忆库失败: {e}")
            # 使用默认记忆库
            self.memory_bank = {
                "version_names": set(),
                "abbreviations": set(),
                "languages": set()
            }

    def save_memory_bank(self):
        """保存记忆库"""
        try:
            # 转换为list类型以便JSON序列化
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
        
        # 移除自动保存，只在关闭软件时保存
        # self.save_memory_bank()

    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.rules_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        column = item.column()
        
        # 只在版本名全称(2)、版本名缩写(3)、语言(4)列显示菜单
        if column not in [2, 3, 4]:
            return
        
        # 创建右键菜单
        menu = QMenu(self)
        
        # 根据列确定菜单项
        if column == 2:
            memory_data = list(self.memory_bank["version_names"])
            menu_title = "📝 选择版本名全称"
        elif column == 3:
            memory_data = list(self.memory_bank["abbreviations"])
            menu_title = "🔤 选择版本名缩写"
        elif column == 4:
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
                background-color: #252525;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                background-color: transparent;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 12px;
            }
            QMenu::item:selected {
                background-color: #5b9dd9;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #888888;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3a3a3a;
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
    
    def show_memory_dialog_for_cell(self, row, column):
        """为特定单元格显示记忆库对话框"""
        # 获取对应的记忆库数据
        if column == 2:  # 版本名全称
            memory_data = list(self.memory_bank["version_names"])
            title = "选择版本名全称"
        elif column == 3:  # 版本名缩写
            memory_data = list(self.memory_bank["abbreviations"])
            title = "选择版本名缩写"
        elif column == 4:  # 语言
            memory_data = list(self.memory_bank["languages"])
            title = "选择语言"
        else:
            return
        
        if not memory_data:
            QMessageBox.information(self, "提示", "记忆库中暂无相关数据")
            return
        
        # 显示选择对话框
        selected_value = self.show_memory_dialog(title, memory_data)
        if selected_value:
            self.set_cell_value(row, column, selected_value)

    def show_memory_dialog(self, title, data_list):
        """显示记忆库选择对话框"""
        dialog = MemoryBankDialog(title, data_list, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.get_selected_value()
        return None

    def dragEnterEvent(self, event: QDragEnterEvent):
        """处理拖拽进入事件"""
        # 检查是否包含文件URL
        if event.mimeData().hasUrls():
            # 检查是否至少有一个有效的文件或文件夹
            urls = event.mimeData().urls()
            has_valid_items = False
            
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    if os.path.exists(file_path):
                        has_valid_items = True
                        break
            
            if has_valid_items:
                event.acceptProposedAction()
                # 更新状态栏提示
                self.status_label.setText("松开鼠标以添加文件...")
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        """处理拖拽释放事件"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            files_to_add = []
            folders_processed = 0
            files_processed = 0
            
            for url in urls:
                if url.isLocalFile():
                    file_path = url.toLocalFile()
                    
                    if os.path.isfile(file_path):
                        # 单个文件
                        files_to_add.append(file_path)
                        files_processed += 1
                    elif os.path.isdir(file_path):
                        # 文件夹 - 递归获取所有文件
                        folder_files = self.get_files_from_folder(file_path)
                        files_to_add.extend(folder_files)
                        folders_processed += 1
                        files_processed += len(folder_files)
            
            if files_to_add:
                # 添加文件到列表
                self.add_files_to_list(files_to_add)
                
                # 显示添加结果
                message = f"已添加 {len(files_to_add)} 个文件"
                if folders_processed > 0:
                    message += f"（来自 {folders_processed} 个文件夹）"
                
                self.status_label.setText(message)
                QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
                
                # 记录到历史
                self.log_history(f"🎯 拖拽添加: {len(files_to_add)} 个文件\n")
            else:
                self.status_label.setText("未找到有效文件")
                QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
            
            event.acceptProposedAction()
        else:
            event.ignore()

    def get_files_from_folder(self, folder_path):
        """从文件夹中递归获取所有文件"""
        files = []
        try:
            folder_path_obj = Path(folder_path)
            # 递归遍历文件夹中的所有文件
            for file_path in folder_path_obj.rglob('*'):
                if file_path.is_file():
                    files.append(str(file_path))
        except Exception as e:
            print(f"处理文件夹时出错 {folder_path}: {e}")
        
        return files

    def find_and_replace_in_table(self):
        """在文件列表中查找并替换文本"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()

        if not find_text:
            QMessageBox.warning(self, "警告", "请输入要查找的文本")
            return

        replaced_count = 0
        affected_rows = []

        # 遍历文件表格进行查找和替换
        for row in range(self.file_table.rowCount()):
            # 操作第一列“原始文件名”
            original_name_item = self.file_table.item(row, 1)
            if original_name_item:
                original_name = original_name_item.text()
                
                if find_text in original_name:
                    # 执行替换
                    updated_name = original_name.replace(find_text, replace_text)
                    # setText会触发on_file_name_edited，从而实现文件重命名
                    original_name_item.setText(updated_name)
                    
                    replaced_count += 1
                    affected_rows.append(row + 1)
        
        # 显示结果
        if replaced_count > 0:
            message = f"成功替换 {replaced_count} 处\n"
            message += f"涉及行号: {', '.join(map(str, affected_rows[:10]))}"
            if len(affected_rows) > 10:
                message += f" 等共 {len(affected_rows)} 行"
            QMessageBox.information(self, "替换完成", message)
            
            # 记录到历史
            self.log_history(f"🔍 查找替换: '{find_text}' -> '{replace_text}' ({replaced_count}处)\n")
            
            # 更新状态栏
            self.status_label.setText(f"已替换 {replaced_count} 处")
            QTimer.singleShot(3000, lambda: self.status_label.setText("就绪"))
        else:
            QMessageBox.information(self, "查找结果", f"未找到 '{find_text}'")

    def setup_date_timer(self):
        """设置一个定时器来自动更新日期"""
        self.date_timer = QTimer(self)
        self.date_timer.timeout.connect(self.update_date_if_needed)
        self.date_timer.start(1000)  # 每秒检查一次

    def update_date_if_needed(self):
        """如果日期已更改，则更新日期编辑框"""
        current_date = datetime.now().strftime("%y%m%d")
        if self.date_edit.text() != current_date:
            self.date_edit.setText(current_date)

    def check_for_updates(self):
        """手动检查更新"""
        from PyQt6.QtWidgets import QProgressDialog
        import requests
        
        # 显示检查进度对话框
        progress = QProgressDialog("正在检查更新...", "取消", 0, 0, self)
        progress.setWindowTitle("检查更新")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()
        
        try:
            # GitHub API URL
            api_url = "https://api.github.com/repos/ESVigan/auto-renamer/releases/latest"
            response = requests.get(api_url, timeout=10)
            progress.close()
            
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get("tag_name", "")
                current_version = "v1.42"
                
                if latest_version and latest_version != current_version:
                    # 发现新版本
                    release_notes = release_data.get("body", "暂无更新说明")
                    message = f"发现新版本：{latest_version}\n"
                    message += f"当前版本：{current_version}\n\n"
                    message += f"更新内容：\n{release_notes}\n\n"
                    message += "是否立即前往GitHub下载？"
                    
                    reply = QMessageBox.question(
                        self, "发现新版本", message,
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        import webbrowser
                        webbrowser.open("https://github.com/ESVigan/auto-renamer/releases/latest")
                else:
                    QMessageBox.information(self, "检查更新", "您使用的已是最新版本！")
            else:
                QMessageBox.warning(self, "检查更新失败", f"无法连接到更新服务器\n错误代码：{response.status_code}")
                
        except requests.exceptions.Timeout:
            progress.close()
            QMessageBox.warning(self, "检查更新失败", "连接超时，请检查网络连接")
        except requests.exceptions.RequestException as e:
            progress.close()
            QMessageBox.warning(self, "检查更新失败", f"网络错误：{str(e)}")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "检查更新失败", f"发生未知错误：{str(e)}")
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, "检查更新失败", f"发生未知错误：{str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        # 强制提交任何正在编辑的单元格，以防数据丢失
        # 通过将当前项设置为空，可以触发委托（delegate）将编辑器中的数据写回模型
        if self.project_table.state() == QAbstractItemView.State.EditingState:
            self.project_table.setCurrentItem(None)
        if self.rules_table.state() == QAbstractItemView.State.EditingState:
            self.rules_table.setCurrentItem(None)

        # 在保存前，从UI表格强制更新内存中的配置，确保所有编辑都已同步
        self._do_project_config_update()
        self._do_rule_config_update()

        # 保存窗口配置
        self.save_window_config()
        
        # 自动保存当前配置
        self.save_auto_config()
        
        # 保存记忆库
        self.save_memory_bank()
        
        # 接受关闭事件
        event.accept()
