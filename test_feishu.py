#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书通知测试脚本
模拟气象预警数据，测试飞书通知功能
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 导入主脚本的函数
from weather_alert import send_feishu_notification

def main():
    """测试飞书通知"""
    load_dotenv()

    feishu_webhook = os.getenv('FEISHU_WEBHOOK')
    report_url = os.getenv('REPORT_URL', 'https://example.com/report.html')

    if not feishu_webhook:
        print("错误：未配置 FEISHU_WEBHOOK")
        sys.exit(1)

    # 模拟预警数据
    location = {
        'name': '北京',
        'id': 'WX4FBXXFKE4F',
        'country': 'CN',
        'path': '北京,北京,中国',
        'timezone': 'Asia/Shanghai',
        'timezone_offset': '+08:00'
    }

    alarms = [
        {
            'type': '暴雨',
            'level': '橙色',
            'title': '北京市气象台发布暴雨橙色预警',
            'description': '预计未来3小时内，北京市大部分地区将出现50毫米以上降水',
            'pub_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'type': '大风',
            'level': '蓝色',
            'title': '北京市气象台发布大风蓝色预警',
            'description': '预计未来24小时内，北京市将出现6级以上大风',
            'pub_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]

    print("=" * 50)
    print("飞书通知测试")
    print("=" * 50)
    print(f"Webhook: {feishu_webhook[:50]}...")
    print(f"模拟预警数量: {len(alarms)}")
    print("\n开始发送测试通知...\n")

    # 发送飞书通知
    success = send_feishu_notification(feishu_webhook, location, alarms, report_url)

    if success:
        print("\n✓ 测试成功！请检查飞书群是否收到消息")
    else:
        print("\n✗ 测试失败，请查看日志")

if __name__ == '__main__':
    main()
