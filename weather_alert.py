#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
气象预警脚本
使用心知天气 API 获取气象灾害预警信息，并生成美观的 HTML 报告
"""

import os
import sys
import requests
import logging
import time
from datetime import datetime
from jinja2 import Template
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='weather_alert.log'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)


# 预警等级颜色映射
ALERT_LEVEL_COLORS = {
    '红色': '#FF4444',
    '橙色': '#FF8800',
    '黄色': '#FFCC00',
    '蓝色': '#4488FF',
    '白色': '#CCCCCC',
}

# API配置
API_CONFIG = {
    "max_retries": 3,
    "initial_delay": 2,
    "timeout": 10
}


def load_config():
    """从 .env 文件加载配置"""
    load_dotenv()

    api_key = os.getenv('SENIVERSE_API_KEY')
    city = os.getenv('CITY', 'beijing')
    feishu_webhook = os.getenv('FEISHU_WEBHOOK')
    report_url = os.getenv('REPORT_URL', 'https://example.com/report.html')

    if not api_key or api_key == 'your_api_key_here':
        logging.error("错误：请在 .env 文件中配置有效的 SENIVERSE_API_KEY")
        sys.exit(1)

    return api_key, city, feishu_webhook, report_url


def get_weather_alarms(api_key, city):
    """调用心知天气 API 获取气象预警信息（带重试机制）"""
    url = 'https://api.seniverse.com/v3/weather/alarm.json'

    params = {
        'key': api_key,
        'location': city,
        'language': 'zh-Hans',
        'detail': 'more'
    }

    for attempt in range(API_CONFIG["max_retries"]):
        try:
            logging.info(f"正在获取气象预警信息... (尝试 {attempt + 1}/{API_CONFIG['max_retries']})")
            response = requests.get(url, params=params, timeout=API_CONFIG["timeout"])
            response.raise_for_status()
            data = response.json()

            # 检查API返回的错误
            if 'status_code' in data:
                error_msg = data.get('status', 'API返回错误')
                logging.error(f"API错误: {error_msg} (状态码: {data['status_code']})")
                if data['status_code'] == 'AP010003':
                    logging.error("API Key无效，请检查配置")
                    sys.exit(1)
                return None

            logging.info("成功获取预警数据")
            return data

        except requests.exceptions.Timeout:
            logging.warning(f"请求超时 (尝试 {attempt + 1}/{API_CONFIG['max_retries']})")
            if attempt < API_CONFIG["max_retries"] - 1:
                time.sleep(API_CONFIG["initial_delay"])
        except requests.exceptions.RequestException as e:
            logging.error(f"API请求失败: {e}")
            if attempt < API_CONFIG["max_retries"] - 1:
                time.sleep(API_CONFIG["initial_delay"])
            else:
                sys.exit(1)

    logging.error("达到最大重试次数")
    sys.exit(1)


def extract_alarms(data):
    """提取预警数据"""
    try:
        results = data.get('results', [])
        if not results:
            return None, None

        location = results[0].get('location', {})
        alarms = results[0].get('alarms', [])

        return location, alarms
    except (KeyError, IndexError) as e:
        logging.error(f"数据解析失败: {e}")
        return None, None


def get_alert_color(level):
    """根据预警等级返回对应颜色"""
    for key in ALERT_LEVEL_COLORS:
        if key in level:
            return ALERT_LEVEL_COLORS[key]
    return '#888888'


def render_html(location, alarms, template_path='template.html', output_path='index.html'):
    """使用 Jinja2 模板渲染 HTML"""

    # 读取模板文件
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logging.error(f"错误：模板文件 {template_path} 不存在")
        sys.exit(1)

    # 为每个预警添加颜色信息
    for alarm in alarms:
        alarm['color'] = get_alert_color(alarm.get('level', ''))

    # 城市在 SVG 地图上的坐标映射（基于 800x600 的 viewBox）
    city_coords = {
        '北京': (430, 180),
        '上海': (530, 340),
        '广州': (460, 480),
        '深圳': (465, 500),
        '成都': (320, 360),
        '杭州': (520, 360),
        '重庆': (340, 380),
        '西安': (360, 280),
        '苏州': (525, 345),
        '武汉': (440, 360),
        '天津': (440, 190),
        '南京': (500, 340),
        '长沙': (440, 400),
        '郑州': (420, 300),
        '沈阳': (480, 140),
        '青岛': (480, 270),
        '济南': (455, 265),
        '哈尔滨': (490, 100),
        '昆明': (300, 450),
        '厦门': (490, 440)
    }

    # 获取城市坐标，默认使用北京
    city_name = location.get('name', '北京')
    city_x, city_y = city_coords.get(city_name, (430, 180))

    # 渲染模板
    template = Template(template_content)
    html_content = template.render(
        location=location,
        alarms=alarms,
        update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        has_alarms=len(alarms) > 0,
        city_x=city_x,
        city_y=city_y
    )

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logging.info(f"HTML 报告已生成: {output_path}")


def build_feishu_card(location, alarms, report_url):
    """构建飞书消息卡片 JSON payload"""
    city_name = location.get('name', '未知')
    has_alarms = len(alarms) > 0

    # 预警等级 emoji 映射
    level_emoji = {
        '红色': '🔴',
        '橙色': '🟠',
        '黄色': '🟡',
        '蓝色': '🔵',
        '白色': '⚪'
    }

    # 根据是否有预警，设置不同的卡片样式
    if has_alarms:
        header_title = "⚠️ 区域异常天气预警"
        header_template = "red"
        status_text = f"**监控区域：** {city_name}\n**预警数量：** {len(alarms)} 条"
    else:
        header_title = "✅ 天气状况正常"
        header_template = "green"
        status_text = f"**监控区域：** {city_name}\n**预警数量：** 0 条\n\n☀️ 当前无气象预警，天气状况良好"

    # 构建预警列表内容
    alarm_elements = []
    if has_alarms:
        for alarm in alarms:
            alarm_type = alarm.get('type', '未知')
            alarm_level = alarm.get('level', '未知')
            pub_date = alarm.get('pub_date', '未知时间')
            emoji = level_emoji.get(alarm_level, '⚪')

            # 添加分割线
            alarm_elements.append({
                "tag": "hr"
            })

            # 添加预警信息
            alarm_elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{emoji} {alarm_type} - {alarm_level}**\n📍 城市：{city_name}\n🕒 发布时间：{pub_date}"
                }
            })

    # 构建完整卡片
    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": header_title
                },
                "template": header_template
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": status_text
                    }
                }
            ] + alarm_elements + [
                {
                    "tag": "hr"
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看详细风险报告"
                            },
                            "type": "primary",
                            "url": report_url
                        }
                    ]
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
    }

    return card


def send_feishu_notification(webhook_url, location, alarms, report_url):
    """发送飞书通知"""
    if not webhook_url:
        logging.warning("未配置飞书 Webhook，跳过通知")
        return False

    try:
        card = build_feishu_card(location, alarms, report_url)
        logging.info("正在发送飞书通知...")

        response = requests.post(webhook_url, json=card, timeout=10)
        response.raise_for_status()

        result = response.json()
        if result.get('code') == 0:
            logging.info("✓ 飞书通知发送成功")
            return True
        else:
            logging.error(f"飞书通知发送失败: {result}")
            return False

    except Exception as e:
        logging.error(f"飞书通知发送异常: {e}")
        return False


def main():
    """主函数"""
    logging.info("=" * 50)
    logging.info("气象预警脚本")
    logging.info("=" * 50)

    # 加载配置
    api_key, city, feishu_webhook, report_url = load_config()
    logging.info(f"查询城市: {city}")

    # 获取预警数据
    data = get_weather_alarms(api_key, city)

    if data is None:
        logging.error("未获取到有效数据")
        sys.exit(1)

    # 提取预警信息
    location, alarms = extract_alarms(data)

    if location is None:
        logging.error("未获取到有效数据")
        sys.exit(1)

    city_name = location.get('name', '未知')
    logging.info(f"城市: {city_name}")
    logging.info(f"预警数量: {len(alarms)}")

    if alarms:
        logging.info("\n当前预警:")
        for alarm in alarms:
            logging.info(f"  - {alarm.get('type', '未知')} | {alarm.get('level', '未知')} | {alarm.get('title', '')}")
    else:
        logging.info("\n当前无气象预警 ✓")

    # 生成 HTML 报告
    logging.info("\n正在生成 HTML 报告...")
    render_html(location, alarms)

    # 发送飞书通知（无论是否有预警都发送）
    logging.info("\n准备发送飞书通知...")
    send_feishu_notification(feishu_webhook, location, alarms, report_url)

    logging.info("\n完成！")


if __name__ == '__main__':
    main()
