# 心知天气 → 和风天气 API 迁移方案（已完成）

**迁移日期**: 2026-04-22
**数据源切换**: 心知天气 API → 和风天气 API
**状态**: ✅ 代码改动完成

---

## 📋 改动概览

### 改动统计

| 类别 | 文件 | 改动类型 | 详情 |
|------|-----|--------|------|
| **核心代码** | `weather_alert.py` | 修改 | 4个主要函数适配 |
| **新增文件** | `qweather_city_codes.py` | 新增 | 139个城市编码映射表 |
| **配置文件** | `.env.example` | 修改 | API Key参数名更新 |
| **配置文件** | `.env` | 修改 | 使用新的和风API Key和飞书信息 |
| **自动化流程** | `.github/workflows/weather_alert.yml` | 修改 | Secrets变量名更新 |

---

## 🔄 API 迁移详情

### 1️⃣ 导入新模块

```python
# 新增导入
from qweather_city_codes import get_city_code
```

### 2️⃣ 城市编码映射 - `qweather_city_codes.py`

**新增文件**，包含：
- ✅ 139个中文城市名 → 和风天气城市代码的映射表
- ✅ `get_city_code(city_name)` 函数：城市名→代码转换
- ✅ `get_city_name(city_code)` 函数：代码→城市名反向查询

**示例数据**：
```python
CITY_CODE_MAP = {
    '北京': '101010100',
    '上海': '101020100',
    '深圳': '440300',
    # ... 共139个城市
}
```

### 3️⃣ API 调用函数更新 - `get_weather_alarms()`

**改动前（心知天气）**：
```python
url = 'https://api.seniverse.com/v3/weather/alarm.json'
params = {
    'key': api_key,
    'location': city,           # 英文城市名
    'language': 'zh-Hans',
    'detail': 'more'
}
```

**改动后（和风天气）**：
```python
url = 'https://api.qweather.com/v1/warning/now'
city_code = get_city_code(city)  # 转换为城市代码
params = {
    'location': city_code,      # 城市代码（如 101010100）
    'key': api_key,
    'lang': 'zh'
}
```

**新增功能**：
- 自动将中文城市名转换为和风天气城市代码
- 改进的错误码处理（使用 `code` 字段而非 `status_code`）

### 4️⃣ 数据提取函数更新 - `extract_alarms()`

**改动前（心知天气数据结构）**：
```python
results = data.get('results', [])
location = results[0].get('location', {})
alarms = results[0].get('alarms', [])
```

**改动后（和风天气数据结构）**：
```python
alarms = data.get('warning', [])           # 直接从顶级字段获取
location = {
    'id': data.get('id', ''),
    'name': data.get('name', ''),
    'adm1': data.get('adm1', ''),          # 省份
    'adm2': data.get('adm2', ''),          # 城市
    # ...
}
```

### 5️⃣ 预警去重函数更新 - `deduplicate_alarms_by_type()`

**改动前**：
```python
pub_date = alarm.get('pub_date', '')           # 心知字段
alarm_level = alarm.get('level', '未知')
```

**改动后**：
```python
pub_time = alarm.get('pubTime', '')             # 和风字段
alarm_level = alarm.get('severity', '未知')     # 和风使用 severity
```

### 6️⃣ 飞书卡片构建 - `build_feishu_card()`

**预警等级映射更新**：

| 心知天气 | 和风天气 | emoji |
|--------|--------|-------|
| 红色 | 极端 | 🔴 |
| 橙色 | 严重 | 🟠 |
| 黄色 | 较重 | 🟡 |
| 蓝色 | 轻微 | 🔵 |

```python
# 更新后的emoji映射
level_emoji = {
    '极端': '🔴',
    '严重': '🟠',
    '较重': '🟡',
    '轻微': '🔵',
}

# 从 level 改为 severity
alarm_severity = alarm.get('severity', '未知')
```

**底部备注更新**：
- 旧: `数据源：心知天气`
- 新: `数据源：和风天气`

### 7️⃣ 配置文件更新

#### `.env.example`
```ini
# 改动前
SENIVERSE_API_KEY=your_private_key_here

# 改动后
QWEATHER_API_KEY=your_api_key_here
```

#### `.env` (本地配置)
```ini
# 改动前
SENIVERSE_API_KEY=SwNhoysR6G_Ta8bAg
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/715324a8-69a1-47a3-80c0-3616de17b279
FEISHU_SECRET=Ec2a0EgUEC7q9YGEhLnzHd

# 改动后
QWEATHER_API_KEY=5afec64e1bd54a4d8a9c8443694289ff
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548
FEISHU_SECRET=fJMgCkWIQVbQlt5C994KSe
```

#### `.github/workflows/weather_alert.yml`
```yaml
# 改动前
echo "SENIVERSE_API_KEY=${{ secrets.SENIVERSE_API_KEY }}" >> .env

# 改动后
echo "QWEATHER_API_KEY=${{ secrets.QWEATHER_API_KEY }}" >> .env
```

---

## ✨ 新增/改进功能

### ✅ 优势

1. **城市编码自动转换**
   - 用户输入中文城市名（如"北京"）
   - 自动查表转换为和风天气代码
   - 无需手动处理城市编码

2. **改进的字段映射**
   - `pubTime` 替代 `pub_date`（更清晰）
   - `severity` 替代 `level`（更规范）
   - `warning` 替代 `alarms`（更符合天气术语）

3. **增强的错误处理**
   - 识别和风天气的错误码格式
   - 更准确的错误消息

4. **数据结构简化**
   - 直接访问顶级字段
   - 无需多级嵌套查询
   - 减少解析错误

---

## 🧪 测试检查清单

### 本地测试
- [ ] ✅ Python 语法检查：`python -m py_compile weather_alert.py` ✓
- [ ] ✅ 城市编码映射测试：`python qweather_city_codes.py` ✓
- [ ] 本地运行完整流程：`python weather_alert.py`
- [ ] 验证飞书通知发送
- [ ] 检查生成的 HTML 报告

### GitHub 部署前需要

1. **更新 GitHub Secrets**
   ```
   旧 Secret（需删除）:
   - SENIVERSE_API_KEY

   新 Secret（需添加）:
   - QWEATHER_API_KEY=5afec64e1bd54a4d8a9c8443694289ff

   现有 Secret（需更新）:
   - FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548
   - FEISHU_SECRET=fJMgCkWIQVbQlt5C994KSe
   ```

2. **在 GitHub 仓库中操作**
   - 进入 `Settings` → `Secrets and variables` → `Actions`
   - 删除旧的 `SENIVERSE_API_KEY`
   - 添加新的 `QWEATHER_API_KEY`
   - 验证其他 Secrets 正确

3. **测试 GitHub Actions**
   - 进入 `Actions` 标签页
   - 手动触发一次工作流 (`Run workflow`)
   - 检查执行日志

---

## 📊 对比总结

### API 端点对比

| 属性 | 心知天气 | 和风天气 |
|------|--------|--------|
| **基础 URL** | `api.seniverse.com/v3/weather/alarm.json` | `api.qweather.com/v1/warning/now` |
| **城市参数** | 英文名/中文名 | 城市代码 |
| **语言参数** | `language=zh-Hans` | `lang=zh` |
| **额外参数** | `detail=more` | ❌ 无需 |
| **认证** | URL 参数 `key` | URL 参数 `key` |

### 数据字段对比

| 功能 | 心知天气 | 和风天气 |
|------|--------|--------|
| **预警数组** | `results[0].alarms` | `warning` |
| **预警类型** | `type` | `type` ✅ 相同 |
| **预警等级** | `level` (红/橙/黄/蓝/白) | `severity` (极端/严重/较重/轻微) |
| **发布时间** | `pub_date` | `pubTime` |
| **预警标题** | `title` | `title` ✅ 相同 |

---

## 🚀 下一步操作

### 立即执行
1. ✅ 提交代码变更到 Git
2. ✅ 在 GitHub 更新 Secrets
3. ✅ 手动测试 GitHub Actions 工作流
4. ✅ 验证飞书通知是否正常发送

### 监控与反馈
- 监控前 5 次运行（手动触发）
- 检查日志中的错误信息
- 验证预警数据准确性

---

## 📝 改动文件清单

```
weather-alert-bot/
├── weather_alert.py              ⚙️ 修改（4个函数适配）
├── qweather_city_codes.py        ✨ 新增（139城市编码映射）
├── .env                          🔑 修改（API Key + 飞书信息）
├── .env.example                  📖 修改（API Key 参数名）
├── .github/workflows/weather_alert.yml  🔄 修改（Secrets 变量名）
└── MIGRATION_PLAN.md             📋 本文档
```

---

**迁移完成时间**: 2026-04-22 ✅
**代码质量**: 语法检查通过 ✓
**准备就绪**: 等待 GitHub Secrets 更新与测试
