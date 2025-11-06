#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件名匹配逻辑
"""

def test_generate_new_name():
    """测试文件名生成逻辑"""
    
    # 模拟项目代号配置
    project_codes = {
        "洗衣店偷衣服": "Pre-shoot-洗衣店偷衣服-C02---华容道平铺02-tileflower",
        "插队的补偿": "Pre-shoot-插队的补偿-C01-华容道平铺02tileflower",
        "无语言偷看1": "pre-shoot-无语言偷看1"
    }
    
    # 模拟差分规则配置
    diff_rules = {
        "1": ("核玩翻页", "HWFY", "cn"),
        "2": ("动画quiz-批量化", "BVC", "es"),
        "4": ("核玩新版", "SLT", "en")
    }
    
    def generate_new_name(original_name_no_ext):
        """生成新文件名 - 修复后的版本"""
        # 新的解析逻辑：基于项目代号匹配
        matched_code = None
        matched_project = None
        
        # 寻找匹配的项目代号（按长度从长到短排序，避免短代号误匹配长代号）
        sorted_codes = sorted(project_codes.items(), key=lambda x: len(x[0]), reverse=True)
        
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
        if diff_num not in diff_rules:
            return f"[差分号{diff_num}无规则]", "❌"
        
        # 获取规则信息
        rule_data = diff_rules[diff_num]
        if len(rule_data) != 3:
            return f"[差分号{diff_num}规则不完整]", "❌"
        
        full_name, abbr, lang = rule_data
        
        # 检查规则数据是否完整
        if not all([full_name.strip(), abbr.strip(), lang.strip()]):
            return f"[差分号{diff_num}规则数据不完整]", "❌"
        
        # 生成最终文件名
        date = "251013"  # 测试用日期
        final_name = f"{date}_{matched_project}+{full_name}_{lang}_{abbr}_1080x1920"
        
        return final_name, "✅"
    
    # 测试用例
    test_cases = [
        "洗衣店偷衣服-2",
        "洗衣店偷衣服2", 
        "洗衣店偷衣服-1",
        "洗衣店偷衣服1",
        "洗衣店偷衣服-4",
        "插队的补偿-2",
        "插队的补偿1",
        "无语言偷看1-2",
        "洗衣店偷衣服-3",  # 无规则的差分号
        "洗衣店偷衣服-abc",  # 非数字差分号
        "不存在的项目-2",  # 无匹配项目
        "洗衣店偷衣服",  # 缺少差分号
    ]
    
    print("=" * 80)
    print("文件名匹配测试结果")
    print("=" * 80)
    
    for test_case in test_cases:
        result, status = generate_new_name(test_case)
        print(f"输入: {test_case}")
        print(f"输出: {result}")
        print(f"状态: {status}")
        print("-" * 40)

if __name__ == "__main__":
    test_generate_new_name()
