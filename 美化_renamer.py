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
import re
import hashlib
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# --- 配置区 ---
# GitHub 用户名和仓库名
GITHUB_REPO = "ESVigan/auto-renamer" 
# 逻辑代码文件名
APP_LOGIC_FILE = "app_logic.py"
# --- 配置区结束 ---

def get_current_version():
    """获取当前版本号，优先从模块变量读取，回退读取文件"""
    try:
        from app_logic import APP_VERSION
        return APP_VERSION
    except Exception:
        pass
    try:
        with open(APP_LOGIC_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        match = re.search(r'^APP_VERSION\s*=\s*["\'](.*?)["\']', content, re.MULTILINE)
        if match:
            return match.group(1)
    except Exception:
        pass
    return "v0.0"

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

def normalize_version(s: str):
    s = (s or "").strip()
    if s[:1].lower() == "v":
        s = s[1:]
    parts = s.split(".")
    nums = []
    for p in parts:
        m = re.sub(r"[^0-9]", "", p)
        nums.append(int(m) if m.isdigit() else 0)
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums[:3])

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
        module = None
        # 加载顺序：exe同目录 -> 用户目录 -> 内置模块
        base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
        user_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'AutoRenamer')
        for candidate_dir in [base_dir, user_dir]:
            candidate = os.path.join(candidate_dir, APP_LOGIC_FILE)
            if os.path.exists(candidate):
                spec = importlib.util.spec_from_file_location('app_logic', candidate)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                break
        if module is None:
            if APP_LOGIC_FILE.replace('.py', '') in sys.modules:
                importlib.reload(sys.modules[APP_LOGIC_FILE.replace('.py', '')])
            import app_logic as module
        app.main_window = module.ModernBatchRenamerApp()
        app.main_window.show()

    except ImportError:
        QMessageBox.critical(None, "错误", f"无法找到主程序文件 '{APP_LOGIC_FILE}'。请确保它与启动器在同一目录下。")
        app.quit()
    except Exception as e:
        QMessageBox.critical(None, "启动失败", f"启动主程序时发生未知错误：\n{e}")
        app.quit()


def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def download_and_update(app, download_url, latest_version, expected_sha256: str | None = None):
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
                if expected_sha256:
                    actual = compute_sha256(message)
                    if actual.lower() != expected_sha256.lower():
                        raise RuntimeError(f"SHA256 校验失败\n期待: {expected_sha256}\n实际: {actual}")
                target = APP_LOGIC_FILE
                if getattr(sys, 'frozen', False):
                    base_dir = os.path.dirname(sys.executable)
                    # 判断目录可写性，决定落地到exe目录还是用户目录
                    def dir_writable(d):
                        try:
                            test = os.path.join(d, ".write_test")
                            with open(test, 'w', encoding='utf-8') as tf:
                                tf.write("ok")
                            os.remove(test)
                            return True
                        except Exception:
                            return False
                    if dir_writable(base_dir):
                        target = os.path.join(base_dir, APP_LOGIC_FILE)
                    else:
                        user_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'AutoRenamer')
                        os.makedirs(user_dir, exist_ok=True)
                        target = os.path.join(user_dir, APP_LOGIC_FILE)
                backup_file = target + ".backup"
                if os.path.exists(target):
                    import shutil
                    shutil.copy2(target, backup_file)
                import shutil
                shutil.move(message, target)
                
                # 显示成功消息
                msg = QMessageBox()
                msg.setWindowTitle("更新成功")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"已成功更新到版本 {latest_version}!")
                msg.setInformativeText("程序将重新启动以应用更新。")
                msg.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg.exec()
                
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


def download_and_swap_exe(app, download_url, latest_version):
    from PyQt6.QtWidgets import QProgressDialog
    import tempfile
    import subprocess
    progress = QProgressDialog("正在下载新版本...", "取消", 0, 100, None)
    progress.setWindowTitle("下载更新")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.show()
    temp_file = os.path.join(tempfile.gettempdir(), f"update_{latest_version}.exe")
    def on_download_progress(percent):
        progress.setValue(percent)
    def on_download_finished(status, message):
        progress.close()
        dl.wait()
        if status == "success":
            try:
                current_exe = sys.executable
                new_path = current_exe + ".new"
                import shutil
                shutil.move(message, new_path)
                script_path = os.path.join(tempfile.gettempdir(), "swap_update.ps1")
                ps = (
                    f"$old = '{current_exe.replace("'", "''")}'\n"
                    f"$new = '{new_path.replace("'", "''")}'\n" 
                    "while ($true) {\n"
                    "  try { Move-Item -LiteralPath $new -Destination $old -Force; break }\n"
                    "  catch { Start-Sleep -Milliseconds 500 }\n"
                    "}\n"
                    "Start-Process -FilePath $old\n"
                )
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(ps)
                subprocess.Popen([
                    "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path
                ])
                sys.exit(0)
            except Exception as e:
                QMessageBox.critical(None, "更新失败", f"应用更新时出错:\n{e}")
        else:
            QMessageBox.warning(None, "下载失败", f"无法下载更新:\n{message}")
    dl = DownloaderThread(download_url, temp_file)
    dl.progress.connect(on_download_progress)
    dl.finished.connect(on_download_finished)
    app.download_exe_thread = dl
    dl.start()

def ensure_app_logic_available(app):
    """当本地缺失 app_logic.py 时，自动从服务器获取并保存到本地（支持源码与打包版）"""
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    user_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'AutoRenamer')
    os.makedirs(user_dir, exist_ok=True)
    target_path = os.path.join(base_dir, APP_LOGIC_FILE)
    # 若exe目录不可写则回退用户目录
    def dir_writable(d):
        try:
            test = os.path.join(d, ".write_test")
            with open(test, 'w', encoding='utf-8') as tf:
                tf.write("ok")
            os.remove(test)
            return True
        except Exception:
            return False
    if not dir_writable(base_dir):
        target_path = os.path.join(user_dir, APP_LOGIC_FILE)
    if os.path.exists(target_path):
        return True

    # 试图从最新发布获取 app_logic.py 资产
    progress = QProgressDialog("正在获取核心文件...", "取消", 0, 100, None)
    progress.setWindowTitle("下载核心文件")
    progress.setWindowModality(Qt.WindowModality.ApplicationModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    progress.show()

    download_url = None
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        proxies = get_system_proxies()
        resp = requests.get(api_url, proxies=proxies, timeout=8)
        if resp.ok:
            data = resp.json()
            for asset in data.get('assets', []):
                if asset.get('name') == APP_LOGIC_FILE:
                    download_url = asset.get('browser_download_url')
                    break
    except Exception:
        pass

    # 回退到主分支原始文件
    if not download_url:
        download_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{APP_LOGIC_FILE}"

    def on_progress(p):
        progress.setValue(p)

    def on_finished(status, message):
        progress.close()
        dl.wait()
        if status == "success" and os.path.exists(target_path):
            QMessageBox.information(None, "下载完成", "核心文件已获取，正在启动程序。")
            run_main_app()
        else:
            QMessageBox.critical(None, "下载失败", f"无法获取核心文件：\n{message}\n\n请稍后重试或手动下载。")
            app.quit()

    dl = DownloaderThread(download_url, target_path)
    dl.progress.connect(on_progress)
    dl.finished.connect(on_finished)
    app.ensure_logic_thread = dl
    dl.start()
    return False

def check_for_updates(app):
    """检查更新并显示提示"""
    current_version = get_current_version()

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
            lv = normalize_version(latest_version)
            cv = normalize_version(current_version)
            if lv > cv:
                # 有新版本可用
                msg = QMessageBox()
                msg.setWindowTitle("发现新版本")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"发现新版本: {latest_version}\n当前版本: {current_version}\n\n是否立即下载并更新?")
                msg.setDetailedText(f"更新内容:\n{release_notes}")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                msg.setDefaultButton(QMessageBox.StandardButton.Yes)
                
                reply = msg.exec()
                
                if reply == QMessageBox.StandardButton.Yes:
                    import sys, webbrowser
                    assets = result.get('assets', [])
                    download_url = None
                    sha_url = None
                    for asset in assets:
                        name = asset.get('name', '')
                        if name == 'app_logic.py':
                            download_url = asset.get('browser_download_url')
                        elif name == 'app_logic.sha256':
                            sha_url = asset.get('browser_download_url')
                    expected_sha = None
                    try:
                        if sha_url:
                            resp_sha = requests.get(sha_url, timeout=5)
                            if resp_sha.ok:
                                expected_sha = resp_sha.text.strip().split()[0]
                    except Exception:
                        pass
                    if not download_url:
                        download_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{APP_LOGIC_FILE}"
                    download_and_update(app, download_url, latest_version, expected_sha)
                else:
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

    # 两种模式均支持：缺失时自动下载 app_logic.py
    base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.getcwd()
    if not os.path.exists(os.path.join(base_dir, APP_LOGIC_FILE)):
        if not ensure_app_logic_available(app):
            # 进入事件循环以驱动下载线程，下载完成后自动启动主程序
            sys.exit(app.exec())
            return

    # 启动时检查更新
    check_for_updates(app)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
