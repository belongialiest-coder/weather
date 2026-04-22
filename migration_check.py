#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 迁移完整性检查脚本
验证所有改动是否正确应用
"""

import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (NOT FOUND)")
        return False

def check_file_contains(filepath, keywords, description):
    """检查文件是否包含指定关键字"""
    if not os.path.exists(filepath):
        print(f"❌ {description}: 文件不存在 - {filepath}")
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for keyword in keywords if isinstance(keywords, list) else [keywords]:
            if keyword not in content:
                missing.append(keyword)

        if not missing:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}: 缺少关键字 - {missing}")
            return False
    except Exception as e:
        print(f"❌ {description}: 读取失败 - {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 API 迁移完整性检查")
    print("=" * 60)

    results = []

    # 1. 检查新增文件
    print("\n📁 [1] 新增文件检查")
    results.append(check_file_exists(
        'qweather_city_codes.py',
        '城市编码映射文件'
    ))

    # 2. 检查核心代码改动
    print("\n⚙️  [2] 核心代码改动检查")
    results.append(check_file_contains(
        'weather_alert.py',
        ['from qweather_city_codes import get_city_code', 'QWEATHER_API_KEY'],
        '导入和风模块 & API Key参数'
    ))

    results.append(check_file_contains(
        'weather_alert.py',
        'api.qweather.com/v1/warning/now',
        'API 端点更新'
    ))

    results.append(check_file_contains(
        'weather_alert.py',
        'get_city_code(city)',
        '城市编码转换调用'
    ))

    results.append(check_file_contains(
        'weather_alert.py',
        ["data.get('warning', [])", "alarm.get('pubTime')", "alarm.get('severity')"],
        '数据字段映射更新'
    ))

    # 3. 检查配置文件改动
    print("\n🔑 [3] 配置文件改动检查")
    results.append(check_file_contains(
        '.env.example',
        'QWEATHER_API_KEY',
        '.env.example - API Key 参数更新'
    ))

    results.append(check_file_contains(
        '.env',
        ['QWEATHER_API_KEY=5afec64e1bd54a4d8a9c8443694289ff',
         'https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548',
         'fJMgCkWIQVbQlt5C994KSe'],
        '.env - 配置信息更新'
    ))

    # 4. 检查 GitHub Actions 配置
    print("\n🔄 [4] GitHub Actions 配置检查")
    results.append(check_file_contains(
        '.github/workflows/weather_alert.yml',
        'QWEATHER_API_KEY',
        'Workflow - API Key Secret 变量更新'
    ))

    # 5. 检查是否没有遗留旧参数
    print("\n⚠️  [5] 遗留旧参数检查")
    old_api_check = check_file_contains(
        'weather_alert.py',
        'SENIVERSE_API_KEY',
        '检查是否遗留旧的心知天气参数'
    )
    if not old_api_check:
        print("✅ 未发现遗留的 SENIVERSE_API_KEY（正确）")
        results.append(True)
    else:
        print("❌ 发现遗留的 SENIVERSE_API_KEY（需要移除）")
        results.append(False)

    # 6. 城市编码映射表检查
    print("\n🗺️  [6] 城市编码映射表检查")
    try:
        from qweather_city_codes import CITY_CODE_MAP, get_city_code

        city_count = len(CITY_CODE_MAP)
        print(f"✅ 城市映射表加载成功 - 共 {city_count} 个城市")
        results.append(city_count >= 139)

        # 测试几个关键城市
        test_cities = ['北京', '上海', '深圳']
        for city in test_cities:
            code = get_city_code(city)
            if code:
                print(f"  ✅ {city} → {code}")
                results.append(True)
            else:
                print(f"  ❌ {city} → 找不到代码")
                results.append(False)
    except Exception as e:
        print(f"❌ 城市编码映射表检查失败: {e}")
        results.append(False)

    # 7. Python 语法检查
    print("\n📝 [7] Python 语法检查")
    try:
        import py_compile
        py_compile.compile('weather_alert.py', doraise=True)
        print("✅ weather_alert.py 语法检查通过")
        results.append(True)
    except Exception as e:
        print(f"❌ weather_alert.py 语法检查失败: {e}")
        results.append(False)

    # 总结
    print("\n" + "=" * 60)
    print("📊 检查总结")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {total - passed}")
    print(f"总计: {total}")

    if passed == total:
        print("\n🎉 所有检查通过！API 迁移完成。")
        print("\n📋 下一步：")
        print("1. 提交代码到 Git")
        print("2. 在 GitHub 更新 Secrets（删除 SENIVERSE_API_KEY，添加 QWEATHER_API_KEY）")
        print("3. 手动测试 GitHub Actions 工作流")
        print("4. 验证飞书通知是否正常发送")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 项检查失败，请检查日志。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
