# 更新 GitHub Secrets 配置

## 问题原因
GitHub Pages 显示旧内容的原因：GitHub Actions 运行时使用的是 **GitHub Secrets** 中存储的配置，而不是本地的 `.env` 文件。虽然本地代码已更新为139城市，但 GitHub Secrets 中还是旧的单城市配置。

## 解决步骤

### 1. 打开 GitHub 仓库设置
1. 访问：https://github.com/belongialiest-coder/weather/settings/secrets/actions
2. 或者：进入仓库 → Settings → Secrets and variables → Actions

### 2. 更新以下 Secrets

需要更新/添加这5个 Secrets：

#### ✅ SENIVERSE_API_KEY
- 值：`Su0VVwkqCYBiQEOLH`
- 说明：心知天气 API 密钥

#### ✅ CITY（最重要！）
- 值：
```
鞍山,蚌埠,包头,保定,北京,常德,常州,成都,大连,大庆,东莞,鄂尔多斯,佛山,福州,阜阳,赣州,广州,贵阳,哈尔滨,海口,邯郸,杭州,合肥,衡阳,呼和浩特,湖州,淮安,惠州,济南,济宁,嘉兴,金华,昆明,兰州,乐山,连云港,临沂,柳州,龙岩,洛阳,绵阳,南昌,南充,南京,南宁,南通,宁波,秦皇岛,青岛,泉州,三亚,厦门,汕头,上海,绍兴,深圳,沈阳,石家庄,苏州,台州,太原,唐山,天津,潍坊,温州,乌鲁木齐,无锡,芜湖,武汉,西安,西宁,襄阳,新乡,徐州,烟台,扬州,银川,榆林,湛江,长春,长沙,郑州,中山,重庆,珠海,淄博,遵义,拉萨,菏泽,沧州,商丘,漳州,荆州,亳州,江门,信阳,许昌,达州,宿迁,岳阳,吉林,宜昌,渭南,大理,自贡,延安,大同,六安,桂林,滁州,赤峰,长治,南阳,伊犁,运城,恩施,邢台,咸阳,开封,驻马店,周口,宝鸡,德州,通辽,滨州,平顶山,郴州,廊坊,泰安,衢州,曲靖,枣庄,日照,丽水,承德,东营,齐齐哈尔,聊城,临汾
```
- 说明：139个监控城市，用逗号分隔（**注意：复制时不要有换行！**）

#### ✅ ALERT_TYPES（新增！）
- 值：`台风,雪,寒潮,冰雹,大雾`
- 说明：只监控影响物流的5种天气类型

#### ✅ FEISHU_WEBHOOK
- 值：`https://open.feishu.cn/open-apis/bot/v2/hook/02b6ea77-283f-4e99-b035-915fbbe3a548`
- 说明：飞书机器人 Webhook 地址

#### ✅ REPORT_URL
- 值：`https://belongialiest-coder.github.io/weather/`
- 说明：GitHub Pages 报告地址

### 3. 如何更新 Secret

对于每个 Secret：
1. 如果已存在：点击右侧 **铅笔图标** 编辑
2. 如果不存在：点击 **New repository secret** 新建
3. 填入 **Name**（如 CITY）和 **Value**（如139个城市列表）
4. 点击 **Update secret** 或 **Add secret**

### 4. 验证更新

更新所有 Secrets 后：
1. 进入 Actions 页面：https://github.com/belongialiest-coder/weather/actions
2. 点击左侧 **Weather Alert Bot**
3. 点击右上角 **Run workflow** → **Run workflow** 手动触发
4. 等待运行完成（约2-3分钟）
5. 打开 https://belongialiest-coder.github.io/weather/ 查看是否更新

### 5. 预期结果

更新成功后，GitHub Pages 应该显示：
- ✅ 标题：气象预警中心 - 监控 **139** 个城市
- ✅ 按省份分组（如：天津市、安徽省、河北省...）
- ✅ 每个省份显示城市和预警详情
- ✅ 无地图功能
- ✅ 显示所有预警，无省略

---

## ⚠️ 重要提示

1. **CITY 的值必须是一行**，不要有换行符，城市之间用英文逗号分隔
2. **ALERT_TYPES 是新增的**，之前没有这个 Secret，需要新建
3. 更新后必须手动触发一次 Actions，或等待定时任务（8:00 / 18:00）
4. 如果还是显示旧内容，可能需要清除浏览器缓存（Ctrl+F5 强制刷新）

---

## 📞 需要帮助？

如果更新后还有问题，请检查：
1. Actions 运行日志是否有错误
2. 日志中是否显示"监控城市数量: 139"
3. 是否所有5个 Secrets 都已正确设置
