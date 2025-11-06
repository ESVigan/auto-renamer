import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
import sys

# For drag-and-drop functionality, tkinterdnd2 is required.
# We'll try to import it, and if it fails, drag-and-drop will be disabled.
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORT = True
except ImportError:
    DND_SUPPORT = False

class BatchRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("批量文件重命名工具 v3.0 (Python)")
        self.root.geometry("850x750")

        self.files_to_rename = []
        self.last_renames = []

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. Global Settings ---
        settings_frame = ttk.LabelFrame(main_frame, text="1. 全局设置 (Global Settings)", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)

        self.date_var = tk.StringVar(value="251013")
        self.template_var = tk.StringVar(value="pre-shoot-门口pay*+")
        
        ttk.Label(settings_frame, text="日期 (YYMMDD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.date_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(settings_frame, text="项目名模板 (* = 项目号):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(settings_frame, textvariable=self.template_var, width=50).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)

        self.date_var.trace_add("write", self.update_preview)
        self.template_var.trace_add("write", self.update_preview)

        # --- 2. Differential Rules ---
        rules_frame = ttk.LabelFrame(main_frame, text="2. 差分规则配置 (Differential Rules)", padding="10")
        rules_frame.pack(fill=tk.X, pady=5)

        cols = ("差分号", "版本名全称", "版本名缩写", "语言")
        self.rules_tree = ttk.Treeview(rules_frame, columns=cols, show='headings', height=5)
        for col in cols:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=150)
        self.rules_tree.pack(side=tk.TOP, fill=tk.X, expand=True)

        # Add default rules
        self.rules_tree.insert("", "end", values=("1", "动画quiz-批量化", "BVC", "es"))
        self.rules_tree.insert("", "end", values=("2", "核玩-半圈拼-书店2", "JSP", "en"))
        self.rules_tree.insert("", "end", values=("4", "核玩新版", "SLT", "en"))

        rules_btn_frame = ttk.Frame(rules_frame)
        rules_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(rules_btn_frame, text="删除选中规则", command=self.remove_selected_rule).pack(side=tk.RIGHT, padx=5)
        ttk.Button(rules_btn_frame, text="添加新规则", command=self.add_rule).pack(side=tk.RIGHT)

        # --- 3. File List & Preview ---
        files_frame = ttk.LabelFrame(main_frame, text="3. 文件列表与预览 (File List & Preview)", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        file_btn_frame = ttk.Frame(files_frame)
        file_btn_frame.pack(fill=tk.X)
        ttk.Button(file_btn_frame, text="添加文件...", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_btn_frame, text="添加文件夹...", command=self.add_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_btn_frame, text="清空列表", command=self.clear_file_list).pack(side=tk.LEFT, padx=5)

        file_cols = ("原始文件名", "新文件名")
        self.file_tree = ttk.Treeview(files_frame, columns=file_cols, show='headings')
        self.file_tree.heading("原始文件名", text="原始文件名")
        self.file_tree.heading("新文件名", text="新文件名")
        self.file_tree.column("原始文件名", width=300)
        self.file_tree.column("新文件名", width=500)
        self.file_tree.pack(fill=tk.BOTH, expand=True, pady=5)

        if DND_SUPPORT:
            self.file_tree.drop_target_register(DND_FILES)
            self.file_tree.dnd_bind('<<Drop>>', self.handle_drop)
            drop_label_text = "或者直接将文件/文件夹拖拽到上面的列表中"
        else:
            drop_label_text = "提示: 未找到 tkinterdnd2 库, 拖拽功能已禁用。\n请运行 'pip install tkinterdnd2' 来启用此功能。"
        ttk.Label(files_frame, text=drop_label_text, justify=tk.CENTER).pack()

        # --- 4. Execute & History ---
        exec_frame = ttk.LabelFrame(main_frame, text="4. 执行与历史 (Execute & History)", padding="10")
        exec_frame.pack(fill=tk.X, pady=5)

        self.exec_button = ttk.Button(exec_frame, text="!! 开始执行重命名 !!", command=self.execute_rename)
        self.exec_button.pack(fill=tk.X, ipady=5)

        history_frame = ttk.Frame(exec_frame)
        history_frame.pack(fill=tk.X, pady=5)
        self.history_text = tk.Text(history_frame, height=5, state="disabled")
        self.history_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.undo_button = ttk.Button(history_frame, text="撤销上次操作", command=self.undo_rename, state="disabled")
        self.undo_button.pack(side=tk.RIGHT, padx=5)

    def add_rule(self):
        self.rules_tree.insert("", "end", values=("", "", "", ""))

    def remove_selected_rule(self):
        selected_items = self.rules_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请先在表格中选择要删除的规则。")
            return
        for item in selected_items:
            self.rules_tree.delete(item)

    def add_files(self):
        files = filedialog.askopenfiles(title="选择文件")
        if files:
            self.add_files_to_list([f.name for f in files])

    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            files_in_folder = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
            self.add_files_to_list(files_in_folder)

    def add_files_to_list(self, file_paths):
        for file_path in file_paths:
            if file_path not in [f[0] for f in self.files_to_rename]:
                self.files_to_rename.append((file_path, os.path.basename(file_path)))
        self.update_preview()

    def clear_file_list(self):
        self.files_to_rename.clear()
        self.update_preview()

    def handle_drop(self, event):
        # The event.data is a string of file paths, possibly wrapped in braces
        file_paths_str = self.root.tk.splitlist(event.data)
        self.add_files_to_list(file_paths_str)

    def update_preview(self, *args):
        for i in self.file_tree.get_children():
            self.file_tree.delete(i)
        
        for file_path, original_name in self.files_to_rename:
            name_no_ext, ext = os.path.splitext(original_name)
            new_name_no_ext = self.generate_new_name(name_no_ext)
            new_name = new_name_no_ext + ext if not new_name_no_ext.startswith("[") else new_name_no_ext
            self.file_tree.insert("", "end", values=(original_name, new_name))

    def generate_new_name(self, original_name_no_ext):
        match = re.match(r"^(.*?)(\d+)-(\d+)$", original_name_no_ext)
        if not match:
            return "[无法解析]"

        _, project_num, diff_num = match.groups()

        rule = None
        for item in self.rules_tree.get_children():
            values = self.rules_tree.item(item, "values")
            if values[0] == diff_num:
                rule = values
                break
        
        if not rule:
            return "[无匹配规则]"

        _, full_name, abbr, lang = rule
        
        date = self.date_var.get()
        template = self.template_var.get()
        project_name = template.replace("*", project_num) + full_name

        return f"{date}_{project_name}_{lang}_{abbr}_1080x1920"

    def execute_rename(self):
        if not self.files_to_rename:
            messagebox.showinfo("提示", "文件列表为空，请先添加文件。")
            return

        self.last_renames.clear()
        self.log_history("开始重命名操作...\n")
        success_count = 0
        fail_count = 0

        preview_items = self.file_tree.get_children()
        for i, (original_path, _) in enumerate(self.files_to_rename):
            original_name, new_name = self.file_tree.item(preview_items[i], "values")
            
            if new_name.startswith("["):
                self.log_history(f"跳过: {original_name} -> {new_name}\n")
                fail_count += 1
                continue

            new_path = os.path.join(os.path.dirname(original_path), new_name)
            try:
                os.rename(original_path, new_path)
                self.log_history(f"成功: {original_name} -> {new_name}\n")
                self.last_renames.append((new_path, original_path))
                success_count += 1
            except OSError as e:
                self.log_history(f"失败: {original_name} -> {e}\n")
                fail_count += 1
        
        self.log_history(f"\n操作完成。成功: {success_count}, 失败/跳过: {fail_count}\n")
        self.files_to_rename.clear()
        self.update_preview()
        self.undo_button.config(state="normal" if self.last_renames else "disabled")

    def undo_rename(self):
        if not self.last_renames:
            messagebox.showinfo("提示", "没有可撤销的操作。")
            return

        self.log_history("开始撤销上次操作...\n")
        success_count = 0
        fail_count = 0

        for new_path, original_path in reversed(self.last_renames):
            try:
                os.rename(new_path, original_path)
                self.log_history(f"撤销成功: {os.path.basename(new_path)} -> {os.path.basename(original_path)}\n")
                success_count += 1
            except OSError as e:
                self.log_history(f"撤销失败: {os.path.basename(new_path)} -> {e}\n")
                fail_count += 1
        
        self.log_history(f"\n撤销完成。成功: {success_count}, 失败: {fail_count}\n")
        self.last_renames.clear()
        self.undo_button.config(state="disabled")

    def log_history(self, message):
        self.history_text.config(state="normal")
        self.history_text.insert(tk.END, message)
        self.history_text.config(state="disabled")
        self.history_text.see(tk.END)

if __name__ == "__main__":
    if DND_SUPPORT:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = BatchRenamerApp(root)
    root.mainloop()
