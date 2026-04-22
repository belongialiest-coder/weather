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
import hmac
import hashlib
import base64
from datetime import datetime
from jinja2 import Template
from dotenv import load_dotenv
from city_province_mapping import group_cities_by_province
from qweather_city_codes import get_city_code

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

    api_key = os.getenv('QWEATHER_API_KEY')
    cities_str = os.getenv('CITY', 'beijing')
    alert_types_str = os.getenv('ALERT_TYPES', '')
    feishu_webhook = os.getenv('FEISHU_WEBHOOK')
    feishu_secret = os.getenv('FEISHU_SECRET', '')  # 飞书签名密钥
    report_url = os.getenv('REPORT_URL', 'https://example.com/report.html')

    if not api_key or api_key == 'your_api_key_here':
        logging.error("错误：请在 .env 文件中配置有效的 QWEATHER_API_KEY")
        sys.exit(1)

    # 解析城市列表（支持逗号分隔）
    cities = [city.strip() for city in cities_str.split(',') if city.strip()]

    # 解析预警类型过滤列表
    alert_types = [t.strip() for t in alert_types_str.split(',') if t.strip()] if alert_types_str else []

    return api_key, cities, alert_types, feishu_webhook, feishu_secret, report_url


def get_weather_alarms(api_key, city):
    """调用和风天气 API 获取气象预警信息（带重试机制）"""
    # 将城市中文名转换为城市代码
    city_code = get_city_code(city)
    if city_code is None:
        logging.warning(f"城市 {city} 找不到对应的代码，跳过该城市")
        return None

    url = 'https://api.qweather.com/v1/warning/now'

    params = {
        'location': city_code,
        'key': api_key,
        'lang': 'zh'
    }

    for attempt in range(API_CONFIG["max_retries"]):
        try:
            logging.info(f"正在获取气象预警信息... (尝试 {attempt + 1}/{API_CONFIG['max_retries']})")
            response = requests.get(url, params=params, timeout=API_CONFIG["timeout"])

            # 特殊处理404错误（城市不存在）
            if response.status_code == 404:
                logging.warning(f"城市 {city} 未找到（404），跳过该城市")
                return None

            response.raise_for_status()
            data = response.json()

            # 检查API返回的错误
            if 'code' in data and data['code'] != '200':
                error_msg = data.get('msg', 'API返回错误')
                logging.error(f"API错误: {error_msg} (代码: {data['code']})")
                if data['code'] == '401':
                    logging.error("API Key无效，请检查配置")
                    sys.exit(1)
                return None

            logging.info("成功获取预警数据")
            return data

        except requests.exceptions.Timeout:
            logging.warning(f"请求超时 (尝试 {attempt + 1}/{API_CONFIG['max_retries']})")
            if attempt < API_CONFIG["max_retries"] - 1:
                time.sleep(API_CONFIG["initial_delay"])
        except requests.exceptions.HTTPError as e:
            # 4xx客户端错误（如404）跳过，5xx服务器错误重试
            if 400 <= e.response.status_code < 500:
                logging.warning(f"客户端错误 {e.response.status_code}，跳过城市 {city}")
                return None
            else:
                logging.error(f"服务器错误: {e}")
                if attempt < API_CONFIG["max_retries"] - 1:
                    time.sleep(API_CONFIG["initial_delay"])
        except requests.exceptions.RequestException as e:
            logging.error(f"API请求失败: {e}")
            if attempt < API_CONFIG["max_retries"] - 1:
                time.sleep(API_CONFIG["initial_delay"])

    logging.warning(f"城市 {city} 达到最大重试次数，跳过")
    return None


def extract_alarms(data):
    """提取预警数据"""
    try:
        # 和风天气API返回格式：data['warning'] 是一个数组
        alarms = data.get('warning', [])
        if not alarms:
            return None, None

        # 城市信息存储在顶级字段中
        location = {
            'id': data.get('id', ''),
            'name': data.get('name', 'Unknown'),
            'country': data.get('country', 'China'),
            'adm1': data.get('adm1', ''),
            'adm2': data.get('adm2', ''),
            'lat': data.get('lat', ''),
            'lon': data.get('lon', '')
        }

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


def gen_feishu_sign(secret):
    """
    生成飞书机器人签名

    参数:
        secret: 飞书机器人的签名密钥

    返回:
        (timestamp, sign): 时间戳和签名字符串
    """
    # 获取当前时间戳
    timestamp = str(int(time.time()))

    # 拼接字符串: timestamp + "\n" + secret
    string_to_sign = '{}\n{}'.format(timestamp, secret)

    # 使用HmacSHA256算法计算签名
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()

    # 对结果进行base64编码
    sign = base64.b64encode(hmac_code).decode('utf-8')

    return timestamp, sign


def filter_alarms_by_type(alarms, alert_types):
    """
    根据预警类型过滤预警信息
    只保留指定类型的预警（台风、雪、寒潮、冰雹、大雾）
    """
    if not alert_types:
        return alarms  # 如果没有指定过滤类型，返回所有预警

    filtered_alarms = []
    for alarm in alarms:
        alarm_type = alarm.get('type', '')
        # 检查预警类型是否包含任何一个需要监控的关键词
        if any(keyword in alarm_type for keyword in alert_types):
            filtered_alarms.append(alarm)
        else:
            logging.info(f"过滤掉不相关的预警: {alarm_type} - {alarm.get('title', '')}")

    return filtered_alarms


def deduplicate_alarms_by_type(alarms):
    """
    对同一类型的预警去重，只保留更新时间最新的那一条
    注意：相同类型不同等级的预警（如"大雾-黄色"和"大雾-橙色"）会被去重，只保留最新的一条

    参数:
        alarms: 预警列表

    返回:
        去重后的预警列表（每种类型只保留最新的一条，不区分等级）
    """
    if not alarms:
        return alarms

    # 按预警类型分组，保留每种类型最新的一条（不区分等级）
    alarm_dict = {}

    for alarm in alarms:
        alarm_type = alarm.get('type', '未知')
        alarm_level = alarm.get('severity', '未知')
        # 只使用"类型"作为key，不区分等级
        key = alarm_type

        # 获取预警的更新时间 (和风天气使用 pubTime)
        pub_time = alarm.get('pubTime', '')

        # 如果该类型预警不存在，或者当前预警更新时间更晚，则更新
        if key not in alarm_dict:
            alarm_dict[key] = alarm
            logging.info(f"  保留预警: {key} ({alarm_level}) - 更新时间: {pub_time}")
        else:
            existing_pub_time = alarm_dict[key].get('pubTime', '')
            existing_level = alarm_dict[key].get('severity', '未知')
            # 比较更新时间，保留最新的
            if pub_time > existing_pub_time:
                logging.info(f"  更新预警: {key} ({existing_level} -> {alarm_level}) - 新时间: {pub_time} > 旧时间: {existing_pub_time}")
                alarm_dict[key] = alarm
            else:
                logging.info(f"  过滤重复预警: {key} ({alarm_level}) - 时间: {pub_time} <= {existing_pub_time}")

    # 返回去重后的预警列表
    deduplicated_alarms = list(alarm_dict.values())

    if len(deduplicated_alarms) < len(alarms):
        logging.info(f"  去重完成: {len(alarms)} 条 -> {len(deduplicated_alarms)} 条（移除 {len(alarms) - len(deduplicated_alarms)} 条重复预警）")

    return deduplicated_alarms


def render_html(cities_data, template_path='template.html', output_path='index.html'):
    """使用 Jinja2 模板渲染 HTML（支持多城市，按省份分组）"""

    # 读取模板文件
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
    except FileNotFoundError:
        logging.error(f"错误：模板文件 {template_path} 不存在")
        sys.exit(1)

    # 为每个城市的每个预警添加颜色信息
    for city_data in cities_data:
        for alarm in city_data['alarms']:
            alarm['color'] = get_alert_color(alarm.get('level', ''))

    # 按省份分组
    provinces_data = group_cities_by_province(cities_data)

    # 统计总预警数
    total_alarms = sum(len(city_data['alarms']) for city_data in cities_data)

    # 渲染模板
    template = Template(template_content)
    html_content = template.render(
        cities_data=cities_data,
        provinces_data=provinces_data,
        update_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        has_alarms=total_alarms > 0,
        total_alarms=total_alarms
    )

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logging.info(f"HTML 报告已生成: {output_path}")


def build_feishu_card(cities_data, report_url):
    """构建飞书消息卡片 JSON payload（支持多城市，按省份分组）"""

    # 按省份分组
    provinces_data = group_cities_by_province(cities_data)

    # 统计总预警数和有预警的省份
    total_alarms = sum(province_data['total_alarms'] for province_data in provinces_data.values())
    provinces_with_alarms = {k: v for k, v in provinces_data.items() if v['total_alarms'] > 0}

    has_alarms = total_alarms > 0

    # 预警等级 emoji 映射（和风天气使用 severity）
    level_emoji = {
        '极端': '🔴',
        '严重': '🟠',
        '较重': '🟡',
        '轻微': '🔵',
    }

    # 根据是否有预警，设置不同的卡片样式
    if has_alarms:
        header_title = "⚠️ 多地区异常天气预警"
        header_template = "red"

        # 列出有预警的省份
        province_list = '、'.join(list(provinces_with_alarms.keys())[:8])  # 最多显示8个省份
        if len(provinces_with_alarms) > 8:
            province_list += f" 等 {len(provinces_with_alarms)} 个省份"

        status_text = f"**预警省份：** {province_list}\n**预警总数：** {total_alarms} 条"
    else:
        header_title = "✅ 所有监控区域天气正常"
        header_template = "green"
        status_text = f"**监控城市：** {len(cities_data)} 个\n**预警数量：** 0 条\n\n☀️ 当前所有区域无气象预警"

    # 构建预警列表内容（按省份分组，显示所有预警）
    alarm_elements = []
    if has_alarms:
        # 按省份展示所有预警
        for province_name, province_data in provinces_with_alarms.items():
            # 添加省份标题
            alarm_elements.append({
                "tag": "hr"
            })
            alarm_elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**📍 {province_name}**（{province_data['total_alarms']} 条预警）"
                }
            })

            # 显示该省份的所有城市预警
            for city_data in province_data['cities']:
                if city_data['alarms']:
                    for alarm in city_data['alarms']:
                        alarm_type = alarm.get('type', '未知')
                        alarm_severity = alarm.get('severity', '未知')
                        city_name = city_data['name']

                        # 获取预警等级的 emoji
                        emoji = '⚪'
                        for key, val in level_emoji.items():
                            if key in alarm_severity:
                                emoji = val
                                break

                        # 添加预警信息
                        alarm_elements.append({
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"  {emoji} **{alarm_type} - {alarm_severity}** | {city_name}"
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
                                "content": "📋 查看完整预警详情"
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
                            "content": f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 数据源：和风天气"
                        }
                    ]
                }
            ]
        }
    }

    return card


def send_feishu_notification(webhook_url, cities_data, report_url, secret=''):
    """
    发送飞书通知（支持多城市和签名校验）

    参数:
        webhook_url: 飞书webhook地址
        cities_data: 城市数据列表
        report_url: 报告URL
        secret: 飞书签名密钥（可选，如果配置了则启用签名校验）
    """
    if not webhook_url:
        logging.warning("未配置飞书 Webhook，跳过通知")
        return False

    try:
        card = build_feishu_card(cities_data, report_url)

        # 如果配置了签名密钥，添加签名信息
        if secret:
            timestamp, sign = gen_feishu_sign(secret)
            card['timestamp'] = timestamp
            card['sign'] = sign
            logging.info(f"已启用飞书签名校验 (timestamp: {timestamp})")
        else:
            logging.warning("未配置飞书签名密钥，建议配置以提高安全性")

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
    """主函数（支持多城市监控和预警过滤）"""
    logging.info("=" * 50)
    logging.info("气象预警脚本 - 多城市监控版")
    logging.info("=" * 50)

    # 加载配置
    api_key, cities, alert_types, feishu_webhook, feishu_secret, report_url = load_config()
    logging.info(f"监控城市数量: {len(cities)}")
    logging.info(f"城市列表: {', '.join(cities[:10])}{'...' if len(cities) > 10 else ''}")
    logging.info(f"监控预警类型: {', '.join(alert_types) if alert_types else '全部'}")

    # 存储所有城市的预警数据
    cities_data = []
    total_alarms_before_filter = 0
    total_alarms_after_filter = 0
    success_count = 0
    failed_count = 0

    # 逐个城市查询预警
    for idx, city in enumerate(cities, 1):
        logging.info(f"\n正在查询城市: {city} ({idx}/{len(cities)})")

        # 获取预警数据
        data = get_weather_alarms(api_key, city)

        if data is None:
            logging.warning(f"城市 {city} 查询失败，跳过")
            failed_count += 1
            # 添加延迟避免API超载
            time.sleep(0.8)
            continue

        # 提取预警信息
        location, alarms = extract_alarms(data)

        if location is None:
            logging.warning(f"城市 {city} 数据解析失败，跳过")
            failed_count += 1
            # 添加延迟避免API超载
            time.sleep(0.8)
            continue

        city_name = location.get('name', city)
        total_alarms_before_filter += len(alarms)
        success_count += 1

        # 过滤预警类型
        if alert_types and alarms:
            filtered_alarms = filter_alarms_by_type(alarms, alert_types)
            logging.info(f"  原始预警数: {len(alarms)}, 过滤后: {len(filtered_alarms)}")
            alarms = filtered_alarms

        # 对同类型预警去重，只保留最新的一条
        if alarms:
            alarms = deduplicate_alarms_by_type(alarms)

        total_alarms_after_filter += len(alarms)

        # 存储城市数据
        cities_data.append({
            'name': city_name,
            'location': location,
            'alarms': alarms
        })

        if alarms:
            logging.info(f"  ✓ {city_name}: {len(alarms)} 条预警")
            for alarm in alarms:
                logging.info(f"    - {alarm.get('type', '未知')} | {alarm.get('level', '未知')}")
        else:
            logging.info(f"  ✓ {city_name}: 无预警")

        # 添加延迟避免API超载（每个城市查询后等待0.8秒）
        time.sleep(0.8)

    # 汇总统计
    logging.info("\n" + "=" * 50)
    logging.info(f"查询完成！")
    logging.info(f"总城市数: {len(cities)} 个")
    logging.info(f"查询成功: {success_count} 个")
    logging.info(f"查询失败: {failed_count} 个")
    logging.info(f"总预警数（过滤前）: {total_alarms_before_filter} 条")
    logging.info(f"总预警数（过滤后）: {total_alarms_after_filter} 条")
    logging.info(f"过滤掉: {total_alarms_before_filter - total_alarms_after_filter} 条不相关预警")
    logging.info("=" * 50)

    # 生成 HTML 报告
    logging.info("\n正在生成 HTML 报告...")
    render_html(cities_data)

    # 发送飞书通知（无论是否有预警都发送）
    logging.info("\n准备发送飞书通知...")
    send_feishu_notification(feishu_webhook, cities_data, report_url, feishu_secret)

    logging.info("\n完成！")


if __name__ == '__main__':
    main()
