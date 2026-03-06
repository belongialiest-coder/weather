# 气象预警脚本

一个基于 Python 的气象灾害预警脚本，使用心知天气 API 获取预警信息，生成美观的 HTML 报告，并通过飞书机器人发送预警通知。支持 GitHub Actions 自动化运行和 GitHub Pages 部署。

## ✨ 功能特点

- 🌦️ 调用心知天气气象灾害预警 API
- 🚨 自动提取异常天气数据（台风、暴雨、冰雹等预警）
- 🎨 使用 Jinja2 模板引擎渲染现代化 HTML 报告
- 🗺️ 中国地图可视化展示预警城市分布
- 🎯 用不同颜色区分预警等级（红色、橙色、黄色、蓝色）
- 📱 响应式设计，支持移动端查看
- 🤖 飞书机器人通知（无论有无预警都发送，确保系统正常运行）
- ⏰ GitHub Actions 定时任务（每天 8:00 和 18:00 自动运行）
- 🌐 自动部署到 GitHub Pages（可公网访问）
- 📊 详细的日志记录和错误处理

## 📁 项目结构

```
weather-alert-bot/
├── .github/
│   └── workflows/
│       └── weather_alert.yml   # GitHub Actions 工作流
├── weather_alert.py            # 主脚本
├── test_feishu.py             # 飞书通知测试脚本
├── 心知天气.py                 # 参考代码
├── template.html              # HTML 模板
├── requirements.txt           # 依赖库
├── .env                       # 配置文件（本地开发用，不提交）
├── .env.example              # 配置文件模板
├── .gitignore                # Git 忽略文件
├── index.html                # 生成的报告
├── weather_alert.log         # 日志文件
└── README.md                 # 使用说明
```

## 🚀 快速开始

### 方式一：本地运行

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/weather-alert-bot.git
cd weather-alert-bot
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
SENIVERSE_API_KEY=你的心知天气私钥
CITY=beijing
FEISHU_WEBHOOK=你的飞书机器人Webhook地址
REPORT_URL=https://your-username.github.io/weather-alert-bot/
```

#### 4. 运行脚本

```bash
python weather_alert.py
```

### 方式二：GitHub Actions 自动化部署

#### 1. Fork 本项目

点击右上角 Fork 按钮，将项目 fork 到你的 GitHub 账号。

#### 2. 配置 GitHub Secrets

在你的 GitHub 仓库中，进入 `Settings` > `Secrets and variables` > `Actions`，添加以下 Secrets：

- `SENIVERSE_API_KEY`: 心知天气私钥
- `CITY`: 监控城市（如 beijing）
- `FEISHU_WEBHOOK`: 飞书机器人 Webhook 地址
- `REPORT_URL`: GitHub Pages URL（如 `https://your-username.github.io/weather-alert-bot/`）

#### 3. 启用 GitHub Pages

1. 进入 `Settings` > `Pages`
2. **Source** 选择 `GitHub Actions`
3. 保存设置

#### 4. 启用 GitHub Actions

1. 进入 `Actions` 标签页
2. 如果看到提示，点击 `I understand my workflows, go ahead and enable them`
3. 工作流会在以下时间自动运行：
   - 每天北京时间 8:00
   - 每天北京时间 18:00
   - 代码推送到 main 分支时
   - 手动触发（Actions 页面点击 "Run workflow"）

#### 5. 查看运行结果

- 在 `Actions` 标签页查看工作流运行状态
- HTML 报告会自动部署到 GitHub Pages
- 有预警时会自动发送飞书通知

## 📋 获取 API Key 和 Webhook

### 心知天气 API Key

1. 访问 [心知天气官网](https://www.seniverse.com/)
2. 注册账号并登录
3. 在控制台获取**私钥**（Private Key）
4. 免费版有调用次数限制，注意配额

### 飞书机器人 Webhook

1. 打开飞书，进入要接收通知的群聊
2. 点击群设置 > 群机器人 > 添加机器人
3. 选择"自定义机器人"
4. 设置机器人名称和描述
5. 复制 Webhook 地址
6. 可选：设置安全配置（签名验证）

## 🎯 使用方法

### 本地运行

```bash
# 正常运行（查询实时预警）
python weather_alert.py

# 测试飞书通知（模拟预警数据）
python test_feishu.py
```

### 手动触发 GitHub Actions

1. 进入仓库的 `Actions` 标签页
2. 选择 `Weather Alert Bot` 工作流
3. 点击 `Run workflow` > `Run workflow`

## 🎨 预警等级颜色

| 等级 | 颜色 | 说明 |
|------|------|------|
| 红色 | 🔴 | 最高级别预警，危险性极高 |
| 橙色 | 🟠 | 严重级别预警，危险性高 |
| 黄色 | 🟡 | 较高级别预警，需注意 |
| 蓝色 | 🔵 | 一般级别预警，需留意 |

## 📱 飞书消息卡片示例

当检测到预警时，会发送类似这样的消息卡片：

```
⚠️ 区域异常天气预警
────────────────────
监控区域： 北京
预警数量： 2 条
────────────────────
🟠 暴雨 - 橙色
📍 城市：北京
🕒 发布时间：2026-03-05 17:53:46
────────────────────
🔵 大风 - 蓝色
📍 城市：北京
🕒 发布时间：2026-03-05 17:53:46
────────────────────
[查看详细风险报告] 按钮

更新时间：2026-03-05 17:53:46
```

## 🛠️ 高级配置

### 修改定时任务时间

编辑 `.github/workflows/weather_alert.yml`：

```yaml
schedule:
  - cron: '0 0 * * *'   # 每天 UTC 0:00 (北京时间 8:00)
  - cron: '0 10 * * *'  # 每天 UTC 10:00 (北京时间 18:00)
```

### 监控多个城市

修改 `.env` 中的 `CITY` 参数，或修改脚本支持多城市查询。

### 自定义 HTML 模板

编辑 `template.html` 文件，修改样式、布局等。

## 📦 依赖库

- `requests>=2.31.0`: HTTP 请求库
- `python-dotenv>=1.0.0`: 环境变量管理
- `Jinja2>=3.1.2`: 模板引擎

## ⚠️ 注意事项

1. **API 密钥安全**：
   - 本地开发：`.env` 文件不要提交到 Git
   - GitHub Actions：使用 Secrets 存储敏感信息

2. **API 调用限制**：
   - 心知天气免费版有调用次数限制
   - 建议合理设置定时任务频率

3. **GitHub Pages**：
   - 首次部署可能需要几分钟
   - 确保仓库设置中启用了 GitHub Pages

4. **时区转换**：
   - GitHub Actions 使用 UTC 时间
   - 北京时间 = UTC + 8 小时

## 🐛 常见问题

### API 请求失败

- 检查网络连接
- 确认 API Key 是否正确（使用私钥而非公钥）
- 检查是否超出调用频率限制

### 飞书通知未收到

- 检查 Webhook URL 是否正确
- 查看日志文件 `weather_alert.log`
- 运行测试脚本 `python test_feishu.py`

### GitHub Actions 失败

- 检查 Secrets 是否正确配置
- 查看 Actions 运行日志
- 确保 GitHub Pages 已启用

### 模板文件不存在

确保 `template.html` 文件与 `weather_alert.py` 在同一目录。

## 🔄 工作流程图

```
┌─────────────────┐
│  定时触发       │
│  (8:00, 18:00)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  运行 Python    │
│  脚本           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  调用心知天气   │
│  API            │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │ 有预警？ │
    └────┬────┘
         │
    ┌────┼────┐
    │ 是      │ 否
    ▼         ▼
┌────────┐ ┌────────┐
│ 发送   │ │ 跳过   │
│ 飞书   │ │ 通知   │
└────┬───┘ └────┬───┘
     │          │
     └────┬─────┘
          │
          ▼
   ┌─────────────┐
   │ 生成 HTML   │
   │ 报告        │
   └──────┬──────┘
          │
          ▼
   ┌─────────────┐
   │ 部署到      │
   │ GitHub Pages│
   └─────────────┘
```

## 📝 许可证

MIT License

## 👤 作者

Created with Claude Code

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请提交 [GitHub Issue](https://github.com/your-username/weather-alert-bot/issues)。
