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
# GitHub 用户名和仓库名
GITHUB_REPO = "ESVigan/auto-renamer" 
# 当前版本号，与 GitHub Release 的 tag 名称对应
CURRENT_VERSION = "v1.42"
# 逻辑代码文件名
APP_LOGIC_FILE = "app_logic.py"
# --- 配置区结束 ---

def get_system_proxies():
    """
    获取系统代理设置
    requests库会自动读取系统环境变量中的代理设置:
    - HTTP_PROXY / http_proxy
    - HTTPS_PROXY / https_proxy
    - NO_PROXY / no_proxy
    
    返回None表示使用requests的默认行为(自动检测系统代理)
    """
    # 返回None让requests自动使用系统代理
    return None

class UpdateCheckThread(QThread):
    """在后台线程中检查更新"""
    result = pyqtSignal(object)

    def run(self):
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            proxies = get_system_proxies()
            response = requests.get(api_url, proxies=proxies, timeout=5)
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
            proxies = get_system_proxies()
            response = requests.get(self.url, stream=True, proxies=proxies, timeout=15)
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


def download_and_update(app, download_url, latest_version):
    """下载并应用更新"""
    # 创建进度对话框
    progress = QProgressDialog("正在下载更新...", "取消", 0, 100, None)
    progress.setWindowTitle("下载更新")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.show()
    
    # 下载文件保存路径
    import tempfile
    temp_file = os.path.join(tempfile.gettempdir(), f"update_{latest_version}.py")
    
    def on_download_progress(percent):
        progress.setValue(percent)
    
    def on_download_finished(status, message):
        progress.close()
        download_thread.wait()
        
        if status == "success":
            try:
                # 备份当前文件
                backup_file = APP_LOGIC_FILE + ".backup"
                if os.path.exists(APP_LOGIC_FILE):
                    import shutil
                    shutil.copy2(APP_LOGIC_FILE, backup_file)
                
                # 替换文件
                import shutil
                shutil.move(message, APP_LOGIC_FILE)
                
                # 显示成功消息
                msg = QMessageBox()
                msg.setWindowTitle("更新成功")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"已成功更新到版本 {latest_version}!")
                msg.setInformativeText("程序将重新启动以应用更新。")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                
                # 重启程序
                import subprocess
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)
                
            except Exception as e:
                QMessageBox.critical(None, "更新失败", f"应用更新时出错:\n{e}\n\n已保留备份文件: {backup_file}")
                run_main_app()
        else:
            QMessageBox.warning(None, "下载失败", f"无法下载更新:\n{message}\n\n将继续使用当前版本。")
            run_main_app()
    
    # 创建下载线程
    download_thread = DownloaderThread(download_url, temp_file)
    download_thread.progress.connect(on_download_progress)
    download_thread.finished.connect(on_download_finished)
    app.download_thread = download_thread
    download_thread.start()


def check_for_updates(app):
    """检查更新并显示提示"""
    def on_update_check_result(result):
        if isinstance(result, Exception):
            # 检查更新失败,静默处理,直接启动主程序
            run_main_app()
            # 等待线程结束
            check_thread.wait()
            return
        
        try:
            latest_version = result.get('tag_name', '')
            release_notes = result.get('body', '无更新说明')
            
            if latest_version and latest_version != CURRENT_VERSION:
                # 有新版本可用
                msg = QMessageBox()
                msg.setWindowTitle("发现新版本")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"发现新版本: {latest_version}\n当前版本: {CURRENT_VERSION}\n\n是否立即下载并更新?")
                msg.setDetailedText(f"更新内容:\n{release_notes}")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg.setDefaultButton(QMessageBox.StandardButton.Yes)
                
                reply = msg.exec()
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 用户选择更新,查找下载链接
                    assets = result.get('assets', [])
                    download_url = None
                    
                    # 查找app_logic.py文件
                    for asset in assets:
                        if asset.get('name') == 'app_logic.py':
                            download_url = asset.get('browser_download_url')
                            break
                    
                    if download_url:
                        download_and_update(app, download_url, latest_version)
                    else:
                        QMessageBox.warning(None, "无法更新", "未找到更新文件,请手动下载更新。\n\n将继续使用当前版本。")
                        run_main_app()
                else:
                    # 用户选择稍后更新
                    run_main_app()
            else:
                # 无更新,直接启动主程序
                run_main_app()
            
        except Exception:
            # 解析更新信息失败,直接启动主程序
            run_main_app()
        finally:
            # 等待线程结束
            check_thread.wait()
    
    # 创建并启动更新检查线程
    check_thread = UpdateCheckThread()
    check_thread.result.connect(on_update_check_result)
    # 将线程存储为app的属性,防止被垃圾回收
    app.update_check_thread = check_thread
    check_thread.start()


def main():
    """启动器主函数"""
    app = QApplication(sys.argv)

    # 检查 app_logic.py 是否存在
    if not os.path.exists(APP_LOGIC_FILE):
        QMessageBox.critical(None, "文件缺失", f"核心逻辑文件 '{APP_LOGIC_FILE}' 不存在,程序无法启动。")
        return

    # 启动时检查更新
    check_for_updates(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
