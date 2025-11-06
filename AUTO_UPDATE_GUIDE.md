# 自动更新功能使用指南

## 功能说明

现在程序支持自动下载和更新功能:
1. 启动时自动检查GitHub Release
2. 发现新版本时弹出提示
3. 用户点击"是"后自动下载并应用更新
4. 自动备份旧版本
5. 更新完成后自动重启程序

## 发布新版本的步骤

### 1. 更新版本号

修改 `美化_renamer.py` 中的版本号:
```python
CURRENT_VERSION = "v1.43"  # 改为新版本号,如 v1.44
```

### 2. 提交代码

```bash
git add 美化_renamer.py
git commit -m "chore: 更新版本号到 v1.44"
git push origin main
```

### 3. 创建Tag

```bash
git tag -a v1.44 -m "v1.44 - 新功能描述"
git push origin v1.44
```

### 4. 创建GitHub Release并上传文件

这是**关键步骤**,必须上传 `app_logic.py` 文件:

1. 访问: https://github.com/ESVigan/auto-renamer/releases/new

2. 填写信息:
   - **Tag**: 选择刚创建的 `v1.44`
   - **Release title**: `v1.44 - 新功能描述`
   - **Description**: 
     ```
     ## 🎉 更新内容
     
     - ✨ 新功能1
     - 🐛 修复bug1
     - 📝 改进文档
     
     ## 📦 安装说明
     
     下载 `app_logic.py` 文件替换旧版本即可。
     或者使用自动更新功能。
     ```

3. **上传文件** (重要!):
   - 点击 "Attach binaries by dropping them here or selecting them"
   - 选择并上传 `app_logic.py` 文件
   - 确保文件名正确为 `app_logic.py`

4. 点击 "Publish release"

## 自动更新工作流程

```
用户启动程序
    ↓
检查GitHub最新Release
    ↓
发现新版本 v1.44
    ↓
显示更新提示对话框
    ↓
用户点击"是"
    ↓
从Release下载 app_logic.py
    ↓
显示下载进度
    ↓
备份当前 app_logic.py → app_logic.py.backup
    ↓
替换为新版本
    ↓
显示"更新成功"
    ↓
自动重启程序
    ↓
程序以新版本运行
```

## 注意事项

1. **必须上传文件**: Release中必须包含 `app_logic.py` 文件作为附件(asset)

2. **文件名必须正确**: 上传的文件名必须是 `app_logic.py`,不能改名

3. **仓库必须公开**: 私有仓库无法通过API下载文件(除非使用token)

4. **版本号格式**: 必须以 `v` 开头,如 `v1.42`, `v1.43` 等

5. **备份文件**: 更新前会自动备份为 `app_logic.py.backup`,更新失败可以手动恢复

## 测试更新功能

1. 确保当前版本号是 `v1.42`
2. 创建一个 `v1.43` 的Release并上传 `app_logic.py`
3. 运行程序: `python 美化_renamer.py`
4. 应该会看到更新提示
5. 点击"是"测试自动下载和更新

## 故障排除

### 问题1: 提示"未找到更新文件"

**原因**: Release中没有上传 `app_logic.py` 文件

**解决**: 
1. 进入Release页面
2. 点击 "Edit release"
3. 上传 `app_logic.py` 文件
4. 保存

### 问题2: 下载失败

**原因**: 网络问题或代理设置

**解决**: 
1. 检查网络连接
2. 确保系统代理设置正确
3. 尝试手动下载测试

### 问题3: 更新后程序无法启动

**原因**: 新版本文件有问题

**解决**: 
1. 找到备份文件 `app_logic.py.backup`
2. 删除 `app_logic.py`
3. 重命名 `app_logic.py.backup` 为 `app_logic.py`
4. 重新启动程序

## 高级功能

如果需要更新多个文件,可以修改代码:
1. 在Release中上传多个文件
2. 修改 `download_and_update` 函数下载所有需要的文件
3. 按顺序替换文件

## 示例Release结构

```
v1.44
├── app_logic.py (必需)
├── README.md (可选)
└── CHANGELOG.md (可选)
```

只有 `app_logic.py` 会被自动下载和更新。
