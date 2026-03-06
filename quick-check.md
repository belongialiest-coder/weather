# ⚡ 快速检查清单

代码已推送，Actions 应该正在运行！请按照以下链接检查：

---

## 🔗 快捷链接

### 1. 查看 Actions 运行状态
👉 https://github.com/belongialiest-coder/weather/actions

**期望结果**：
- ✅ 看到正在运行或已完成的 workflow
- ✅ "Weather Alert Bot" 显示绿色对勾
- ✅ 两个 jobs（check-weather 和 deploy）都成功

如果失败，点击进入查看错误日志。

---

### 2. 查看部署的网站
👉 https://belongialiest-coder.github.io/weather/

**期望结果**：
- ✅ 看到气象预警报告页面
- ✅ 中国地图可视化显示正常
- ✅ 显示"当前无气象预警"

如果看到 404，等待 1-2 分钟后刷新（首次部署需要时间）。

---

### 3. 检查飞书通知
打开飞书群，查看是否收到通知。

**期望结果**：
- ✅ 收到绿色卡片："✅ 天气状况正常"
- ✅ 显示北京监控区域
- ✅ 预警数量 0 条
- ✅ 有"查看详细风险报告"按钮

点击按钮测试是否能打开 GitHub Pages。

---

## ⚠️ 必须手动完成的步骤（3 个）

### 步骤 1：更新 REPORT_URL Secret

**为什么**：确保飞书按钮指向正确的 URL

**操作**：
1. 访问：https://github.com/belongialiest-coder/weather/settings/secrets/actions
2. 找到 `REPORT_URL`
3. 点击右侧 **Update** 按钮
4. 确认值为：`https://belongialiest-coder.github.io/weather/`
5. 点击 **Update secret**

---

### 步骤 2：启用 GitHub Pages

**为什么**：允许公网访问 HTML 报告

**操作**：
1. 访问：https://github.com/belongialiest-coder/weather/settings/pages
2. **Source** 选择：`GitHub Actions`
3. 保存

---

### 步骤 3：检查 Actions 权限（如果部署失败）

**如果 deploy job 失败，执行此步骤**：

**操作**：
1. 访问：https://github.com/belongialiest-coder/weather/settings/actions
2. 滚动到 **Workflow permissions**
3. 选择 `Read and write permissions`
4. 勾选 `Allow GitHub Actions to create and approve pull requests`
5. 点击 **Save**
6. 然后手动重新运行 Actions

---

## 📊 状态检查表

请完成后打勾：

- [ ] Actions 运行成功（绿色对勾）
- [ ] GitHub Pages 已启用
- [ ] REPORT_URL Secret 已更新
- [ ] 网站可以访问 (https://belongialiest-coder.github.io/weather/)
- [ ] 收到飞书通知
- [ ] 飞书按钮能打开网站

---

## 🆘 如果遇到问题

### 问题 1：Actions 运行失败

**查看错误日志**：
1. 点击失败的 workflow run
2. 展开红色的 ❌ 步骤
3. 查看错误信息

**常见错误**：
- `The API key is invalid` → 检查 SENIVERSE_API_KEY Secret
- `Permission denied` → 检查 Actions 权限设置
- `Failed to deploy` → 检查是否启用了 Pages

---

### 问题 2：网站 404

**原因**：Pages 未启用或部署未完成

**解决**：
1. 确认 Settings > Pages 中 Source 为 "GitHub Actions"
2. 等待 2-3 分钟
3. 刷新页面

---

### 问题 3：没收到飞书通知

**检查**：
1. Actions 中 check-weather job 是否成功
2. Secrets 中 FEISHU_WEBHOOK 是否正确
3. 查看 Actions 日志中是否有"飞书通知发送成功"

---

## ✅ 全部完成后

您的气象预警系统已经部署成功！系统会：

- ⏰ 每天 8:00 自动运行
- ⏰ 每天 18:00 自动运行
- 📊 自动生成 HTML 报告
- 📱 自动发送飞书通知（无论有无预警）
- 🌐 报告自动部署到 GitHub Pages

---

**创建时间**：2026-03-06
**仓库地址**：https://github.com/belongialiest-coder/weather
