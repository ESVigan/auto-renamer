# 更新检查功能 - 私有仓库解决方案

## 问题诊断

测试结果显示 **404错误**,这表明GitHub API无法访问您的仓库。

## 原因

您的仓库 `ESVigan/auto-renamer` 是**私有仓库**,GitHub API默认无法访问私有仓库的Release信息。

## 解决方案

### 方案1: 将仓库设为公开 (推荐)

如果这个项目可以公开:

1. 访问: https://github.com/ESVigan/auto-renamer/settings
2. 滚动到页面底部 "Danger Zone"
3. 点击 "Change visibility"
4. 选择 "Make public"

**优点**: 
- 简单,无需修改代码
- 用户可以直接访问和下载
- 更新检查功能立即可用

### 方案2: 使用GitHub Personal Access Token

如果必须保持私有,需要使用认证token:

1. **创建Personal Access Token**:
   - 访问: https://github.com/settings/tokens
   - 点击 "Generate new token" → "Generate new token (classic)"
   - 勾选权限: `repo` (完整仓库访问权限)
   - 生成并复制token

2. **修改代码使用token**:
   ```python
   # 在美化_renamer.py的配置区添加:
   GITHUB_TOKEN = "your_token_here"  # 替换为您的token
   
   # 修改UpdateCheckThread的run方法:
   def run(self):
       try:
           api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
           headers = {}
           if GITHUB_TOKEN:
               headers['Authorization'] = f'token {GITHUB_TOKEN}'
           proxies = get_system_proxies()
           response = requests.get(api_url, headers=headers, proxies=proxies, timeout=5)
           response.raise_for_status()
           self.result.emit(response.json())
       except Exception as e:
           self.result.emit(e)
   ```

**缺点**:
- Token需要保密,不能提交到公开代码
- Token有过期时间
- 配置较复杂

### 方案3: 禁用自动更新检查

如果不需要自动更新检查功能:

修改 `美化_renamer.py` 的 `main()` 函数:
```python
def main():
    """启动器主函数"""
    app = QApplication(sys.argv)

    if not os.path.exists(APP_LOGIC_FILE):
        QMessageBox.critical(None, "文件缺失", f"核心逻辑文件 '{APP_LOGIC_FILE}' 不存在,程序无法启动。")
        return

    # 直接启动主程序,不检查更新
    run_main_app()
    sys.exit(app.exec())
```

## 推荐做法

**建议使用方案1 - 将仓库设为公开**,因为:
1. 最简单,无需修改代码
2. 更新检查功能可以正常工作
3. 其他用户也可以使用您的工具
4. 符合开源项目的最佳实践

如果项目包含敏感信息,可以:
- 将敏感配置放在 `.gitignore` 中
- 使用环境变量存储敏感数据
- 提供配置模板文件

## 测试

设置为公开后,再次运行测试:
```bash
python test_api_direct.py
```

应该会看到状态码200和Release信息。
