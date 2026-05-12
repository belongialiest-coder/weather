#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
西太平洋热带扰动监控脚本
使用 tropycal 获取 JTWC 实时数据，监控西太平洋热带扰动和热带气旋，并发送飞书通知
"""

import os
import sys
import logging
import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='typhoon_monitor.log'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)


def load_config():
    """从环境变量加载配置"""
    load_dotenv()
    feishu_webhook = os.getenv('FEISHU_WEBHOOK')
    feishu_secret = os.getenv('FEISHU_SECRET', '')
    report_url = os.getenv('REPORT_URL', '')
    return feishu_webhook, feishu_secret, report_url


def get_storm_type_label(storm_type):
    """获取热带气旋类型中文标签"""
    type_map = {
        'invest': '热带扰动',
        'tropical depression': '热带低压',
        'tropical storm': '热带风暴',
        'typhoon': '台风',
        'supertyphoon': '超强台风',
        'subtropical storm': '亚热带风暴',
        'subtropical depression': '亚热带低压',
    }
    key = (storm_type or '').lower()
    return type_map.get(key, storm_type or '未知')


def get_storm_report_time(storm):
    """从 storm 对象中提取最新报文时间，返回 datetime 或 None"""
    times = getattr(storm, 'time', None)
    if times and len(times) > 0:
        t = times[-1]
        # tropycal 返回的可能是 numpy.datetime64 或 datetime
        if hasattr(t, 'to_pydatetime'):
            return t.to_pydatetime().replace(tzinfo=timezone.utc)
        if isinstance(t, datetime):
            return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
        try:
            import pandas as pd
            return pd.Timestamp(t).to_pydatetime().replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def fetch_wp_disturbances():
    """获取西太平洋活跃热带扰动数据，返回 (wp_systems, tcfas, jtwc_update_time)"""
    try:
        import tropycal.realtime as realtime
    except Exception as e:
        logging.error(f"tropycal 导入失败（跳过数据获取，生成空报告）: {e}")
        return {}, {}, None

    logging.info("正在从 JTWC 获取西太平洋热带扰动数据...")

    try:
        rt = realtime.Realtime(jtwc=True, jtwc_source='jtwc')
    except Exception as e:
        logging.warning(f"JTWC 主源获取失败，尝试备用源: {e}")
        try:
            rt = realtime.Realtime(jtwc=True, jtwc_source='ucar')
        except Exception as e2:
            logging.error(f"备用源也失败: {e2}")
            return {}, {}, None

    # 过滤西太平洋 (WP) 系统
    try:
        active_storms = rt.get_active_storms()
        wp_systems = {k: v for k, v in active_storms.items() if k.startswith('WP')}
    except Exception as e:
        logging.error(f"获取活跃风暴失败: {e}")
        wp_systems = {}

    # 从各系统报文时间中取最新的作为 JTWC 整体更新时间
    jtwc_update_time = None
    for storm in wp_systems.values():
        t = get_storm_report_time(storm)
        if t and (jtwc_update_time is None or t > jtwc_update_time):
            jtwc_update_time = t

    # 获取 TCFA 信息
    tcfas = {}
    try:
        tcfa_list = rt.get_tcfas()
        for tcf in tcfa_list:
            invest_id = tcf.get('invest_id', '')
            if invest_id.startswith('WP'):
                tcfas[invest_id] = tcf
    except Exception as e:
        logging.warning(f"获取 TCFA 数据失败（可能当前无 TCFA）: {e}")

    logging.info(f"找到 {len(wp_systems)} 个西太平洋活跃系统，{len(tcfas)} 个 TCFA")
    if jtwc_update_time:
        logging.info(f"JTWC 最新报文时间: {jtwc_update_time.strftime('%Y-%m-%d %H:%M UTC')}")
    return wp_systems, tcfas, jtwc_update_time


def gen_feishu_sign(secret):
    """生成飞书机器人签名"""
    timestamp = str(int(time.time()))
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256
    ).digest()
    sign = base64.b64encode(hmac_code).decode('utf-8')
    return timestamp, sign


def render_html(wp_systems, tcfas, jtwc_update_time=None, output_path='index.html'):
    """生成热带扰动监控 HTML 报告"""
    now_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    jtwc_time_str = (jtwc_update_time.strftime('%Y-%m-%d %H:%M UTC')
                     if jtwc_update_time else '暂无数据')
    tcfa_count = len(tcfas)
    invest_count = sum(1 for s in wp_systems.values() if getattr(s, 'type', '').lower() == 'invest')
    active_count = len(wp_systems) - invest_count

    # 构建并排序系统列表
    type_order = {'supertyphoon': 0, 'typhoon': 1, 'tropical storm': 2,
                  'tropical depression': 3, 'invest': 4}
    systems_data = []
    for storm_id, storm in wp_systems.items():
        type_raw = getattr(storm, 'type', '') or ''
        lat = getattr(storm, 'lat', None)
        lon = getattr(storm, 'lon', None)
        systems_data.append({
            'id': storm_id,
            'type_raw': type_raw,
            'type_label': get_storm_type_label(type_raw),
            'lat': lat,
            'lon': lon,
            'wind': getattr(storm, 'wind', None),
            'pressure': getattr(storm, 'pressure', None),
            'movement_dir': getattr(storm, 'movement_dir', None),
            'movement_speed': getattr(storm, 'movement_speed', None),
            'has_tcfa': storm_id in tcfas,
            'tcfa': tcfas.get(storm_id, {}),
            'report_time': get_storm_report_time(storm),
        })
    systems_data.sort(key=lambda x: type_order.get(x['type_raw'].lower(), 99))

    # CSS 样式映射
    card_classes = {
        'supertyphoon': ('supertyphoon', '#FF4444'),
        'typhoon': ('typhoon', '#FF8800'),
        'tropical storm': ('ts', '#FFCC00'),
        'tropical depression': ('td', '#48bb78'),
        'invest': ('invest', '#4488FF'),
    }

    # 生成风暴卡片 HTML
    cards_html = ''
    for s in systems_data:
        type_key = s['type_raw'].lower()
        card_cls, border_color = card_classes.get(type_key, ('invest', '#4488FF'))

        lat_str = f"北纬 {s['lat']:.1f}°" if s['lat'] is not None else 'N/A'
        lon_str = f"东经 {s['lon']:.1f}°" if s['lon'] is not None else 'N/A'
        wind_str = f"{s['wind']} 节" if s['wind'] is not None else 'N/A'
        pres_str = f"{s['pressure']} hPa" if s['pressure'] is not None else 'N/A'
        move_str = (f"{s['movement_dir']}° / {s['movement_speed']} 节"
                    if s['movement_dir'] is not None else 'N/A')
        rpt_str = (s['report_time'].strftime('%m-%d %H:%MZ')
                   if s['report_time'] else 'N/A')

        tcfa_badge = '<span class="badge badge-tcfa">TCFA</span>' if s['has_tcfa'] else ''
        tcfa_alert = ''
        if s['has_tcfa']:
            tcf = s['tcfa']
            dev_prob = tcf.get('development_probability', 'N/A')
            issue_time = tcf.get('issue_time', 'N/A')
            tcfa_alert = (
                f'<div class="tcfa-alert">'
                f'⚠️ JTWC 已发布热带气旋形成警报 (TCFA) — '
                f'发展概率：{dev_prob}，发布时间：{issue_time}'
                f'</div>'
            )

        cards_html += f'''
        <div class="storm-card {card_cls}" style="border-left-color:{border_color}">
            <div class="storm-header">
                <div class="storm-id">{s["id"]}</div>
                <div class="badge-row">
                    <span class="badge" style="background:{border_color};{'color:#333' if type_key=='tropical storm' else ''}">{s["type_label"]}</span>
                    {tcfa_badge}
                </div>
            </div>
            <div class="storm-info">
                <div class="info-item"><div class="info-label">位置</div><div class="info-value">{lat_str}, {lon_str}</div></div>
                <div class="info-item"><div class="info-label">最大风速</div><div class="info-value">{wind_str}</div></div>
                <div class="info-item"><div class="info-label">中心气压</div><div class="info-value">{pres_str}</div></div>
                <div class="info-item"><div class="info-label">移动方向/速度</div><div class="info-value">{move_str}</div></div>
                <div class="info-item"><div class="info-label">📡 报文时间 (UTC)</div><div class="info-value">{rpt_str}</div></div>
            </div>
            {tcfa_alert}
        </div>'''

    no_systems_html = ''
    if not wp_systems:
        no_systems_html = '''
        <div class="no-systems">
            <div class="icon">🌤️</div>
            <h2>西太平洋目前无活跃热带系统</h2>
            <p>JTWC 当前未发现活跃的热带扰动或热带气旋</p>
        </div>'''

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>西太平洋热带扰动监控</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        .header h1 {{ font-size: 2rem; color: #1a1a2e; margin-bottom: 8px; }}
        .header .subtitle {{ color: #718096; font-size: 0.95rem; }}
        .stats-bar {{
            background: white;
            border-radius: 12px;
            padding: 15px 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
            font-size: 0.9rem;
            color: #555;
        }}
        .stat {{ display: flex; align-items: center; gap: 5px; }}
        .stat strong {{ color: #1a1a2e; }}
        .no-systems {{
            background: white;
            border-radius: 16px;
            padding: 60px 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .no-systems .icon {{ font-size: 4rem; margin-bottom: 20px; }}
        .no-systems h2 {{ font-size: 1.6rem; color: #48bb78; margin-bottom: 10px; }}
        .no-systems p {{ color: #718096; }}
        .storm-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            border-left: 6px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .storm-card:hover {{ transform: translateY(-3px); box-shadow: 0 14px 36px rgba(0,0,0,0.25); }}
        .storm-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .storm-id {{ font-size: 1.4rem; font-weight: bold; color: #1a1a2e; }}
        .badge-row {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: bold;
            color: white;
        }}
        .badge-tcfa {{ background: #cc0000; }}
        .storm-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }}
        .info-item {{ background: #f7fafc; border-radius: 8px; padding: 10px 14px; }}
        .info-label {{ font-size: 0.75rem; color: #999; margin-bottom: 3px; }}
        .info-value {{ font-size: 1rem; font-weight: 600; color: #2d3748; }}
        .tcfa-alert {{
            background: #fff5f5;
            border: 1px solid #fc8181;
            border-radius: 8px;
            padding: 10px 14px;
            margin-top: 14px;
            font-size: 0.9rem;
            color: #c53030;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: rgba(255,255,255,0.6);
            font-size: 0.85rem;
        }}
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 1.5rem; }}
            .storm-card {{ padding: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌀 西太平洋热带扰动监控</h1>
            <div class="subtitle">数据来源：JTWC（美国联合台风警报中心）via tropycal · 监控范围：西北太平洋（WP）</div>
        </div>
        <div class="stats-bar">
            <div class="stat">🕒 脚本运行：<strong>{now_str}</strong></div>
            <div class="stat">📡 JTWC报文：<strong>{jtwc_time_str}</strong></div>
            <div class="stat">🌀 活跃系统：<strong>{len(wp_systems)} 个</strong></div>
            <div class="stat">🔴 热带气旋：<strong>{active_count} 个</strong></div>
            <div class="stat">🔵 热带扰动：<strong>{invest_count} 个</strong></div>
            <div class="stat">⚠️ TCFA：<strong>{tcfa_count} 个</strong></div>
        </div>
        {no_systems_html}
        {cards_html}
        <div class="footer">
            数据来源：JTWC via tropycal | 仅供参考，请以官方发布为准
        </div>
    </div>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info(f"HTML 报告已生成: {output_path}")


def build_feishu_card(wp_systems, tcfas, report_url, jtwc_update_time=None):
    """构建飞书消息卡片"""
    tcfa_count = len(tcfas)
    invest_count = sum(1 for s in wp_systems.values()
                       if getattr(s, 'type', '').lower() == 'invest')
    active_count = len(wp_systems) - invest_count

    if not wp_systems:
        header_title = "✅ 西太平洋无活跃热带系统"
        header_template = "green"
    elif tcfa_count > 0:
        header_title = f"⚠️ 西太平洋热带扰动警报 — {tcfa_count} 个 TCFA"
        header_template = "red"
    else:
        header_title = f"🌀 西太平洋热带扰动监控 — {len(wp_systems)} 个活跃系统"
        header_template = "orange"

    jtwc_time_str = (jtwc_update_time.strftime('%Y-%m-%d %H:%M UTC')
                     if jtwc_update_time else '暂无')
    status_text = (
        f"**活跃系统：** {len(wp_systems)} 个\n"
        f"**热带气旋：** {active_count} 个\n"
        f"**热带扰动：** {invest_count} 个\n"
        f"**TCFA 警报：** {tcfa_count} 个\n"
        f"**📡 JTWC 报文时间：** {jtwc_time_str}"
    )

    elements = [{"tag": "div", "text": {"tag": "lark_md", "content": status_text}}]

    if wp_systems:
        elements.append({"tag": "hr"})
        for storm_id, storm in wp_systems.items():
            type_raw = getattr(storm, 'type', '') or ''
            lat = getattr(storm, 'lat', None)
            lon = getattr(storm, 'lon', None)
            wind = getattr(storm, 'wind', None)
            pressure = getattr(storm, 'pressure', None)
            has_tcfa = storm_id in tcfas

            type_label = get_storm_type_label(type_raw)
            lat_str = f"北纬{lat:.1f}°" if lat is not None else 'N/A'
            lon_str = f"东经{lon:.1f}°" if lon is not None else 'N/A'
            wind_str = f"{wind}节" if wind is not None else 'N/A'
            pres_str = f"{pressure}hPa" if pressure is not None else 'N/A'
            rpt_time = get_storm_report_time(storm)
            rpt_str = rpt_time.strftime('%m-%d %H:%MZ') if rpt_time else 'N/A'
            tcfa_tag = "【⚠️TCFA】" if has_tcfa else ""

            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**{storm_id}** {tcfa_tag}| {type_label}\n"
                        f"位置：{lat_str}, {lon_str} | 风速：{wind_str} | 气压：{pres_str} | 📡 报文：{rpt_str}"
                    )
                }
            })

    elements.append({"tag": "hr"})

    if report_url:
        elements.append({
            "tag": "action",
            "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📋 查看完整监控报告"},
                "type": "primary",
                "url": report_url
            }]
        })

    elements.append({
        "tag": "note",
        "elements": [{
            "tag": "plain_text",
            "content": (
                f"更新时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"
                " | 数据源：JTWC via tropycal"
            )
        }]
    })

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": header_title},
                "template": header_template
            },
            "elements": elements
        }
    }


def send_feishu_notification(webhook_url, wp_systems, tcfas, report_url, secret='', jtwc_update_time=None):
    """发送飞书通知"""
    if not webhook_url:
        logging.warning("未配置飞书 Webhook，跳过通知")
        return False

    try:
        card = build_feishu_card(wp_systems, tcfas, report_url, jtwc_update_time)

        if secret:
            timestamp, sign = gen_feishu_sign(secret)
            card['timestamp'] = timestamp
            card['sign'] = sign
            logging.info("已启用飞书签名校验")
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
    logging.info("=" * 50)
    logging.info("西太平洋热带扰动监控 — JTWC via tropycal")
    logging.info("=" * 50)

    feishu_webhook, feishu_secret, report_url = load_config()

    wp_systems, tcfas, jtwc_update_time = fetch_wp_disturbances()

    logging.info(f"西太平洋活跃系统: {len(wp_systems)} 个")
    for storm_id, storm in wp_systems.items():
        type_raw = getattr(storm, 'type', '')
        lat = getattr(storm, 'lat', None)
        lon = getattr(storm, 'lon', None)
        wind = getattr(storm, 'wind', None)
        tcfa_tag = '【TCFA】' if storm_id in tcfas else ''
        logging.info(
            f"  {storm_id}: {type_raw}, 位置({lat}, {lon}), 风速 {wind} 节 {tcfa_tag}"
        )

    logging.info("正在生成 HTML 报告...")
    render_html(wp_systems, tcfas, jtwc_update_time)

    logging.info("准备发送飞书通知...")
    send_feishu_notification(feishu_webhook, wp_systems, tcfas, report_url, feishu_secret, jtwc_update_time)

    logging.info("完成！")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"脚本异常退出: {e}", exc_info=True)
        # 即使出错也尝试生成一个空报告，保证 GitHub Pages 有内容
        try:
            render_html({}, {}, None)
        except Exception:
            pass
        raise
