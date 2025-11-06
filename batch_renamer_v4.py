import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import json
from tkinter import font

# For drag-and-drop functionality
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

class ModernBatchRenamerApp:
    def __init__(self, root):
        self.root = root
        
        # 配置文件路径
        self.window_config_file = "window_config.json"
        self.auto_config_file = "auto_config.json"
        
        self.setup_modern_ui()
        
        # Data storage
        self.files_to_rename = []
        self.last_renames = []
        self.project_codes = {}  # 项目代号映射表
        self.diff_rules = {}     # 差分规则映射表
        
        self.create_ui()
        self.load_default_data()
        
        # 加载窗口配置
        self.load_window_config()
        
        # 加载自动保存的配置
        self.load_auto_config()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_modern_ui(self):
        """设置现代化UI主题和样式"""
        self.root.title("批量文件重命名工具 v4.0")
        self.root.geometry("1000x800")
        
        # 设置现代化配色
        self.colors = {
            'bg_primary': '#2b2b2b',      # 主背景 - 深灰
            'bg_secondary': '#3c3c3c',    # 次背景 - 浅灰
            'bg_accent': '#4a90e2',       # 强调色 - 蓝
            'text_primary': '#ffffff',    # 主文字 - 白
            'text_secondary': '#cccccc',  # 次文字 - 浅灰
            'success': '#27ae60',         # 成功 - 绿
            'warning': '#f39c12',         # 警告 - 橙
            'danger': '#e74c3c',          # 危险 - 红
            'border': '#555555',          # 边框 - 灰
        }
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        # 配置ttk样式
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # 自定义样式
        self.style.configure('Modern.TFrame', 
                           background=self.colors['bg_primary'],
                           relief='flat',
                           borderwidth=0)
        
        self.style.configure('Card.TFrame',
                           background=self.colors['bg_secondary'],
                           relief='raised',
                           borderwidth=1)
        
        self.style.configure('Modern.TLabel',
                           background=self.colors['bg_primary'],
                           foreground=self.colors['text_primary'],
                           font=('Microsoft YaHei UI', 10))
        
        self.style.configure('Title.TLabel',
                           background=self.colors['bg_primary'],
                           foreground=self.colors['text_primary'],
                           font=('Microsoft YaHei UI', 12, 'bold'))
        
        self.style.configure('Modern.TEntry',
                           fieldbackground=self.colors['bg_secondary'],
                           foreground=self.colors['text_primary'],
                           borderwidth=1,
                           relief='solid')
        
        self.style.configure('Accent.TButton',
                           background=self.colors['bg_accent'],
                           foreground='white',
                           borderwidth=0,
                           focuscolor='none')
        
        self.style.map('Accent.TButton',
                      background=[('active', '#357abd')])

    def create_ui(self):
        """创建现代化UI界面"""
        main_container = ttk.Frame(self.root, style='Modern.TFrame', padding="20")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 标题区域
        self.create_header(main_container)
        
        # 内容区域
        content_frame = ttk.Frame(main_container, style='Modern.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # 左侧配置区域
        left_panel = ttk.Frame(content_frame, style='Modern.TFrame')
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.create_global_settings(left_panel)
        self.create_project_codes_section(left_panel)
        self.create_diff_rules_section(left_panel)
        
        # 右侧文件处理区域
        right_panel = ttk.Frame(content_frame, style='Modern.TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_file_section(right_panel)
        self.create_execute_section(right_panel)

    def create_header(self, parent):
        """创建标题区域"""
        header_frame = ttk.Frame(parent, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="智能批量重命名工具", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # 配置管理按钮
        config_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        config_frame.pack(side=tk.RIGHT)
        
        ttk.Button(config_frame, text="💾 保存配置", command=self.save_all_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_frame, text="📂 加载配置", command=self.load_config_file).pack(side=tk.LEFT, padx=5)
        
        version_label = ttk.Label(header_frame, text="v4.0", style='Modern.TLabel')
        version_label.pack(side=tk.RIGHT, padx=(10, 0))

    def create_global_settings(self, parent):
        """创建全局设置区域"""
        card = self.create_card(parent, "全局设置")
        
        # 日期设置
        date_frame = ttk.Frame(card, style='Modern.TFrame')
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="日期 (YYMMDD):", style='Modern.TLabel').pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value="251013")
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, style='Modern.TEntry', width=15)
        date_entry.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.date_var.trace_add("write", self.update_preview)

    def create_project_codes_section(self, parent):
        """创建项目代号配置区域"""
        card = self.create_card(parent, "项目代号配置")
        
        # 说明文字
        help_text = ttk.Label(card, text="直接在表格中输入编辑，支持多行配置", 
                             style='Modern.TLabel', font=('Microsoft YaHei UI', 9))
        help_text.pack(anchor='w', pady=(0, 10))
        
        # 创建可编辑表格
        self.create_editable_project_table(card)
        
        # 按钮区域
        btn_frame = ttk.Frame(card, style='Modern.TFrame')
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="➕ 添加行", command=self.add_project_row, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="➖ 删除行", command=self.remove_project_row).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_project_config).pack(side=tk.RIGHT)

    def create_diff_rules_section(self, parent):
        """创建差分规则配置区域"""
        card = self.create_card(parent, "差分规则配置")
        
        # 说明文字
        help_text = ttk.Label(card, text="直接在表格中输入编辑，所有项目共用", 
                             style='Modern.TLabel', font=('Microsoft YaHei UI', 9))
        help_text.pack(anchor='w', pady=(0, 10))
        
        # 创建可编辑表格
        self.create_editable_rules_table(card)
        
        # 按钮区域
        btn_frame = ttk.Frame(card, style='Modern.TFrame')
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="➕ 添加行", command=self.add_rule_row, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="➖ 删除行", command=self.remove_rule_row).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_rule_config).pack(side=tk.RIGHT)

    def create_file_section(self, parent):
        """创建文件处理区域"""
        card = self.create_card(parent, "文件列表与预览")
        
        # 文件操作按钮
        btn_frame = ttk.Frame(card, style='Modern.TFrame')
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📁 添加文件", command=self.add_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="📂 添加文件夹", command=self.add_folder).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ 清空列表", command=self.clear_file_list).pack(side=tk.LEFT)
        
        # 文件列表
        list_frame = ttk.Frame(card, style='Modern.TFrame')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        file_cols = ("原始文件名", "新文件名", "状态", "操作")
        self.file_tree = ttk.Treeview(list_frame, columns=file_cols, show='headings')
        
        self.file_tree.heading("原始文件名", text="原始文件名")
        self.file_tree.heading("新文件名", text="新文件名")
        self.file_tree.heading("状态", text="状态")
        self.file_tree.heading("操作", text="操作")
        
        self.file_tree.column("原始文件名", width=200)
        self.file_tree.column("新文件名", width=350)
        self.file_tree.column("状态", width=80)
        self.file_tree.column("操作", width=60, anchor='center')
        
        # 滚动条
        file_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scroll.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        file_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定事件
        self.file_tree.bind("<Double-1>", self.on_double_click)
        self.file_tree.bind("<Button-1>", self.on_click)
        
        # 拖拽支持
        if DND_SUPPORT:
            self.file_tree.drop_target_register(DND_FILES)
            self.file_tree.dnd_bind('<<Drop>>', self.handle_drop)
            drop_text = "💡 支持拖拽文件到此处"
        else:
            drop_text = "⚠️ 需要安装 tkinterdnd2 库来支持拖拽功能"
        
        ttk.Label(card, text=drop_text, style='Modern.TLabel').pack(pady=(10, 0))

    def create_execute_section(self, parent):
        """创建执行区域"""
        card = self.create_card(parent, "执行与历史")
        
        # 执行按钮
        self.exec_button = ttk.Button(card, text="🚀 开始执行重命名", 
                                     command=self.execute_rename, 
                                     style='Accent.TButton')
        self.exec_button.pack(fill=tk.X, pady=(0, 10), ipady=10)
        
        # 历史记录
        history_frame = ttk.Frame(card, style='Modern.TFrame')
        history_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(history_frame, text="操作历史:", style='Modern.TLabel').pack(anchor='w')
        
        # 历史文本区域
        text_frame = ttk.Frame(history_frame, style='Modern.TFrame')
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        self.history_text = tk.Text(text_frame, height=6, state="disabled",
                                   bg=self.colors['bg_secondary'], 
                                   fg=self.colors['text_primary'],
                                   font=('Microsoft YaHei UI', 9),
                                   relief='solid', borderwidth=1)
        
        history_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=history_scroll.set)
        
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 撤销按钮
        self.undo_button = ttk.Button(card, text="⏪ 撤销上次操作", 
                                     command=self.undo_rename, 
                                     state="disabled")
        self.undo_button.pack(fill=tk.X, pady=(10, 0))

    def create_card(self, parent, title):
        """创建卡片样式的容器"""
        # 外层容器
        outer_frame = ttk.Frame(parent, style='Modern.TFrame')
        outer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 标题
        title_label = ttk.Label(outer_frame, text=title, style='Title.TLabel')
        title_label.pack(anchor='w', pady=(0, 10))
        
        # 内容卡片
        card = ttk.Frame(outer_frame, style='Card.TFrame', padding="15")
        card.pack(fill=tk.BOTH, expand=True)
        
        return card

    def create_editable_project_table(self, parent):
        """创建可编辑的项目代号表格"""
        # 使用网格布局创建类似Excel的可编辑表格
        table_frame = ttk.Frame(parent, style='Modern.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 表头
        header_frame = ttk.Frame(table_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(header_frame, text="项目代号", style='Modern.TLabel', 
                 width=15, relief='solid', borderwidth=1, anchor='center').pack(side=tk.LEFT, padx=1)
        ttk.Label(header_frame, text="完整项目名", style='Modern.TLabel', 
                 width=40, relief='solid', borderwidth=1, anchor='center').pack(side=tk.LEFT, padx=1)
        
        # 可滚动的内容区域
        canvas = tk.Canvas(table_frame, height=150, bg=self.colors['bg_secondary'])
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.project_entries = []
        self.project_frame = scrollable_frame
        
        # 添加初始行
        self.load_project_data()

    def load_project_data(self):
        """加载项目数据到可编辑表格"""
        # 默认项目数据
        default_projects = [
            ("洗衣店偷衣服", "Pre-shoot-洗衣店偷衣服-C02---华容道平铺02-tileflower"),
            ("插队的补偿", "Pre-shoot-插队的补偿-C01-华容道平铺02tileflower"), 
            ("无语言偷看1", "pre-shoot-无语言偷看1"),
            ("", ""),  # 空行供用户输入
            ("", ""),
        ]
        
        for i, (code, name) in enumerate(default_projects):
            self.add_project_entry_row(code, name)
            if code and name:
                self.project_codes[code] = name
    
    def add_project_entry_row(self, code="", name=""):
        """添加项目输入行"""
        row_frame = ttk.Frame(self.project_frame, style='Modern.TFrame')
        row_frame.pack(fill=tk.X, pady=1)
        
        check_var = tk.BooleanVar(value=False)
        check = ttk.Checkbutton(row_frame, variable=check_var)
        check.pack(side=tk.LEFT, padx=(0, 5))

        code_var = tk.StringVar(value=code)
        name_var = tk.StringVar(value=name)
        
        code_entry = ttk.Entry(row_frame, textvariable=code_var, width=15, style='Modern.TEntry')
        code_entry.pack(side=tk.LEFT, padx=1)
        
        name_entry = ttk.Entry(row_frame, textvariable=name_var, width=40, style='Modern.TEntry')  
        name_entry.pack(side=tk.LEFT, padx=1)
        
        # 绑定修改事件
        code_var.trace_add("write", self.update_project_config)
        name_var.trace_add("write", self.update_project_config)
        
        self.project_entries.append((check_var, code_var, name_var, row_frame))

    def add_project_row(self):
        """添加新的项目行"""
        self.add_project_entry_row()

    def remove_project_row(self):
        """删除选中的项目行"""
        # 从后往前遍历以安全删除
        for i in range(len(self.project_entries) - 1, -1, -1):
            check_var, _, _, row_frame = self.project_entries[i]
            if check_var.get():
                row_frame.destroy()
                self.project_entries.pop(i)
        self.update_project_config()

    def save_project_config(self):
        """保存项目配置"""
        self.update_project_config()
        messagebox.showinfo("提示", "项目配置已保存！")

    def update_project_config(self, *args):
        """更新项目配置"""
        self.project_codes.clear()
        
        for _, code_var, name_var, _ in self.project_entries:
            code = code_var.get().strip()
            name = name_var.get().strip()
            if code and name:
                self.project_codes[code] = name
        
        self.update_preview()

    def load_default_data(self):
        """加载默认差分规则数据"""
        # 默认差分规则
        default_rules = [
            ("1", "核玩翻页", "HWFY", "cn"),
            ("2", "动画quiz-批量化", "BVC", "es"), 
            ("4", "核玩新版", "SLT", "en"),
            ("", "", "", ""),
            ("", "", "", ""),
        ]
        
        for rule in default_rules:
            self.add_rule_entry_row(*rule)
        
        self.update_rule_config()

    # ========== 事件处理方法 ==========

    def create_editable_rules_table(self, parent):
        """创建可编辑的差分规则表格"""
        table_frame = ttk.Frame(parent, style='Modern.TFrame')
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 表头
        header_frame = ttk.Frame(table_frame, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        headers = ["✓", "差分号", "版本名全称", "版本名缩写", "语言"]
        widths = [3, 8, 20, 12, 8]
        
        for header, width in zip(headers, widths):
            ttk.Label(header_frame, text=header, style='Modern.TLabel', 
                     width=width, relief='solid', borderwidth=1, anchor='center').pack(side=tk.LEFT, padx=1)

        # 可滚动的内容区域
        canvas = tk.Canvas(table_frame, height=200, bg=self.colors['bg_secondary'])
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='Modern.TFrame')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.rule_entries = []
        self.rule_frame = scrollable_frame

    def add_rule_entry_row(self, diff="", full="", abbr="", lang=""):
        """添加差分规则输入行"""
        row_frame = ttk.Frame(self.rule_frame, style='Modern.TFrame')
        row_frame.pack(fill=tk.X, pady=1)
        
        # 选中框
        check_var = tk.BooleanVar(value=False)
        check = ttk.Checkbutton(row_frame, variable=check_var)
        check.pack(side=tk.LEFT, padx=(0, 5))

        # 创建变量
        diff_var = tk.StringVar(value=diff)
        full_var = tk.StringVar(value=full)
        abbr_var = tk.StringVar(value=abbr)
        lang_var = tk.StringVar(value=lang)
        
        # 创建输入框
        widths = [8, 20, 12, 8]
        vars_list = [diff_var, full_var, abbr_var, lang_var]
        
        for var, width in zip(vars_list, widths):
            entry = ttk.Entry(row_frame, textvariable=var, width=width, style='Modern.TEntry')
            entry.pack(side=tk.LEFT, padx=1)
            var.trace_add("write", self.update_rule_config)
            
        self.rule_entries.append((check_var, vars_list, row_frame))

    def add_rule_row(self):
        """添加新的差分规则行"""
        self.add_rule_entry_row()

    def remove_rule_row(self):
        """删除选中的差分规则行"""
        for i in range(len(self.rule_entries) - 1, -1, -1):
            check_var, _, row_frame = self.rule_entries[i]
            if check_var.get():
                row_frame.destroy()
                self.rule_entries.pop(i)
        self.update_rule_config()

    def save_rule_config(self):
        """保存差分规则配置"""
        self.update_rule_config()
        messagebox.showinfo("提示", "差分规则已保存！")

    def update_rule_config(self, *args):
        """更新差分规则配置"""
        self.diff_rules.clear()
        
        for _, vars, _ in self.rule_entries:
            diff = vars[0].get().strip()
            if diff:
                self.diff_rules[diff] = (vars[1].get().strip(), vars[2].get().strip(), vars[3].get().strip())
        
        self.update_preview()

    def add_files(self):
        """添加文件"""
        files = filedialog.askopenfiles(title="选择文件")
        if files:
            file_paths = [f.name for f in files]
            self.add_files_to_list(file_paths)

    def add_folder(self):
        """添加文件夹"""
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            files = []
            for f in os.listdir(folder):
                full_path = os.path.join(folder, f)
                if os.path.isfile(full_path):
                    files.append(full_path)
            self.add_files_to_list(files)

    def add_files_to_list(self, file_paths):
        """添加文件到列表"""
        for file_path in file_paths:
            if not any(f[0] == file_path for f in self.files_to_rename):
                self.files_to_rename.append((file_path, os.path.basename(file_path)))
        self.update_preview()

    def clear_file_list(self):
        """清空文件列表"""
        self.files_to_rename.clear()
        self.update_preview()

    def handle_drop(self, event):
        """处理拖拽文件"""
        file_paths = self.root.tk.splitlist(event.data)
        all_files = []
        
        for path in file_paths:
            if os.path.isfile(path):
                all_files.append(path)
            elif os.path.isdir(path):
                for f in os.listdir(path):
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path):
                        all_files.append(full_path)
        
        self.add_files_to_list(all_files)

    def update_preview(self, *args):
        """更新预览"""
        if not hasattr(self, 'file_tree'):
            return
        # 清空现有预览
        for i in self.file_tree.get_children():
            self.file_tree.delete(i)
        
        # 重新生成预览
        for file_path, original_name in self.files_to_rename:
            name_no_ext, ext = os.path.splitext(original_name)
            result = self.generate_new_name(name_no_ext)
            
            if isinstance(result, tuple):
                new_name_no_ext, status = result
                new_name = new_name_no_ext + ext if not new_name_no_ext.startswith("[") else new_name_no_ext
            else:
                new_name = result + ext if not result.startswith("[") else result
                status = "✅" if not result.startswith("[") else "❌"
            
            # 根据状态设置不同颜色
            tags = ("success",) if status == "✅" else ("error",)
            self.file_tree.insert("", "end", values=(original_name, new_name, status, "🗑️ 删除"), tags=tags)
        
        # 配置标签颜色
        self.file_tree.tag_configure("success", foreground=self.colors['success'])
        self.file_tree.tag_configure("error", foreground=self.colors['danger'])

    def generate_new_name(self, original_name_no_ext):
        """生成新文件名"""
        # 新的解析逻辑：基于项目代号匹配
        matched_code = None
        matched_project = None
        
        # 寻找匹配的项目代号（按长度从长到短排序，避免短代号误匹配长代号）
        sorted_codes = sorted(self.project_codes.items(), key=lambda x: len(x[0]), reverse=True)
        
        for code, project_name in sorted_codes:
            if code and original_name_no_ext.startswith(code):
                matched_code = code
                matched_project = project_name
                break
        
        if not matched_code:
            return "[无匹配项目]", "❌"
        
        # 提取剩余部分并查找差分号
        remaining = original_name_no_ext[len(matched_code):]
        
        # 处理不同的分隔符格式：直接连接数字或用-分隔
        # 支持格式：洗衣店偷衣服-2 或 洗衣店偷衣服2
        if remaining.startswith('-'):
            # 格式：洗衣店偷衣服-2
            diff_num = remaining[1:]  # 去掉开头的-
        else:
            # 格式：洗衣店偷衣服2
            diff_num = remaining
        
        # 检查差分号是否为空或无效
        if not diff_num:
            return "[缺少差分号]", "❌"
        
        # 检查是否为纯数字
        if not diff_num.isdigit():
            return f"[差分号格式错误: {diff_num}]", "❌"
        
        # 检查差分规则是否存在
        if diff_num not in self.diff_rules:
            return f"[差分号{diff_num}无规则]", "❌"
        
        # 获取规则信息
        rule_data = self.diff_rules[diff_num]
        if len(rule_data) != 3:
            return f"[差分号{diff_num}规则不完整]", "❌"
        
        full_name, abbr, lang = rule_data
        
        # 检查规则数据是否完整
        if not all([full_name.strip(), abbr.strip(), lang.strip()]):
            return f"[差分号{diff_num}规则数据不完整]", "❌"
        
        # 生成最终文件名
        date = self.date_var.get()
        final_name = f"{date}_{matched_project}+{full_name}_{lang}_{abbr}_1080x1920"
        
        return final_name, "✅"

    def on_double_click(self, event):
        """处理双击事件以编辑单元格"""
        region = self.file_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.file_tree.identify_column(event.x)
        # 允许编辑“原始文件名”和“新文件名”列
        if column not in ("#1", "#2"):
            return

        item_id = self.file_tree.identify_row(event.y)
        
        # 获取单元格边界
        x, y, width, height = self.file_tree.bbox(item_id, column)
        
        # 创建一个Entry小部件
        value = self.file_tree.set(item_id, column)
        entry = ttk.Entry(self.file_tree, style='Modern.TEntry')
        entry.place(x=x, y=y, width=width, height=height)
        
        entry.insert(0, value)
        entry.focus_force()
        
        def on_focus_out(event):
            entry.destroy()

        def on_return(event):
            new_value = entry.get()
            self.file_tree.set(item_id, column, new_value)
            
            # 如果修改的是原始文件名，需要更新数据源并重新生成预览
            if column == "#1":
                index = self.file_tree.index(item_id)
                if 0 <= index < len(self.files_to_rename):
                    # 更新数据源中的原始文件名
                    original_path, _ = self.files_to_rename[index]
                    self.files_to_rename[index] = (original_path, new_value)
                    
                    # 重新计算这一行的新文件名
                    name_no_ext, ext = os.path.splitext(new_value)
                    result = self.generate_new_name(name_no_ext)
                    
                    if isinstance(result, tuple):
                        new_name_no_ext, status = result
                        new_name = new_name_no_ext + ext if not new_name_no_ext.startswith("[") else new_name_no_ext
                    else:
                        new_name = result + ext if not result.startswith("[") else result
                        status = "✅" if not result.startswith("[") else "❌"
                    
                    self.file_tree.set(item_id, "新文件名", new_name)
                    self.file_tree.set(item_id, "状态", status)
                    
                    # 更新颜色标签
                    new_tags = ("success",) if status == "✅" else ("error",)
                    self.file_tree.item(item_id, tags=new_tags)

            # 如果手动修改了新文件名，状态可能需要更新
            elif column == "#2":
                if new_value:
                    self.file_tree.set(item_id, "状态", "✅")
                    self.file_tree.item(item_id, tags=("success",))
                else:
                    self.file_tree.set(item_id, "状态", "❌")
                    self.file_tree.item(item_id, tags=("error",))
            
            entry.destroy()

        entry.bind("<Return>", on_return)
        entry.bind("<FocusOut>", on_focus_out)

    def on_click(self, event):
        """处理单击事件以删除行"""
        region = self.file_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.file_tree.identify_column(event.x)
        if column != "#4":  # “操作”列
            return

        item_id = self.file_tree.identify_row(event.y)
        
        # 找到要删除的文件
        index_to_delete = self.file_tree.index(item_id)
        
        # 从数据源和UI中删除
        if 0 <= index_to_delete < len(self.files_to_rename):
            self.files_to_rename.pop(index_to_delete)
            self.file_tree.delete(item_id)

    def execute_rename(self):
        """执行重命名"""
        items = self.file_tree.get_children()
        if not items:
            messagebox.showinfo("提示", "文件列表为空，请先添加文件")
            return
        
        self.last_renames.clear()
        self.log_history("开始执行重命名操作...\n")
        
        success_count = 0
        fail_count = 0
        
        # 遍历UI中的每一项，因为UI是最新状态（包括手动编辑和删除）
        for i, item_id in enumerate(items):
            values = self.file_tree.item(item_id, "values")
            # 解包时要考虑“操作”列
            original_name, new_name, status, _ = values
            
            # 从数据列表中获取完整路径
            original_path, _ = self.files_to_rename[i]
            
            if status != "✅":
                self.log_history(f"跳过: {original_name} ({status})\n")
                fail_count += 1
                continue
            
            new_path = os.path.join(os.path.dirname(original_path), new_name)
            
            try:
                os.rename(original_path, new_path)
                self.log_history(f"✅ 成功: {original_name} -> {new_name}\n")
                self.last_renames.append((new_path, original_path))
                success_count += 1
            except OSError as e:
                self.log_history(f"❌ 失败: {original_name} -> {str(e)}\n")
                fail_count += 1
        
        self.log_history(f"\n操作完成！成功: {success_count}, 失败/跳过: {fail_count}\n")
        
        # 清空文件列表并刷新
        self.files_to_rename.clear()
        self.update_preview()
        
        # 启用撤销按钮
        if self.last_renames:
            self.undo_button.config(state="normal")

    def undo_rename(self):
        """撤销重命名"""
        if not self.last_renames:
            messagebox.showinfo("提示", "没有可撤销的操作")
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
        self.undo_button.config(state="disabled")

    def save_all_config(self):
        """保存完整配置到JSON文件"""
        config_data = {
            "date": self.date_var.get(),
            "project_codes": {},
            "diff_rules": {}
        }
        
        # 收集项目代号配置
        for _, code_var, name_var, _ in self.project_entries:
            code = code_var.get().strip()
            name = name_var.get().strip()
            if code and name:
                config_data["project_codes"][code] = name
        
        # 收集差分规则配置
        for _, vars_list, _ in self.rule_entries:
            diff = vars_list[0].get().strip()
            if diff:  # 只保存非空规则
                config_data["diff_rules"][diff] = {
                    "full_name": vars_list[1].get().strip(),
                    "abbr": vars_list[2].get().strip(),
                    "lang": vars_list[3].get().strip()
                }
        
        # 选择保存位置
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"配置已保存到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存配置失败：\n{str(e)}")

    def load_config_file(self):
        """从JSON文件加载配置"""
        file_path = filedialog.askopenfilename(
            title="加载配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 加载日期
                if "date" in config_data:
                    self.date_var.set(config_data["date"])
                
                # 清空并重新加载项目代号
                for _, _, row_frame in self.project_entries:
                    row_frame.destroy()
                self.project_entries.clear()
                self.project_codes.clear()
                
                if "project_codes" in config_data:
                    for code, name in config_data["project_codes"].items():
                        self.add_project_entry_row(code, name)
                        self.project_codes[code] = name
                
                # 添加一些空行
                for _ in range(3):
                    self.add_project_entry_row()
                
                # 清空并重新加载差分规则
                for _, _, row_frame in self.rule_entries:
                    row_frame.destroy()
                self.rule_entries.clear()
                self.diff_rules.clear()
                
                if "diff_rules" in config_data:
                    for diff_num, rule_data in config_data["diff_rules"].items():
                        self.add_rule_entry_row(
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
                
                # 添加一些空行
                for _ in range(3):
                    self.add_rule_entry_row()
                
                messagebox.showinfo("成功", f"配置已从以下文件加载：\n{file_path}")
                self.update_preview()
                
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败：\n{str(e)}")

    def log_history(self, message):
        """记录历史日志"""
        self.history_text.config(state="normal")
        self.history_text.insert(tk.END, message)
        self.history_text.config(state="disabled")
        self.history_text.see(tk.END)

    def load_window_config(self):
        """加载窗口配置"""
        try:
            if os.path.exists(self.window_config_file):
                with open(self.window_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 设置窗口大小和位置
                if "geometry" in config:
                    self.root.geometry(config["geometry"])
                
                # 设置窗口状态（最大化等）
                if "state" in config and config["state"] == "zoomed":
                    self.root.state('zoomed')
                    
        except Exception as e:
            # 如果加载失败，使用默认配置
            print(f"加载窗口配置失败: {e}")

    def save_window_config(self):
        """保存窗口配置"""
        try:
            config = {
                "geometry": self.root.geometry(),
                "state": self.root.state()
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
                
                # 加载日期
                if "date" in config_data:
                    self.date_var.set(config_data["date"])
                
                # 清空并重新加载项目代号
                for _, _, row_frame in self.project_entries:
                    row_frame.destroy()
                self.project_entries.clear()
                self.project_codes.clear()
                
                if "project_codes" in config_data:
                    for code, name in config_data["project_codes"].items():
                        self.add_project_entry_row(code, name)
                        self.project_codes[code] = name
                
                # 添加一些空行
                for _ in range(3):
                    self.add_project_entry_row()
                
                # 清空并重新加载差分规则
                for _, _, row_frame in self.rule_entries:
                    row_frame.destroy()
                self.rule_entries.clear()
                self.diff_rules.clear()
                
                if "diff_rules" in config_data:
                    for diff_num, rule_data in config_data["diff_rules"].items():
                        self.add_rule_entry_row(
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
                
                # 添加一些空行
                for _ in range(3):
                    self.add_rule_entry_row()
                
                print("自动加载配置成功")
                
        except Exception as e:
            print(f"自动加载配置失败: {e}")

    def save_auto_config(self):
        """自动保存当前配置"""
        try:
            config_data = {
                "date": self.date_var.get(),
                "project_codes": {},
                "diff_rules": {}
            }
            
            # 收集项目代号配置
            for _, code_var, name_var, _ in self.project_entries:
                code = code_var.get().strip()
                name = name_var.get().strip()
                if code and name:
                    config_data["project_codes"][code] = name
            
            # 收集差分规则配置
            for _, vars_list, _ in self.rule_entries:
                diff = vars_list[0].get().strip()
                if diff:  # 只保存非空规则
                    config_data["diff_rules"][diff] = {
                        "full_name": vars_list[1].get().strip(),
                        "abbr": vars_list[2].get().strip(),
                        "lang": vars_list[3].get().strip()
                    }
            
            with open(self.auto_config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"自动保存配置失败: {e}")

    def on_closing(self):
        """窗口关闭事件处理"""
        # 保存窗口配置
        self.save_window_config()
        
        # 自动保存当前配置
        self.save_auto_config()
        
        # 关闭程序
        self.root.destroy()


# ========== 编辑对话框类 ==========

class EditProjectDialog:
    def __init__(self, parent, code="", name=""):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑项目代号")
        self.dialog.geometry("500x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (250 // 2)
        self.dialog.geometry(f"500x250+{x}+{y}")
        
        # 创建界面
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 代号输入
        ttk.Label(main_frame, text="项目代号:", font=('Microsoft YaHei UI', 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.code_var = tk.StringVar(value=code)
        ttk.Entry(main_frame, textvariable=self.code_var, width=40, font=('Microsoft YaHei UI', 10)).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # 项目名输入
        ttk.Label(main_frame, text="完整项目名:", font=('Microsoft YaHei UI', 10)).grid(row=1, column=0, sticky="nw", pady=5)
        self.name_var = tk.StringVar(value=name)
        name_text = tk.Text(main_frame, width=40, height=4, font=('Microsoft YaHei UI', 9))
        name_text.grid(row=1, column=1, padx=(10, 0), pady=5)
        name_text.insert("1.0", name)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=lambda: self.ok_clicked(name_text)).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def ok_clicked(self, name_text):
        code = self.code_var.get().strip()
        name = name_text.get("1.0", tk.END).strip()
        
        if not code:
            messagebox.showwarning("警告", "请输入项目代号")
            return
        
        if not name:
            messagebox.showwarning("警告", "请输入完整项目名")
            return
        
        self.result = (code, name)
        self.dialog.destroy()


class EditRuleDialog:
    def __init__(self, parent, diff="", full="", abbr="", lang=""):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑差分规则")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"400x300+{x}+{y}")
        
        # 创建界面
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 差分号
        ttk.Label(main_frame, text="差分号:", font=('Microsoft YaHei UI', 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.diff_var = tk.StringVar(value=diff)
        ttk.Entry(main_frame, textvariable=self.diff_var, width=30, font=('Microsoft YaHei UI', 10)).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # 版本名全称
        ttk.Label(main_frame, text="版本名全称:", font=('Microsoft YaHei UI', 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.full_var = tk.StringVar(value=full)
        ttk.Entry(main_frame, textvariable=self.full_var, width=30, font=('Microsoft YaHei UI', 10)).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # 版本名缩写
        ttk.Label(main_frame, text="版本名缩写:", font=('Microsoft YaHei UI', 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.abbr_var = tk.StringVar(value=abbr)
        ttk.Entry(main_frame, textvariable=self.abbr_var, width=30, font=('Microsoft YaHei UI', 10)).grid(row=2, column=1, padx=(10, 0), pady=5)
        
        # 语言
        ttk.Label(main_frame, text="语言:", font=('Microsoft YaHei UI', 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.lang_var = tk.StringVar(value=lang)
        ttk.Entry(main_frame, textvariable=self.lang_var, width=30, font=('Microsoft YaHei UI', 10)).grid(row=3, column=1, padx=(10, 0), pady=5)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确定", command=self.ok_clicked).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # 等待对话框关闭
        self.dialog.wait_window()
    
    def ok_clicked(self):
        diff = self.diff_var.get().strip()
        full = self.full_var.get().strip()
        abbr = self.abbr_var.get().strip()
        lang = self.lang_var.get().strip()
        
        if not all([diff, full, abbr, lang]):
            messagebox.showwarning("警告", "请填写所有字段")
            return
        
        self.result = (diff, full, abbr, lang)
        self.dialog.destroy()


# ========== 主程序入口 ==========

if __name__ == "__main__":
    if DND_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = ModernBatchRenamerApp(root)
    root.mainloop()
