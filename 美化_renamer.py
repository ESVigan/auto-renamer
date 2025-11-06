#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPX 批量重命名工具 - 启动器
负责检查更新并启动主应用程序。
"""

import sys
import os
import json
import requests
import importlib
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- 配置区 ---
# 请将这里替换为您的 GitHub 用户名和仓库名
GITHUB_REPO = "YourUsername/YourRepoName" 
# 当前版本号，与 GitHub Release 的 tag 名称对应
CURRENT_VERSION = "v1.42"
# 逻辑代码文件名
APP_LOGIC_FILE = "app_logic.py"
# --- 配置区结束 ---

class UpdateCheckThread(QThread):
    """在后台线程中检查更新"""
    result = pyqtSignal(object)

    def run(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url, timeout=5)
            response.raise_for_status()
            self.result.emit(response.json())
        except Exception as e:
            self.result.emit(e)

class DownloaderThread(QThread):
    """在后台线程中下载文件"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # (下载状态, 消息或文件路径)

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=15)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    if total_size > 0:
                        progress_percent = int((bytes_downloaded / total_size) * 100)
                        self.progress.emit(progress_percent)
            
            self.finished.emit("success", self.save_path)

        except Exception as e:
            self.finished.emit("error", f"下载失败: {e}")


def run_main_app():
    """动态加载并运行主程序"""
    app = QApplication.instance()
    try:
        # 确保 app_logic 模块被重新加载
        if APP_LOGIC_FILE.replace('.py', '') in sys.modules:
            importlib.reload(sys.modules[APP_LOGIC_FILE.replace('.py', '')])
        
        from app_logic import ModernBatchRenamerApp
        
        # 将主窗口存储为app的属性，以防止其被垃圾回收
        app.main_window = ModernBatchRenamerApp()
        app.main_window.show()

    except ImportError:
        QMessageBox.critical(None, "错误", f"无法找到主程序文件 '{APP_LOGIC_FILE}'。请确保它与启动器在同一目录下。")
        app.quit()
    except Exception as e:
        QMessageBox.critical(None, "启动失败", f"启动主程序时发生未知错误：\n{e}")
        app.quit()


def main():
    """启动器主函数"""
    app = QApplication(sys.argv)

    # 检查 app_logic.py 是否存在
    if not os.path.exists(APP_LOGIC_FILE):
        QMessageBox.critical(None, "文件缺失", f"核心逻辑文件 '{APP_LOGIC_FILE}' 不存在，程序无法启动。")
        return

    # 创建一个临时的加载提示窗口
    loading_label = QLabel("正在检查更新，请稍候...")
    loading_label.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
    loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    loading_label.setStyleSheet("background-color: #f0f0f0; color: #333; font-size: 16px; padding: 20px; border-radius: 10px;")
    loading_label.show()
    app.processEvents()

    update_checker = UpdateCheckThread()

    def on_update_check_finished(result):
        loading_label.close()
        if isinstance(result, dict):
            latest_version = result.get("tag_name")
            if latest_version and latest_version != CURRENT_VERSION:
                reply = QMessageBox.question(None, "发现新版本", 
                                             f"检测到新版本 {latest_version}！\n您当前的版本是 {CURRENT_VERSION}。\n\n是否立即更新？",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    handle_download(result)
                else:
                    run_main_app()
            else:
                run_main_app()
        else:
            # 检查更新失败，直接启动主程序
            print(f"检查更新失败: {result}")
            run_main_app()

    def handle_download(release_data):
        assets = release_data.get("assets", [])
        download_url = None
        for asset in assets:
            if asset.get("name") == APP_LOGIC_FILE:
                download_url = asset.get("browser_download_url")
                break
        
        if not download_url:
            QMessageBox.warning(None, "更新失败", f"在版本 {release_data.get('tag_name')} 中未找到 '{APP_LOGIC_FILE}' 文件。")
            run_main_app()
            return

        progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setWindowTitle("更新")
        progress_dialog.show()

        downloader = DownloaderThread(download_url, APP_LOGIC_FILE)
        
        def on_download_progress(percent):
            progress_dialog.setValue(percent)

        def on_download_finished(status, message):
            progress_dialog.close()
            if status == "success":
                QMessageBox.information(None, "更新完成", "程序已更新到最新版本，即将重启。")
                # 重启应用程序的逻辑
                QApplication.quit()
                # 在Windows上，os.execv会替换当前进程
                os.execv(sys.executable, [sys.executable] + sys.argv)
            else:
                QMessageBox.critical(None, "更新失败", message)
                run_main_app()

        downloader.progress.connect(on_download_progress)
        downloader.finished.connect(on_download_finished)
        
        # 保持 downloader 对象的引用
        app.downloader = downloader
        downloader.start()

    update_checker.result.connect(on_update_check_finished)
    # 保持 update_checker 对象的引用
    app.update_checker = update_checker
    update_checker.start()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
