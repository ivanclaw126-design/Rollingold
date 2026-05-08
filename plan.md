# Rollingold 行业轮动 HTML 开发计划

## 1. 目标

在 `/Users/spicyclaw/MyProjects/Rollingold` 从零搭建一个每日自动更新的静态 HTML 页面，用于盘后参考行业日级别、周级别轮动状态，并辅助在不同行业之间做资金配置判断。

最终页面发布到 GitHub Pages，计划仓库为公开仓库：

```text
ivanclaw126-design/Rollingold
```

页面定位是研究工具，不输出自动交易指令，不生成硬性买卖点，只输出行业强弱、轮动阶段、宽度确认、背离提示和观察优先级。

## 2. 核心方案

第一版采用“价格相对轮动 + 市场宽度确认 + 综合评分”的三层结构。

### 2.1 价格相对轮动

用途：回答哪些行业相对市场正在跑赢，以及相对强弱是在增强还是减弱。

默认数据源：

- AKShare
- 申万一级行业指数
- 默认基准：`801003` 申万 A 指

已验证本机环境：

```text
Python 3.14.3
akshare 1.18.55
Node.js v24.14.0
npm 11.9.0
gh 2.88.0
```

核心接口：

```python
ak.index_realtime_sw(symbol="一级行业")
ak.index_hist_sw(symbol="801080", period="day")
ak.index_hist_sw(symbol="801080", period="week")
```

核心计算：

```text
relative_strength = industry_close / benchmark_close
price_x = zscore(log(relative_strength), lookback=120)
momentum_y = zscore(log(relative_strength) - shift(log(relative_strength), 20), lookback=120)
```

日线默认动量窗口为 20 个交易日，周线默认动量窗口为 4 周。

象限定义：

| 象限 | 条件 | 状态 |
|---|---|---|
| 右上 | price_x >= 0 且 momentum_y >= 0 | 领涨 |
| 右下 | price_x >= 0 且 momentum_y < 0 | 走弱 |
| 左下 | price_x < 0 且 momentum_y < 0 | 领跌 |
| 左上 | price_x < 0 且 momentum_y >= 0 | 走强 |

### 2.2 市场宽度确认

用途：回答行业内部赚钱效应是否扩散，避免只被少数权重股拉动误导。

数据来源参考：

```text
/Users/spicyclaw/.openclaw/workspace-analyst/scripts/market_breadth_daily_send.sh
```

实际抓取入口：

```text
https://sckd.dapanyuntu.com/api/api/industry_ma20_analysis_page?page=0
```

请求头必须包含：

```text
Referer: https://sckd.dapanyuntu.com/
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

当前已确认该接口返回：

```text
86 个二级行业
约 29-31 个交易日
MA20 站上率数据
```

聚合方式沿用现有脚本：

- 86 个二级行业映射到 26 个一级行业大类
- 每个一级行业按有效二级行业取算术平均
- `0` 按无数据处理，不计入平均
- 保留 1 位小数

宽度指标：

```text
breadth_ma20 = 一级行业 MA20 站上率
breadth_delta_1d = 当日宽度 - 前一交易日宽度
breadth_delta_5d = 当日宽度 - 5 个交易日前宽度
market_breadth_avg = 全部一级行业宽度均值
relative_breadth = breadth_ma20 - market_breadth_avg
```

### 2.3 成交确认

用途：判断行业强弱是否有资金关注度支撑。

第一版不接入复杂资金流指标，只使用 AKShare 申万指数行情里的成交额字段。

指标：

```text
amount_share = industry_amount / sum(all_industry_amount)
amount_share_ma20 = amount_share 的 20 日均值
amount_confirm = amount_share > amount_share_ma20
```

资金流、大单流入、ETF 流入第一版不做主信号，只预留后续扩展。

## 3. 行业口径

页面主行业列表以大盘云图宽度数据的 26 个一级行业为准。价格端申万一级行业需要对齐到该口径。

默认映射：

| 页面行业 | 价格端来源 |
|---|---|
| 农林牧渔 | 农林牧渔 |
| 基础化工 / 化工 | 基础化工 |
| 钢铁 | 钢铁 |
| 有色金属 | 有色金属 |
| 电子 | 电子 |
| 汽车 | 汽车 |
| 食品饮料 | 食品饮料 |
| 纺织服装 | 纺织服饰 |
| 轻工制造 | 轻工制造 + 家用电器 |
| 医药 | 医药生物 |
| 公用事业 | 公用事业 + 环保 |
| 交通运输 | 交通运输 |
| 房地产 | 房地产 |
| 商贸零售 | 商贸零售 + 社会服务 + 美容护理 |
| 银行 | 银行 |
| 金融 | 非银金融 |
| 综合 | 综合 |
| 建筑 | 建筑材料 + 建筑装饰 |
| 电力 | 电力设备 |
| 机械 | 机械设备 |
| 国防军工 | 国防军工 |
| 计算机 | 计算机 |
| 传媒 | 传媒 |
| 通信 | 通信 |
| 煤炭 | 煤炭 |
| 石油 | 石油石化 |

如果一个页面行业由多个价格行业合成，第一版使用等权平均相对强弱，不做市值加权。

## 4. 综合评分

第一版评分范围为 0-100，用于排序和分层，不直接等同于仓位。

权重：

| 模块 | 权重 |
|---|---:|
| 价格相对强弱 | 30% |
| 相对强弱动量 | 25% |
| MA20 站上率 | 20% |
| MA20 站上率改善速度 | 15% |
| 成交额确认 | 10% |

状态标签：

| 标签 | 规则 |
|---|---|
| 强趋势共振 | 领涨象限，宽度高于市场均值，宽度 5 日改善，成交确认为真 |
| 强势放缓 | 领涨或走弱象限，但宽度 5 日回落或动量转弱 |
| 弱势修复 | 走强象限，宽度 5 日改善 |
| 弱势衰减 | 领跌象限，宽度低于市场均值且动量为负 |
| 观察 | 不满足以上明确状态 |

背离提示：

| 背离 | 含义 |
|---|---|
| 价格强、宽度弱 | 少数权重股拉动，趋势质量不足 |
| 价格弱、宽度改善 | 可能处于早期修复，需要观察价格确认 |
| 价格强、成交弱 | 价格相对占优，但资金关注度不足 |
| 宽度高、动量弱 | 行业内普涨后边际放缓 |

## 5. 页面设计

目标是一个可直接打开和发布的静态页面：

```text
docs/index.html
```

页面模块：

1. 顶部状态栏
   - 最新交易日
   - 数据更新时间
   - 日线 / 周线切换
   - 数据质量提示

2. 行业相对轮动图
   - SVG 或 Canvas 四象限图
   - 横轴：相对强弱
   - 纵轴：相对动量
   - 展示最近 20 日或 24 周轨迹
   - 当前点按状态着色

3. 市场宽度热力图
   - 参考图二
   - 展示最近约 30 个交易日 MA20 站上率
   - 色阶 0-100
   - 行业按最新宽度或综合评分排序

4. 综合评分榜
   - 当前强势行业
   - 边际改善行业
   - 边际恶化行业
   - 弱势修复行业
   - 走弱预警行业

5. 行业详情面板
   - 点击行业后展示：
     - 当前象限
     - 综合评分
     - MA20 宽度
     - 1 日 / 5 日宽度变化
     - 成交确认
     - 背离提示
     - 最近轨迹简评

6. 页脚说明
   - 数据来源
   - 更新时间
   - “仅供研究参考，不构成投资建议”

## 6. 项目结构

建议结构：

```text
Rollingold/
├── plan.md
├── pyproject.toml
├── README.md
├── config/
│   └── industry_mapping.yaml
├── data/
│   ├── cache/
│   └── state/
├── docs/
│   └── index.html
├── logs/
│   └── .gitkeep
├── reports/
│   └── latest.json
├── scripts/
│   ├── generate_site.sh
│   ├── publish_daily.sh
│   └── install_launchd.sh
├── src/
│   └── rollingold/
│       ├── __init__.py
│       ├── breadth.py
│       ├── config.py
│       ├── data_sources.py
│       ├── indicators.py
│       ├── render.py
│       └── site.py
└── tests/
    ├── fixtures/
    ├── test_breadth.py
    ├── test_indicators.py
    └── test_render.py
```

## 7. 开发步骤

### 阶段 1：初始化项目

- 初始化 Git 仓库
- 新建公开 GitHub 仓库 `ivanclaw126-design/Rollingold`
- 配置 GitHub Pages 来源为 `main:/docs`
- 建立 Python 项目结构
- 添加基础 README 和本计划文档

验收：

```bash
git status --short
python3 -m pytest
```

### 阶段 2：迁移宽度数据管线

- 将大盘云图 API 抓取逻辑封装到 `src/rollingold/breadth.py`
- 将二级行业到一级行业映射写入 `config/industry_mapping.yaml`
- 输出标准化宽度数据到 `data/state/breadth_history.json`
- 保留最近可用历史，避免接口短暂失败导致页面空白

验收：

```bash
python3 -m rollingold.breadth --output data/state/breadth_history.json
```

结果应包含：

- `dates`
- `industries`
- `values`
- `latest_date`
- `market_average`

### 阶段 3：接入价格相对轮动

- 用 AKShare 拉取申万一级指数历史行情
- 拉取默认基准 `801003`
- 计算日线和周线相对强弱、动量、象限
- 对页面行业映射中的合成行业做等权平均

验收：

```bash
python3 -m rollingold.site --mode data --output reports/latest.json
```

结果应包含每个行业：

- `price_x`
- `momentum_y`
- `quadrant`
- `path_daily`
- `path_weekly`

### 阶段 4：生成静态 HTML

- 用 Python 生成 `docs/index.html`
- 页面内嵌最新 JSON 数据
- 不依赖后端
- CSS 和 JS 直接内联，方便 GitHub Pages 发布
- 实现日线 / 周线切换、行业点击详情、热力图、排行榜

验收：

```bash
python3 -m rollingold.site --output docs/index.html
open docs/index.html
```

浏览器中应能看到：

- 四象限轮动图
- 宽度热力图
- 综合评分榜
- 行业详情
- 更新时间

### 阶段 5：自动更新和发布

- 编写 `scripts/publish_daily.sh`
- 检查是否交易日
- 抓取数据并生成页面
- 若最新交易日未变化，则跳过提交
- 若页面变化，则提交并推送

默认提交格式：

```text
chore: update industry rotation report YYYY-MM-DD
```

安装本机 launchd：

```text
~/Library/LaunchAgents/com.spicyclaw.rollingold.daily.plist
```

运行时间：

```text
周一至周五 16:20 Asia/Shanghai
```

验收：

```bash
bash scripts/publish_daily.sh
tail -n 100 logs/daily-update.log
```

### 阶段 6：发布验证

- 推送到 GitHub
- 打开 GitHub Pages URL
- 验证页面返回 200
- 验证最新日期和本地 `reports/latest.json` 一致
- 验证移动端宽度不重叠

## 8. 测试计划

### 单元测试

覆盖：

- 行业映射完整性
- 0 值过滤
- 宽度聚合
- 相对强弱计算
- 动量计算
- 象限判断
- 综合评分
- 状态标签
- 背离提示

### 离线 Fixture 测试

保存固定样例：

```text
tests/fixtures/breadth_raw.json
tests/fixtures/sw_index_hist_801080.csv
tests/fixtures/sw_index_hist_801003.csv
```

离线生成：

```bash
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

断言：

- 页面非空
- 包含 26 个行业
- 包含 `价格相对轮动`
- 包含 `市场宽度`
- 包含 `综合评分`
- 最新日期正确

### 浏览器验证

用 Playwright 检查：

- `docs/index.html` 可以打开
- SVG 或 Canvas 非空
- 热力图格子数量正确
- 日线 / 周线切换有效
- 点击行业能更新详情面板
- 移动端无明显文字重叠

## 9. 风险和处理

### AKShare 接口漂移

处理：

- 保留最近一次成功数据
- 页面顶部显示数据质量状态
- 日志记录接口错误
- 不用失败数据覆盖 `reports/latest.json`

### 大盘云图接口 403 或结构变化

处理：

- 固定 Referer 和 User-Agent
- 验证返回字段 `dates`、`industries`、`data`
- 失败时沿用上一交易日宽度数据，并在页面显示“宽度数据未更新”

### GitHub Pages 更新延迟

处理：

- 本地脚本只负责提交和推送
- 发布后用 `curl -I` 检查 Pages URL
- 若 URL 未更新，日志标注等待 Pages 构建

### 行业口径不完全一致

处理：

- 第一版明确标注为“宽度行业口径 + 申万价格口径映射”
- 合成行业使用等权平均
- 后续如接入 Wind / Choice / iFinD，再升级为统一行业成分和市值权重

## 10. 第一版不做

- 不做自动下单
- 不做个股推荐
- 不做资金流主信号
- 不做完整历史回测页面
- 不做数据库服务
- 不做用户登录
- 不做多账户同步

## 11. 验收标准

第一版完成时必须满足：

1. `docs/index.html` 能独立打开。
2. GitHub Pages 能访问最新页面。
3. 页面展示价格相对轮动图、市场宽度热力图、综合评分榜和行业详情。
4. 每日自动更新脚本能在本机运行。
5. 无新交易日时不会产生无意义提交。
6. 数据源失败时不会覆盖上一版可用页面。
7. 页面明确标注“仅供研究参考，不构成投资建议”。

