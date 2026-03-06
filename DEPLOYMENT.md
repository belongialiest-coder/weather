# GitHub Actions 部署指南

本指南将帮助你在 5 分钟内完成气象预警系统的自动化部署。

## 📋 准备工作

在开始之前，确保你已经：

1. ✅ 拥有 GitHub 账号
2. ✅ 获取了心知天气 API 私钥
3. ✅ 创建了飞书机器人并获取 Webhook 地址

## 🚀 部署步骤

### 1. Fork 仓库

1. 访问项目 GitHub 页面
2. 点击右上角 **Fork** 按钮
3. 等待 Fork 完成

### 2. 配置 GitHub Secrets

进入你 Fork 的仓库，按照以下步骤操作：

1. 点击仓库顶部的 **Settings**（设置）
2. 在左侧菜单找到 **Secrets and variables** > **Actions**
3. 点击 **New repository secret** 按钮
4. 依次添加以下 4 个 Secrets：

#### Secret 1: SENIVERSE_API_KEY
- **Name**: `SENIVERSE_API_KEY`
- **Value**: 你的心知天气私钥（例如：`Su0VVwkqCYBiQEOLH`）

#### Secret 2: CITY
- **Name**: `CITY`
- **Value**: 要监控的城市（例如：`beijing`）

#### Secret 3: FEISHU_WEBHOOK
- **Name**: `FEISHU_WEBHOOK`
- **Value**: 飞书机器人 Webhook 完整 URL
  ```
  https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
  ```

#### Secret 4: REPORT_URL
- **Name**: `REPORT_URL`
- **Value**: GitHub Pages URL
  ```
  https://你的用户名.github.io/weather-alert-bot/
  ```
  注意：将 `你的用户名` 替换为你的 GitHub 用户名

### 3. 启用 GitHub Pages

1. 在仓库设置页面，点击左侧 **Pages**
2. 在 **Source** 下拉菜单中，选择 **GitHub Actions**
3. 点击 **Save**（保存）

### 4. 启用 GitHub Actions

1. 点击仓库顶部的 **Actions** 标签
2. 如果看到提示信息，点击 **I understand my workflows, go ahead and enable them**
3. 完成！

### 5. 手动触发第一次运行（可选）

为了测试配置是否正确，建议手动触发一次：

1. 在 **Actions** 页面，点击左侧的 **Weather Alert Bot**
2. 点击右上角的 **Run workflow** 按钮
3. 选择分支（通常是 `main`），点击 **Run workflow**
4. 等待几分钟，查看运行结果

### 6. 查看运行结果

运行完成后：

1. ✅ **GitHub Pages**: 访问 `https://你的用户名.github.io/weather-alert-bot/` 查看 HTML 报告
2. ✅ **飞书通知**: 如果有预警，飞书群会收到通知
3. ✅ **运行日志**: 在 Actions 页面查看详细日志

## ⏰ 自动运行时间

配置完成后，工作流会在以下时间自动运行：

- 🌅 **每天早上 8:00**（北京时间）
- 🌆 **每天下午 18:00**（北京时间）
- 🔄 **代码推送到 main 分支时**
- 👆 **手动触发**

## 🔧 修改定时任务

如果想修改运行时间，编辑 `.github/workflows/weather_alert.yml` 文件：

```yaml
schedule:
  - cron: '0 0 * * *'   # UTC 0:00 = 北京时间 8:00
  - cron: '0 10 * * *'  # UTC 10:00 = 北京时间 18:00
```

**时区转换公式**：北京时间 - 8 小时 = UTC 时间

例如：
- 北京时间 9:00 → UTC 1:00 → cron: `'0 1 * * *'`
- 北京时间 12:00 → UTC 4:00 → cron: `'0 4 * * *'`
- 北京时间 20:00 → UTC 12:00 → cron: `'0 12 * * *'`

## 🎯 Cron 表达式说明

```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期几 (0-6, 0=周日)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)
```

常用示例：
- `'0 */6 * * *'` - 每 6 小时运行一次
- `'0 8,18 * * *'` - 每天 8:00 和 18:00 运行
- `'0 0 * * 1'` - 每周一 0:00 运行
- `'30 8 * * 1-5'` - 工作日 8:30 运行

## 🐛 故障排查

### Secrets 配置错误

**症状**：Actions 运行失败，日志显示 API Key 无效或 Webhook 错误

**解决方法**：
1. 检查 Secrets 名称是否正确（大小写敏感）
2. 检查 Secrets 值是否包含多余的空格
3. 重新添加 Secrets

### GitHub Pages 404 错误

**症状**：访问 GitHub Pages URL 显示 404

**解决方法**：
1. 确认已在设置中启用 GitHub Pages
2. 等待几分钟（首次部署需要时间）
3. 检查 Actions 是否运行成功
4. 确认 Source 设置为 "GitHub Actions"

### 定时任务不运行

**症状**：到了设定时间，工作流没有自动触发

**解决方法**：
1. 确认 Actions 已启用
2. GitHub Actions 的定时任务可能有延迟（5-10 分钟）
3. 手动触发测试是否能正常运行
4. 检查仓库是否有近期活动（长期无活动的仓库定时任务可能被禁用）

### 飞书通知未收到

**症状**：Actions 运行成功，但飞书没有收到通知

**解决方法**：
1. 检查当前是否真的有预警（可能是无预警状态）
2. 查看 Actions 运行日志，确认是否发送了通知
3. 检查 Webhook URL 是否正确
4. 在本地运行 `python test_feishu.py` 测试飞书连接

## 📊 监控与维护

### 查看运行历史

1. 进入 **Actions** 标签
2. 查看所有运行记录
3. 点击具体运行查看详细日志

### 查看部署的网页

访问：`https://你的用户名.github.io/weather-alert-bot/`

### 接收失败通知

GitHub 会在工作流失败时发送邮件通知到你的注册邮箱。

## 🎉 完成！

现在你的气象预警系统已经：

- ✅ 每天自动运行两次
- ✅ 自动部署 HTML 报告到 GitHub Pages
- ✅ 有预警时自动发送飞书通知
- ✅ 全程自动化，无需手动干预

## 📞 需要帮助？

如果遇到问题，可以：

1. 查看 README.md 的"常见问题"部分
2. 查看 Actions 运行日志
3. 提交 [GitHub Issue](https://github.com/your-username/weather-alert-bot/issues)

祝使用愉快！🚀
