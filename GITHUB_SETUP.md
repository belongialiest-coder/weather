# GitHub 部署完整指南

本指南将帮助您将气象预警机器人部署到 GitHub，实现自动化运行和公网访问。

## 📋 前置准备

- ✅ 已完成本地代码开发和测试
- ✅ 已初始化 Git 仓库（已完成）
- ✅ 拥有 GitHub 账号
- ✅ 已安装 Git 命令行工具

---

## 🚀 第一步：创建 GitHub 仓库

### 1.1 在 GitHub 上创建新仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - **Repository name**: `weather-alert-bot`（或其他名称）
   - **Description**: `气象预警自动化系统`
   - **Visibility**: Public（必须是 Public 才能使用 GitHub Pages）
3. **不要**勾选 "Initialize this repository with"（因为本地已有代码）
4. 点击 **Create repository**

### 1.2 记录仓库地址

创建后，GitHub 会显示类似这样的地址：
```
https://github.com/你的用户名/weather-alert-bot.git
```

---

## 📤 第二步：推送代码到 GitHub

在本地项目目录运行以下命令：

```bash
cd "d:\ai工作区\weather-alert-bot"

# 设置远程仓库地址（替换成你的仓库地址）
git remote add origin https://github.com/你的用户名/weather-alert-bot.git

# 推送代码
git branch -M main
git push -u origin main
```

推送成功后，刷新 GitHub 仓库页面，应该能看到所有文件。

---

## 🔐 第三步：配置 GitHub Secrets

Secrets 用于存储敏感信息（API 密钥、Webhook 地址等），不会暴露在代码中。

### 3.1 进入 Secrets 配置页面

1. 打开你的 GitHub 仓库
2. 点击 **Settings** 标签
3. 左侧菜单找到 **Secrets and variables** > **Actions**
4. 点击 **New repository secret**

### 3.2 添加 4 个 Secrets

按照以下格式逐个添加：

#### Secret 1: SENIVERSE_API_KEY
- **Name**: `SENIVERSE_API_KEY`
- **Value**: `Su0VVwkqCYBiQEOLH`
- 点击 **Add secret**

#### Secret 2: CITY
- **Name**: `CITY`
- **Value**: `beijing`（或其他城市名称）
- 点击 **Add secret**

#### Secret 3: FEISHU_WEBHOOK
- **Name**: `FEISHU_WEBHOOK`
- **Value**: `https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548`
- 点击 **Add secret**

#### Secret 4: REPORT_URL
- **Name**: `REPORT_URL`
- **Value**: `https://你的用户名.github.io/weather-alert-bot/`

  **重要**：将 `你的用户名` 替换为你的 GitHub 用户名，例如：
  - 如果用户名是 `zhangsan`
  - 则填写：`https://zhangsan.github.io/weather-alert-bot/`

### 3.3 验证 Secrets 配置

配置完成后，应该能看到 4 个 Secrets：
- ✅ SENIVERSE_API_KEY
- ✅ CITY
- ✅ FEISHU_WEBHOOK
- ✅ REPORT_URL

---

## 📄 第四步：启用 GitHub Pages

### 4.1 进入 Pages 配置页面

1. 仓库页面点击 **Settings**
2. 左侧菜单找到 **Pages**

### 4.2 配置 Pages

1. **Source** 选择: `GitHub Actions`
   - 如果看不到这个选项，说明还没有运行过 Actions，可以先手动触发一次
2. 保存配置

---

## ▶️ 第五步：手动触发第一次运行

### 5.1 进入 Actions 页面

1. 点击仓库顶部的 **Actions** 标签
2. 如果看到黄色提示 "Workflows aren't being run on this forked repository"
   - 点击 **I understand my workflows, go ahead and enable them**
3. 左侧选择 **Weather Alert Bot** workflow

### 5.2 手动触发 Workflow

1. 点击右侧的 **Run workflow** 按钮
2. 选择 branch: `main`
3. 点击绿色的 **Run workflow** 按钮

### 5.3 查看运行结果

1. 等待几秒，页面会出现一个新的 workflow run
2. 点击进入查看详情
3. 等待所有步骤完成（约 1-2 分钟）

**成功标志**：
- ✅ "check-weather" job 显示绿色对勾
- ✅ "deploy" job 显示绿色对勾
- ✅ 收到飞书通知消息

---

## 🌐 第六步：验证 GitHub Pages 部署

### 6.1 获取 Pages URL

1. 回到 **Settings** > **Pages**
2. 页面顶部会显示：
   ```
   Your site is live at https://你的用户名.github.io/weather-alert-bot/
   ```

### 6.2 访问报告页面

1. 点击上面的链接或直接在浏览器访问
2. 应该能看到气象预警报告页面
3. 包含：
   - ✅ 中国地图预警分布
   - ✅ 预警图例
   - ✅ 预警详情列表（如果有预警）
   - ✅ 响应式设计（支持手机访问）

### 6.3 验证飞书通知按钮

1. 在飞书群中找到刚才收到的通知卡片
2. 点击 **查看详细风险报告** 按钮
3. 应该能打开 GitHub Pages 上的报告页面

---

## ⏰ 第七步：验证定时任务

### 7.1 定时任务配置

项目配置了两个定时任务：
- **每天北京时间 8:00**（UTC 0:00）
- **每天北京时间 18:00**（UTC 10:00）

### 7.2 查看定时运行记录

1. 在 **Actions** 页面可以看到所有运行记录
2. 定时任务会自动触发，无需手动操作
3. 每次运行都会：
   - 获取最新预警数据
   - 生成 HTML 报告
   - 部署到 GitHub Pages
   - 发送飞书通知

---

## ✅ 验收清单

完成部署后，请确认以下所有项目：

### GitHub 配置
- [ ] 代码已推送到 GitHub
- [ ] 4 个 Secrets 配置正确
- [ ] GitHub Pages 已启用
- [ ] 仓库可见性为 Public

### Actions 运行
- [ ] 手动运行成功（绿色对勾）
- [ ] check-weather job 执行成功
- [ ] deploy job 执行成功
- [ ] 无错误日志

### 功能验证
- [ ] GitHub Pages 可以正常访问
- [ ] HTML 报告显示正常
- [ ] 中国地图可视化正常显示
- [ ] 飞书通知成功发送
- [ ] 飞书卡片按钮可以打开报告
- [ ] 无预警时也收到通知（绿色卡片）

---

## 🔧 常见问题排查

### 问题 1：推送代码失败

**错误信息**: `Permission denied (publickey)`

**解决方案**：
```bash
# 方案 1：使用 HTTPS 方式（推荐）
git remote set-url origin https://github.com/你的用户名/weather-alert-bot.git
git push -u origin main

# 推送时会要求输入用户名和密码（或 Personal Access Token）
```

**方案 2**：配置 SSH 密钥（参考 GitHub 官方文档）

---

### 问题 2：Actions 运行失败

**检查步骤**：
1. 点击失败的 workflow run
2. 查看具体哪个步骤失败
3. 展开失败步骤查看错误日志

**常见原因**：
- ❌ Secrets 配置错误或缺失
  - 解决：检查 Settings > Secrets 中是否有全部 4 个
- ❌ API Key 无效
  - 解决：确认使用的是私钥不是公钥
- ❌ 权限不足
  - 解决：Settings > Actions > General > Workflow permissions 选择 "Read and write permissions"

---

### 问题 3：GitHub Pages 访问 404

**检查步骤**：
1. Settings > Pages 确认 Source 是 "GitHub Actions"
2. Actions 中 deploy job 是否成功
3. 等待 1-2 分钟让 Pages 部署完成
4. 确认仓库是 Public 而不是 Private

**解决方案**：
- 手动重新触发 workflow
- 检查 deploy job 的日志输出

---

### 问题 4：飞书通知按钮无法打开

**原因**：REPORT_URL 配置错误

**检查**：
1. Settings > Secrets > REPORT_URL 的值
2. 确认格式：`https://你的用户名.github.io/weather-alert-bot/`
3. 确认用户名拼写正确
4. 确认结尾有斜杠 `/`

**解决方案**：
```bash
# 修改 Secret 中的 REPORT_URL
# 或者在本地 .env 中测试
REPORT_URL=https://正确的用户名.github.io/weather-alert-bot/
```

---

### 问题 5：昨晚 18:00 没有自动推送

**可能原因**：

1. **首次部署问题**
   - 定时任务需要等第一次成功运行后才会激活
   - 解决：手动触发一次成功后，定时任务会自动生效

2. **没有配置 Secrets**
   - 如果 Secrets 未配置，脚本会失败但不会发送通知
   - 解决：确保 4 个 Secrets 都已配置

3. **时区转换错误**
   - cron: '0 10 * * *' 对应北京时间 18:00
   - 解决：已经配置正确，无需修改

4. **GitHub Actions 延迟**
   - 免费账户的定时任务可能有 3-10 分钟延迟
   - 解决：这是正常现象，耐心等待

**验证方法**：
- 查看 Actions 页面的运行历史
- 筛选 "Schedule" 触发的运行记录
- 如果有运行记录但失败，查看错误日志

---

## 📞 获取帮助

如果遇到其他问题：

1. **查看 Actions 日志**
   - 大部分问题都能在日志中找到线索

2. **检查配置文件**
   - `.github/workflows/weather_alert.yml`
   - 确认 Secrets 名称拼写正确

3. **本地测试**
   ```bash
   cd "d:\ai工作区\weather-alert-bot"
   py weather_alert.py
   ```
   - 如果本地能运行，说明是 GitHub 配置问题

---

## 🎉 部署成功！

如果以上步骤都完成且验证通过，恭喜您成功部署了气象预警自动化系统！

系统现在会：
- ✅ 每天自动运行 2 次（8:00 和 18:00）
- ✅ 自动获取最新预警数据
- ✅ 自动生成美观的 HTML 报告
- ✅ 自动发送飞书通知（无论有无预警）
- ✅ 自动部署到 GitHub Pages 供公网访问

---

**文档版本**: v1.1
**更新日期**: 2026-03-06
**作者**: Claude Code (Sonnet 4.5)
