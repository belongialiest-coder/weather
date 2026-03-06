import requests
import time
import random
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='weather_alarm.log'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

# 飞书机器人Webhook地址
FEISHU_HOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548"

# 预警级别优先级
ALARM_LEVEL_PRIORITY = {
    "红色": 4, "橙色": 3, "黄色": 2, "蓝色": 1, "未知": 0
}

# 物流相关预警类型
RELEVANT_ALARM_TYPES = [
    "暴雨", "台风", "大风", "雷电", "冰雹",
    "大雾", "道路结冰", "雪灾", "寒潮", "霜冻"
]

# API频率控制配置
API_CONFIG = {
    "base_url": "https://api.seniverse.com/v3/weather/alarm.json",
    "max_retries": 5,
    "initial_delay": 2,
    "max_delay": 30,
    "batch_size": 10,
    "batch_delay": 10,
    "request_delay": 1,
    "random_jitter": 0.5
}


# 自定义异常类
class InvalidKeyError(Exception):
    pass


class WeatherAlarmChecker:
    def __init__(self, private_key: str):
        self.private_key = private_key
        self.retry_delay = API_CONFIG["initial_delay"]
        self.failed_cities = []
        self.processed_alarm_ids = set()  # 用于去重

        # 区域划分（城市名 -> 所属大区），确保与实际城市名完全匹配
        self.REGION_MAP = {
            "东北": ["大连市", "沈阳市", "长春市", "哈尔滨市", "吉林市", "鞍山市", "大庆市", "赤峰市"],
            "华北": ["北京市", "天津市", "石家庄市", "太原市", "呼和浩特市", "保定市", "邯郸市", "唐山市", "沧州市",
                     "邢台市"],
            "华南": ["广州市", "深圳市", "南宁市", "海口市", "东莞市", "佛山市", "惠州市", "中山市", "汕头市", "湛江市",
                     "三亚市"],
            "西南": ["成都市", "重庆市", "贵阳市", "昆明市", "拉萨市", "乐山市", "绵阳市", "南充市", "遵义市", "大理市",
                     "自贡市"],
            "西北": ["西安市", "兰州市", "西宁市", "银川市", "乌鲁木齐市", "榆林市", "延安市", "咸阳市",
                     "伊犁哈萨克自治州"],
            "华东": ["上海市", "杭州市", "南京市", "济南市", "合肥市", "福州市", "南昌市", "青岛市", "厦门市", "宁波市",
                     "苏州市", "无锡市", "温州市", "台州市", "常州市", "徐州市", "南通市", "嘉兴市", "金华市", "泉州市",
                     "临沂市", "济宁市", "淄博市", "菏泽市", "淮安市", "宿迁市", "芜湖市", "蚌埠市", "阜阳市", "六安市",
                     "滁州市"],
            "华中": ["武汉市", "郑州市", "长沙市", "合肥市", "南昌市", "洛阳市", "新乡市", "许昌市", "开封市", "衡阳市",
                     "岳阳市", "荆州市", "襄阳市", "信阳市", "南阳市", "宜昌市", "株洲市", "湘潭市", "娄底市"]
        }

        # 港口所在精细监控区及名称映射
        self.PORT_AREAS = {
            "大连市": "210213",
            "天津市": "120116",
            "上海市": "310115",
            "广州市": "440115",
            "湛江市": "440825",
            "海口市": "460105",
        }
        self.PORT_NAMES = {
            "大连市": "大连大窑港",
            "天津市": "天津港",
            "上海市": "上海芦潮港",
            "广州市": "广州南沙港",
            "湛江市": "湛江徐闻港",
            "海口市": "海口秀英港",
        }

        # 基础监控城市（完整列表）
        self.BASE_CITIES = {
            "北京市": "110000",
            "蚌埠市": "340300",
            "东莞市": "441900",
            "佛山市": "440600",
            "广州市": "440100",
            "常德市": "430700",
            "常州市": "320400",
            "成都市": "510100",
            "惠州市": "441300",
            "汕头市": "440500",
            "深圳市": "440300",
            "湛江市": "440800",
            "中山市": "442000",
            "福州市": "350100",
            "阜阳市": "341200",
            "赣州市": "360700",
            "珠海市": "440400",
            "贵阳市": "520100",
            "江门市": "440700",
            "柳州市": "450200",
            "南宁市": "450100",
            "杭州市": "330100",
            "合肥市": "340100",
            "衡阳市": "430400",
            "桂林市": "450300",
            "湖州市": "330500",
            "淮安市": "320800",
            "海口市": "460100",
            "济南市": "370100",
            "济宁市": "370800",
            "嘉兴市": "330400",
            "金华市": "330700",
            "昆明市": "530100",
            "兰州市": "620100",
            "乐山市": "511100",
            "连云港市": "320700",
            "临沂市": "371300",
            "三亚市": "460200",
            "龙岩市": "350800",
            "洛阳市": "410300",
            "绵阳市": "510700",
            "南昌市": "360100",
            "南充市": "511300",
            "南京市": "320100",
            "保定市": "130600",
            "南通市": "320600",
            "宁波市": "330200",
            "邯郸市": "130400",
            "青岛市": "370200",
            "泉州市": "350500",
            "秦皇岛市": "130300",
            "厦门市": "350200",
            "石家庄市": "130100",
            "上海市": "310000",
            "绍兴市": "330600",
            "唐山市": "130200",
            "沧州市": "130900",
            "大庆市": "230600",
            "苏州市": "320500",
            "台州市": "331000",
            "哈尔滨市": "230100",
            "长春市": "220100",
            "吉林市": "220200",
            "潍坊市": "370700",
            "温州市": "330300",
            "乌鲁木齐市": "650100",
            "无锡市": "320200",
            "芜湖市": "340200",
            "武汉市": "420100",
            "西安市": "610100",
            "西宁市": "630100",
            "襄阳市": "420600",
            "新乡市": "410700",
            "徐州市": "320300",
            "烟台市": "370600",
            "扬州市": "321000",
            "银川市": "640100",
            "榆林市": "610800",
            "鞍山市": "210300",
            "大连市": "210200",
            "长沙市": "430100",
            "郑州市": "410100",
            "沈阳市": "210100",
            "重庆市": "500000",
            "包头市": "150200",
            "淄博市": "370300",
            "遵义市": "520300",
            "拉萨市": "540100",
            "菏泽市": "371700",
            "鄂尔多斯市": "150600",
            "商丘市": "411400",
            "漳州市": "350600",
            "荆州市": "421000",
            "亳州市": "341600",
            "呼和浩特市": "150100",
            "信阳市": "411500",
            "许昌市": "411000",
            "达州市": "511700",
            "宿迁市": "321300",
            "岳阳市": "430600",
            "赤峰市": "150400",
            "渭南市": "610500",
            "大理白族自治州": "532900",
            "宜昌市": "420500",
            "太原市": "140100",
            "延安市": "610600",
            "大同市": "140200",
            "自贡市": "510300",
            "六安市": "341500",
            "滁州市": "341100",
            "长治市": "140400",
            "运城市": "140800",
            "南阳市": "411300",
            "伊犁哈萨克自治州": "654000",
            "天津市": "120000",
            "恩施土家族苗族自治州": "422800",
            "咸阳市": "610400",
            "开封市": "410200",
            "驻马店市": "411700",
        }

        # 合并城市配置
        self.CITY_CONFIG = {**self.BASE_CITIES, **self.PORT_AREAS}

    def get_alarm_data(self, adcode: str, city_name: str) -> Optional[Dict[str, Any]]:
        """获取预警数据，包含重试机制"""
        params = {
            "key": self.private_key,
            "location": city_name,
            "detail": "more"
        }

        for attempt in range(API_CONFIG["max_retries"]):
            try:
                jitter = random.uniform(-API_CONFIG["random_jitter"], API_CONFIG["random_jitter"])
                delay = API_CONFIG["request_delay"] + max(0, jitter)
                time.sleep(delay)

                response = requests.get(API_CONFIG["base_url"], params=params, timeout=10)
                response.raise_for_status()

                self.retry_delay = API_CONFIG["initial_delay"]
                return response.json()

            except requests.exceptions.HTTPError as e:
                if response.status_code == 403:
                    if "Invalid private key" in response.text:
                        raise InvalidKeyError("API密钥无效，请检查并替换")
                    elif "Rate limit exceeded" in response.text:
                        self._handle_rate_limit()
                else:
                    logging.error(f"HTTP错误 {response.status_code}: {e}")
                    time.sleep(API_CONFIG["request_delay"])
            except Exception as e:
                logging.error(f"获取数据失败: {e}")
                time.sleep(API_CONFIG["request_delay"])

        logging.error(f"城市 {city_name} 达到最大重试次数")
        self.failed_cities.append((adcode, city_name))
        return None

    def _handle_rate_limit(self):
        """处理API限流"""
        self.retry_delay = min(self.retry_delay * 2, API_CONFIG["max_delay"])
        logging.warning(f"检测到API限流，等待 {self.retry_delay} 秒后重试")
        time.sleep(self.retry_delay)

    def parse_alarm_data(self, alarm_data: Dict[str, Any], city_name: str, is_port: bool) -> List[Dict[str, Any]]:
        """解析预警数据，标记港口区域并去重"""
        alarms = []
        if "results" in alarm_data and len(alarm_data["results"]) > 0:
            for result in alarm_data["results"]:
                location = result.get("location", {})
                adcode = location.get("adcode", "未知编码")
                display_name = location.get("display_name", location.get("name", "未知地区"))

                # 处理港口名称映射
                if is_port and city_name in self.PORT_NAMES:
                    display_name = self.PORT_NAMES[city_name]

                for alarm in result.get("alarms", []):
                    # 生成唯一标识用于去重
                    alarm_id = f"{display_name}_{alarm.get('type', '未知')}_{alarm.get('level', '未知')}_{alarm.get('title', '')}"
                    if alarm_id in self.processed_alarm_ids:
                        continue

                    self.processed_alarm_ids.add(alarm_id)
                    alarms.append({
                        "display_name": display_name,
                        "type": alarm.get("type", "未知"),
                        "level": alarm.get("level", "未知"),
                        "title": alarm.get("title", "无标题"),
                        "region": self._get_region(display_name)
                    })
        return alarms

    def _get_region(self, city_name: str) -> str:
        """获取城市所属区域"""
        for region, cities in self.REGION_MAP.items():
            if city_name in cities or (city_name.endswith("港") and city_name.replace("港", "市") in cities):
                return region
        return "其他"

    def filter_relevant_alarms(self, alarms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤物流相关预警"""
        return [a for a in alarms if a["type"] in RELEVANT_ALARM_TYPES]

    def check_multiple_areas(self, city_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """分批检查多个区域的预警"""
        all_alarms = []
        city_batches = [list(city_config.items())[i:i + API_CONFIG["batch_size"]]
                        for i in range(0, len(city_config), API_CONFIG["batch_size"])]

        for batch in city_batches:
            for city_name, adcode in batch:
                is_port = adcode in self.PORT_AREAS.values()
                try:
                    alarm_data = self.get_alarm_data(adcode, city_name)
                    if alarm_data:
                        parsed_alarms = self.parse_alarm_data(alarm_data, city_name, is_port)
                        all_alarms.extend(self.filter_relevant_alarms(parsed_alarms))
                except InvalidKeyError:
                    logging.critical("API密钥无效，终止程序")
                    raise
                except Exception as e:
                    logging.error(f"处理城市 {city_name} 时出错: {e}")

            if batch != city_batches[-1]:
                time.sleep(API_CONFIG["batch_delay"])

        logging.info(f"共发现 {len(all_alarms)} 条相关预警")
        return all_alarms

    def classify_alarms_by_region(self, alarms: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """按区域和预警类型分类"""
        region_alarms = {region: {} for region in self.REGION_MAP.keys()}
        region_alarms["其他"] = {}

        for alarm in alarms:
            region = alarm["region"]
            alarm_type = alarm["type"]

            if region not in region_alarms:
                region_alarms["其他"][alarm_type] = region_alarms["其他"].get(alarm_type, []) + [alarm]
                continue

            if alarm_type not in region_alarms[region]:
                region_alarms[region][alarm_type] = []
            region_alarms[region][alarm_type].append(alarm)

        # 移除空区域
        return {region: alarms for region, alarms in region_alarms.items() if alarms}

    def generate_feishu_message(self, classified_alarms: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> List[
        Dict[str, Any]]:
        """生成飞书消息，按区域和预警类型排列"""
        messages = []
        type_order = ["暴雨", "台风", "大风", "雷电", "大雾", "道路结冰", "雪灾", "寒潮", "霜冻"]

        for region, type_alarms in classified_alarms.items():
            if not type_alarms:
                continue

            message_content = [
                [{"tag": "text", "text": f"### {region}\n\n"}]
            ]

            # 按预设顺序排列预警类型
            for alarm_type in type_order:
                if alarm_type not in type_alarms:
                    continue

                # 按级别排序并去重
                sorted_alarms = sorted(
                    type_alarms[alarm_type],
                    key=lambda x: ALARM_LEVEL_PRIORITY.get(x["level"], 0),
                    reverse=True
                )

                # 去重处理
                unique_alarms = []
                seen = set()
                for alarm in sorted_alarms:
                    # 使用城市名和级别作为唯一标识
                    alarm_id = f"{alarm['display_name']}_{alarm['level']}"
                    if alarm_id not in seen:
                        seen.add(alarm_id)
                        unique_alarms.append(alarm)

                if not unique_alarms:
                    continue

                # 添加预警类型标题
                message_content.append([{"tag": "text", "text": f"{alarm_type}：\n"}])

                # 添加每个预警
                for alarm in unique_alarms:
                    level_emoji = {
                        "红色": "🔴", "橙色": "🟠", "黄色": "🟡", "蓝色": "🔵", "未知": "⚪"
                    }.get(alarm["level"], "⚪")
                    message_content.append([
                        {"tag": "text", "text": f"  {alarm['display_name']}（{level_emoji} {alarm['level']}）\n"}
                    ])

                # 类型间添加分隔
                message_content.append([{"tag": "text", "text": "\n"}])

            # 构建完整消息
            message = {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": f"🚚 物流气象预警 - {region}地区",
                            "content": message_content
                        }
                    }
                }
            }
            messages.append(message)

        return messages

    def send_to_feishu(self, messages: List[Dict[str, Any]]) -> None:
        """发送消息到飞书，支持分段发送"""
        for msg in messages:
            try:
                response = requests.post(FEISHU_HOOK_URL, json=msg)
                response.raise_for_status()
                logging.info("飞书消息发送成功")
            except Exception as e:
                logging.error(f"飞书消息发送失败: {e}")

    def run(self) -> None:
        """运行完整流程"""
        try:
            logging.info("===== 开始物流气象预警检查 =====")
            alarms = self.check_multiple_areas(self.CITY_CONFIG)
            if not alarms:
                logging.info("未发现相关预警")
                return

            classified = self.classify_alarms_by_region(alarms)
            messages = self.generate_feishu_message(classified)
            self.send_to_feishu(messages)

            if self.failed_cities:
                logging.warning(f"以下 {len(self.failed_cities)} 个城市查询失败:")
                for adcode, city in self.failed_cities:
                    logging.warning(f"  - {city} (编码: {adcode})")

        except InvalidKeyError as e:
            logging.critical(f"程序终止: {e}")
        except Exception as e:
            logging.critical(f"发生未知错误: {e}", exc_info=True)


if __name__ == "__main__":
    # 替换为你的API密钥
    private_key = "Su0VVwkqCYBiQEOLH"
    checker = WeatherAlarmChecker(private_key)
    checker.run()