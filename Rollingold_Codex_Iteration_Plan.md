# Rollingold 迭代规划与 Codex 执行说明

> 目标：把 Rollingold 从“盘后行业轮动静态报表”升级为“可解释、可复现、可交互、可辅助策略规划的板块轮动研究网站”。
>
> 约束：保持 GitHub Pages 静态发布优先；不输出个股推荐、不生成自动交易指令、不承诺收益；所有策略功能均定位为研究与情景分析。

---

## 0. 当前项目诊断

### 0.1 已确认的当前形态

- 仓库：`ivanclaw126-design/Rollingold`
- 发布页：`https://ivanclaw126-design.github.io/Rollingold/`
- 当前产品定位：盘后行业轮动静态页面。
- 当前默认发布路径：`docs/index.html`，适配 GitHub Pages `main:/docs` 来源。
- 当前核心信号：
  - 价格相对轮动：申万一级行业相对默认基准 `801003` 申万 A 指的相对强弱与动量。
  - 市场宽度确认：大盘云图二级行业 MA20 站上率聚合到页面行业。
  - 综合评分排序：价格、动量、宽度、宽度改善、成交确认合成 0-100 分。
- 当前页面模块：行业轮动、价格相对轮动图、综合评分榜、市场宽度热力图、行业 ETF 归一化业绩、ETF 对应关系与一致性。
- 当前技术形态：Python 抓数与计算，生成纯静态 HTML；`render.py` 内联 CSS/JS；`reports/latest.json` 作为最新数据报告。

### 0.2 当前代码结构观察

现有结构大体如下：

```text
Rollingold/
├── config/
│   └── industry_mapping.yaml
├── data/
│   ├── cache/
│   └── state/
├── docs/
│   └── index.html
├── reports/
│   └── latest.json
├── scripts/
├── src/
│   └── rollingold/
│       ├── breadth.py
│       ├── config.py
│       ├── data_sources.py
│       ├── indicators.py
│       ├── render.py
│       └── site.py
└── tests/
```

关键模块分工：

| 模块 | 当前职责 | 主要问题 | 后续方向 |
|---|---|---|---|
| `data_sources.py` | AKShare 申万指数、ETF 现货、ETF 历史数据加载与缓存 | 缺少统一数据源注册、字段契约、源级质量评分 | 建立 `SourceSpec`、`DataContract`、`DataQualityReport` |
| `breadth.py` | 抓取大盘云图 MA20 宽度并聚合到页面行业 | 第三方接口非官方，失败兜底已有但可解释性不足 | 增加质量台账、源漂移检测、缺失行业暴露 |
| `indicators.py` | z-score、象限、综合评分、状态标签、背离提示 | 固定权重、固定阈值、无历史验证；路径 z-score 以当前窗口统计量归一，适合展示但不适合回测 | 升级为因子面板、滚动归一、可配置评分、贡献拆解 |
| `site.py` | 串联配置、宽度、价格、ETF，生成 report | 逻辑较集中，数据构建、ETF 选择、排行、元信息耦合 | 拆分为 `pipeline.py`、`factor_panel.py`、`scoring.py`、`etf.py` |
| `render.py` | 生成单文件 HTML、CSS、JS | 单文件过长，后续维护成本高；交互扩展受限 | 先抽取 JS/CSS 字符串模块，再考虑轻量前端构建 |
| `tests/` | 覆盖指标和页面生成基础断言 | 有离线 fixture，但缺少 schema、回测、端到端交互测试 | 增加 JSON Schema、Playwright、golden snapshot、无前视偏差测试 |

### 0.3 当前最大瓶颈

1. **从“信号展示”到“策略研究”的鸿沟**  
   现在页面能回答“今天谁强、谁改善、谁走弱”，但还不能系统回答：
   - 过去这种信号有效吗？
   - 不同参数下结论稳定吗？
   - 某行业当前分数来自哪些因子？
   - 轮动阶段发生了什么迁移？
   - 如果采用 Top-N / 低换手 / 风险过滤，结果如何？

2. **数据可信度没有产品化表达**  
   已有数据质量提示，但用户看不到每个行业、每个信号的来源覆盖、日期对齐、缺失程度、口径偏差、ETF 近似程度。

3. **综合评分可解释性不足**  
   当前固定权重可以作为第一版，但面向更多用户时，需要展示“分数贡献项”和“置信度”，否则评分容易被误解为黑箱投资建议。

4. **交互不足以支撑研究闭环**  
   现有页面适合读报表，但还缺少参数试验、行业对比、回测、导出、URL 状态保存、策略模拟等功能。

---

## 1. 产品定位升级

### 1.1 新定位

**Rollingold = 面向 A 股行业/板块轮动的静态研究工作台。**

核心不是给出“买哪个”，而是帮助用户完成四个研究动作：

1. **发现**：找到正在修复、确认、加速、背离、衰退的行业。
2. **解释**：看到每个行业的价格、动量、宽度、成交、风险、ETF 一致性贡献。
3. **验证**：用历史信号回看与简单策略回测检查有效性。
4. **规划**：在不同约束下模拟行业配置方案，例如 Top-N、低换手、风险过滤、观察名单。

### 1.2 用户分层

| 用户 | 主要问题 | 对应功能 |
|---|---|---|
| 普通主动投资者 | 哪些板块值得关注？为什么？风险在哪里？ | 今日摘要、信号分组、行业详情、解释卡片 |
| 研究员 / FA / VC 观察者 | 行业景气与二级市场信号是否变化？ | 行业对比、趋势阶段、宽度扩散、事件备注 |
| 量化爱好者 | 这个评分体系历史上是否有效？ | 因子面板、回测、参数敏感性、下载数据 |
| 组合管理者 | 如何形成有纪律的行业配置观察框架？ | 策略实验室、Top-N、再平衡、换手约束、风险过滤 |

---

## 2. 总体架构升级

### 2.1 建议新增模块

```text
src/rollingold/
├── models.py              # dataclass / typed schema：行业、因子、信号、回测结果
├── schemas.py             # JSON Schema / report schema 校验
├── data_contracts.py      # 数据源字段、日期、质量校验
├── factor_panel.py        # 生成行业 x 日期 x 因子面板
├── scoring.py             # 可配置评分、贡献拆解、置信度
├── phase.py               # 轮动阶段机与阶段迁移
├── backtest.py            # 策略回测与指标计算
├── strategy_lab.py        # 策略参数、组合模拟、结果序列
├── etf.py                 # ETF 匹配、替代口径、跟踪一致性
├── report_builder.py      # 组装 latest.json 和 history report
├── render_assets.py       # CSS / JS 字符串或模板资产
└── render.py              # HTML 外壳和数据注入
```

### 2.2 建议新增数据文件

```text
config/
├── industry_mapping.yaml
├── scoring.default.yaml
├── strategy_presets.yaml
└── data_sources.yaml

data/
├── cache/
├── state/
│   └── breadth_history.json
└── history/
    ├── signal_panel_daily.csv
    ├── signal_panel_weekly.csv
    ├── score_history.csv
    └── backtest_summary.json

reports/
├── latest.json
└── history/
    └── YYYY-MM-DD.json

docs/
├── index.html
└── assets/                # 可选；若继续单文件 HTML，则不需要
```

### 2.3 保持向后兼容

Codex 执行时必须保证以下命令仍可用：

```bash
python3 -m rollingold.breadth --output data/state/breadth_history.json
python3 -m rollingold.site --mode data --refresh-cache --output reports/latest.json
python3 -m rollingold.site --output docs/index.html
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
python3 -m pytest
```

如需新增命令，建议采用：

```bash
python3 -m rollingold.site --mode panel --output data/history/signal_panel_daily.csv
python3 -m rollingold.site --mode backtest --output data/history/backtest_summary.json
```

---

## 3. 数据方向迭代

### 3.1 数据源注册与质量报告

新增 `config/data_sources.yaml`：

```yaml
sources:
  sw_index:
    provider: AKShare
    functions:
      - index_hist_sw
      - index_realtime_sw
    fields_required: [日期, 收盘, 成交额]
    freshness: trading_day
    reliability_tier: public_unofficial_adapter
  breadth_ma20:
    provider: dapanyuntu
    endpoint: https://sckd.dapanyuntu.com/api/api/industry_ma20_analysis_page?page=0
    fields_required: [dates, industries, data]
    freshness: trading_day
    reliability_tier: undocumented_public_endpoint
  etf:
    provider: AKShare
    functions:
      - fund_etf_spot_em
      - fund_etf_hist_em
    fields_required: [日期, 收盘, 成交额]
    freshness: trading_day
    reliability_tier: public_unofficial_adapter
```

新增 `DataQualityReport`：

```python
@dataclass(frozen=True)
class DataQualityReport:
    source: str
    latest_date: str
    expected_latest_date: str | None
    is_fresh: bool
    rows: int
    missing_fields: list[str]
    missing_industries: list[str]
    stale_reason: str | None
    confidence: float  # 0-1
```

页面展示：

- 顶部总质量：`完整 / 部分缺失 / 沿用旧数据 / 日期不一致`
- 行业级质量：每个行业显示价格、宽度、ETF 的数据状态。
- 数据质量详情弹窗：列出源、日期、缺失行业、字段校验、fallback 情况。

### 3.2 日期与交易日对齐

新增 `calendar.py`：

- 使用 AKShare 交易日历或本地维护的 `data/cache/trading_calendar.csv`。
- 生成 report 前检查：
  - 行业价格最新日
  - 宽度最新日
  - ETF 最新日
  - report 最新日
- 当 ETF 是当日实时、行业价格仍是上一交易日时，不应简单用 `max()` 混成“最新数据日”；应区分：
  - `latest_report_date`
  - `price_date`
  - `breadth_date`
  - `etf_date`
  - `date_alignment_status`

### 3.3 因子历史面板

新增 `factor_panel.py`，输出长表：

```text
date, period, industry, factor, value, source, confidence
2026-05-08, daily, 电子, price_x, 1.23, sw_index, 0.95
2026-05-08, daily, 电子, momentum_y, 0.84, sw_index, 0.95
2026-05-08, daily, 电子, breadth_ma20, 67.5, breadth_ma20, 0.80
```

也可以输出宽表：

```text
date,period,industry,price_x,momentum_y,breadth_ma20,breadth_delta_1d,breadth_delta_5d,relative_breadth,amount_share,amount_share_ma20,amount_confirm,vol_20,drawdown_60,score,phase,confidence
```

用途：

- 今日信号
- 分数历史曲线
- 行业阶段迁移
- 回测
- 参数敏感性
- 数据导出

### 3.4 数据口径透明化

每个行业详情中新增“口径说明”：

- 价格端来源：例如 `轻工制造 = 轻工制造 + 家用电器`。
- 宽度端来源：对应二级行业列表。
- ETF 替代关系：直接匹配 / 近似 / 仅覆盖局部口径。
- 口径置信度：
  - 直接一致：0.9-1.0
  - 多行业合成：0.7-0.9
  - 主题 ETF 近似：0.4-0.7
  - 严重偏离：低于 0.4

---

## 4. 算法方向迭代

### 4.1 相对强弱与动量：从展示 z-score 升级为可回测因子

当前可保留：

```text
relative_strength = industry_close / benchmark_close
price_x = zscore(log(relative_strength), lookback=120)
momentum_y = zscore(log(relative_strength) - shift(log(relative_strength), 20), lookback=120)
```

新增严格滚动版本，避免历史回测前视偏差：

```python
def rolling_zscore(series: pd.Series, lookback: int) -> pd.Series:
    mean = series.rolling(lookback, min_periods=lookback // 2).mean()
    std = series.rolling(lookback, min_periods=lookback // 2).std(ddof=0)
    return (series - mean) / std.replace(0, pd.NA)
```

新增因子：

| 因子 | 含义 | 用途 |
|---|---|---|
| `rs_z_120` | 相对强弱 120D 滚动 z-score | 判断当前位置 |
| `rs_mom_20_z` | 相对强弱 20D 变化 z-score | 判断边际速度 |
| `rs_mom_60_z` | 相对强弱 60D 变化 z-score | 过滤短期噪音 |
| `rs_accel_5_20` | 5D 动量相对 20D 动量加速度 | 捕捉早期修复 |
| `rs_rank_pct` | 行业内相对强弱横截面百分位 | 横向排序更直观 |
| `rs_new_high_60` | 相对强弱是否创 60D 新高 | 趋势确认 |

### 4.2 宽度因子升级

当前宽度信号保留：

- `breadth_ma20`
- `breadth_delta_1d`
- `breadth_delta_5d`
- `relative_breadth`

新增：

| 因子 | 计算 | 解释 |
|---|---|---|
| `breadth_slope_5` | 近 5 日线性回归斜率 | 宽度扩散速度 |
| `breadth_slope_10` | 近 10 日线性回归斜率 | 扩散持续性 |
| `breadth_above_50` | `breadth_ma20 >= 50` | 行业内多数股票站上 MA20 |
| `breadth_thrust` | 5 日从低位快速上行，例如 `<30 -> >50` | 潜在扩散启动 |
| `breadth_divergence_score` | 价格强弱与宽度相对强弱差值 | 判断权重股拉动还是普涨 |
| `breadth_persistence` | 最近 N 日宽度高于市场均值比例 | 趋势质量稳定性 |

### 4.3 成交确认升级

当前 `amount_confirm = amount_share > amount_share_ma20` 过于离散，应保留 Boolean 但新增连续因子：

| 因子 | 计算 | 解释 |
|---|---|---|
| `amount_share` | 行业成交额 / 全行业成交额 | 市场关注度 |
| `amount_share_z_60` | 成交占比 60D z-score | 资金热度异常 |
| `amount_mom_5` | 成交占比 5D 变化 | 短期流入关注 |
| `price_amount_confirm_score` | 价格动量与成交热度共振分 | 放量上涨或缩量反弹区别 |

### 4.4 风险与稳定性因子

面向策略规划必须加入风险约束，否则“高分行业”会被用户误解为低风险。

新增：

| 因子 | 计算 | 用途 |
|---|---|---|
| `vol_20` | 行业指数 20D 日收益波动率 | 风险过滤 |
| `vol_60` | 60D 波动率 | 策略风控 |
| `max_drawdown_60` | 近 60D 最大回撤 | 避免下跌中继 |
| `downside_vol_60` | 下行波动率 | 趋势质量 |
| `trend_stability` | 近 N 日处于同一正向阶段比例 | 降低频繁换手 |
| `correlation_to_benchmark` | 与基准相关性 | 区分 beta 与 alpha |

### 4.5 轮动阶段机

保留四象限，但新增更适合普通用户理解的阶段标签：

```text
低位修复 -> 价格确认 -> 趋势扩散 -> 高位背离 -> 动能衰退 -> 弱势下行
```

建议规则：

| 阶段 | 规则示例 |
|---|---|
| 低位修复 | `price_x < 0` 且 `momentum_y > 0` 且 `breadth_delta_5d > 0` |
| 价格确认 | `price_x >= 0` 且 `momentum_y > 0`，宽度尚未显著高于市场 |
| 趋势扩散 | `price_x >= 0`、`momentum_y > 0`、`breadth_ma20 > market_avg`、`breadth_persistence > 0.6` |
| 高位背离 | `price_x > 0` 但 `breadth_delta_5d < 0` 或 `breadth_ma20 < market_avg` |
| 动能衰退 | `price_x > 0` 且 `momentum_y < 0` |
| 弱势下行 | `price_x < 0` 且 `momentum_y < 0` 且宽度弱 |

新增阶段迁移记录：

```text
date,industry,prev_phase,phase,transition,score_delta
2026-05-08,电子,价格确认,趋势扩散,upgrade,+8.2
```

页面新增“今日阶段变化”：

- 新进入趋势扩散
- 从高位背离转为动能衰退
- 从弱势下行转为低位修复

### 4.6 综合评分升级为可解释评分

当前权重可作为 `scoring.default.yaml` 的第一套 preset：

```yaml
score_presets:
  default_v1:
    price_relative_strength: 0.30
    relative_momentum: 0.25
    ma20_breadth: 0.20
    breadth_delta_5d: 0.15
    amount_confirm: 0.10
```

新增 `balanced_v2`：

```yaml
score_presets:
  balanced_v2:
    trend:
      rs_z_120: 0.18
      rs_rank_pct: 0.07
    momentum:
      rs_mom_20_z: 0.15
      rs_accel_5_20: 0.05
    breadth:
      breadth_ma20: 0.12
      breadth_slope_5: 0.08
      breadth_persistence: 0.08
    liquidity:
      amount_share_z_60: 0.08
      amount_mom_5: 0.04
    risk:
      vol_penalty: 0.06
      drawdown_penalty: 0.06
    data_quality:
      confidence: 0.04
```

每个行业输出：

```json
"score_breakdown": {
  "trend": 23.5,
  "momentum": 17.2,
  "breadth": 19.0,
  "liquidity": 6.4,
  "risk": -3.2,
  "data_quality": 3.8,
  "total": 66.9
}
```

页面展示“分数贡献条形图 / waterfall”。

### 4.7 背离识别升级

当前背离：

- 价格强、宽度弱
- 价格弱、宽度改善
- 价格强、成交弱
- 宽度高、动量弱

新增：

| 背离 | 识别 | 页面解释 |
|---|---|---|
| 价格创新高但宽度不创新高 | `rs_new_high_60=True` 且 `breadth_ma20 < previous_high_60` | 权重拉动可能较强 |
| 成交升温但价格未确认 | `amount_share_z_60 > 1` 且 `momentum_y <= 0` | 有资金关注但趋势未确认 |
| 宽度扩散但 ETF 偏离 | `breadth_delta_5d > 0` 且 ETF consistency=偏离 | ETF 可能不是好替代品 |
| 高波动冲分 | `score high` 且 `vol_20` 高分位 | 分数有效但风险更高 |

---

## 5. 策略规划与回测方向

### 5.1 策略实验室 MVP

新增页面区块：`策略实验室`。

用户可设置：

- 周期：日线 / 周线
- 评分方案：`default_v1` / `balanced_v2`
- 行业数量：Top 3 / Top 5 / Top 8
- 再平衡频率：每 5 / 10 / 20 个交易日
- 风险过滤：排除 `vol_20` 最高 20% 或 `max_drawdown_60 < -15%`
- 交易成本：默认单边 0.1%，可调
- 换手约束：单次最多替换 N 个行业

输出：

- 策略净值曲线
- 基准净值曲线
- 年化收益、年化波动、最大回撤、胜率、换手率
- 最近一期持仓行业列表
- 每期行业更换原因：分数上升 / 阶段升级 / 风险过滤 / 分数跌出

### 5.2 回测实现规则

新增 `backtest.py`：

```python
@dataclass(frozen=True)
class StrategyConfig:
    score_preset: str
    top_n: int
    rebalance_days: int
    cost_bps: float
    risk_filter: str | None
    max_replacements: int | None

@dataclass(frozen=True)
class BacktestResult:
    dates: list[str]
    equity_curve: list[float]
    benchmark_curve: list[float]
    holdings: list[dict]
    trades: list[dict]
    metrics: dict[str, float]
```

关键约束：

1. 回测只能使用当日或之前可得数据。
2. 若信号在盘后生成，则下一交易日开盘或收盘执行，避免前视。
3. 默认行业收益使用申万行业指数收益，不用 ETF 收益；ETF 只作为可投资替代参考。
4. 交易成本必须进入回测。
5. 结果标注“历史模拟，不代表未来收益”。

### 5.3 回测指标

```text
annual_return
annual_volatility
sharpe_like_ratio
max_drawdown
calmar_like_ratio
win_rate_daily
win_rate_rebalance
turnover_average
turnover_total
active_return_vs_benchmark
information_ratio_like
```

不建议第一版引入过度复杂的统计显著性；但可以增加：

- 分年度表现
- 回撤区间
- 持仓集中度
- 因子分桶收益

### 5.4 参数敏感性

新增“参数稳定性”表：

| Top-N | 再平衡 | 收益 | 回撤 | 换手 | 当前持仓一致性 |
|---:|---:|---:|---:|---:|---:|
| 3 | 5D | ... | ... | ... | ... |
| 5 | 10D | ... | ... | ... | ... |
| 8 | 20D | ... | ... | ... | ... |

目标：避免用户只看某一个被优化过的参数组合。

---

## 6. 视觉设计方向

### 6.1 信息架构

建议首页改成五个连续层级：

1. **今日总览**
   - 市场轮动温度
   - 强趋势行业数
   - 低位修复行业数
   - 走弱预警行业数
   - 数据质量状态

2. **今日变化**
   - 分数上升 Top 5
   - 分数下降 Top 5
   - 阶段升级
   - 阶段降级

3. **行业轮动地图**
   - 四象限散点 + 轨迹
   - 行业点大小可表达成交热度或 ETF 规模
   - 行业点透明度可表达数据置信度

4. **行业详情抽屉**
   - 当前阶段
   - 分数贡献
   - 宽度曲线
   - ETF 替代说明
   - 近 20 日关键变化
   - 口径与数据质量

5. **策略实验室**
   - 参数选择
   - 回测表现
   - 当前候选组合
   - 风险说明

### 6.2 视觉语言

保留当前低饱和、研究工具风格，但增强层次：

- 背景：浅灰绿或中性灰。
- 卡片：白底，轻边框。
- 正向：绿色。
- 修复 / 观察：蓝色。
- 放缓 / 警戒：琥珀色。
- 负向：红色。
- 数据缺失：灰色斜纹或虚线。

避免：

- 大面积高饱和红绿，尤其面向色弱用户。
- 用单一颜色表达全部含义。
- 把评分颜色设计得像“强烈买卖建议”。

### 6.3 图表设计

| 图表 | 当前 | 升级 |
|---|---|---|
| 四象限图 | 已有 | 点大小=成交热度，透明度=数据置信度，尾迹长度可选，hover 显示关键因子 |
| 宽度热力图 | 已有 | 增加排序方式：按分数 / 宽度 / 阶段 / 行业顺序；增加行内趋势 sparkline |
| ETF 业绩图 | 已有 | 增加行业指数 vs ETF 双线对比，标记偏离区间 |
| 评分榜 | 已有 | 增加分数贡献堆叠条、分数变化、阶段变化 |
| 新增回测图 | 无 | 净值曲线、回撤曲线、换手柱状、持仓时间轴 |
| 新增因子雷达 | 无 | 行业详情内展示趋势、动量、宽度、成交、风险、置信度 |

### 6.4 移动端设计

- 顶部 tab 不超过一行时横向滚动。
- 四象限图保持横向滚动，提供“仅当前点”简化模式。
- 行业详情使用底部抽屉。
- 热力图默认最近 10 日，用户可展开。
- 策略实验室移动端以表单 + 卡片结果为主，不强行展示大表。

---

## 7. 交互方式方向

### 7.1 参数控制

新增控件：

- 基准：申万 A 指 / 沪深 300 / 中证全指，可先只做配置预留。
- 周期：日线 / 周线。
- 动量窗口：20D / 40D / 60D。
- z-score lookback：120D / 240D。
- 轨迹长度：20 / 60 / 120 / 仅点位。
- 排序方式：综合评分 / 分数变化 / 宽度 / 宽度变化 / 风险。
- 评分方案：默认 / 趋势优先 / 修复优先 / 低风险优先。

实现要求：

- 使用 URL query 保存状态，例如：

```text
?period=daily&score=balanced_v2&trace=60&sort=score&industry=电子
```

- 使用 `localStorage` 保存用户上次选择。
- 提供“恢复默认”按钮。

### 7.2 行业对比

新增 compare mode：

- 用户可选择 2-5 个行业。
- 展示：
  - 相对收益曲线
  - 分数历史
  - 宽度历史
  - ETF 表现
  - 因子雷达对比

数据字段：

```json
"compare_series": {
  "电子": {"dates": [...], "score": [...], "rs": [...], "breadth": [...]},
  "通信": {...}
}
```

### 7.3 今日变化解释

新增 `change_log`：

```json
"change_log": [
  {
    "industry": "电子",
    "type": "phase_upgrade",
    "from": "价格确认",
    "to": "趋势扩散",
    "score_delta": 7.8,
    "reason": ["相对动量上升", "MA20 宽度高于市场均值", "成交占比高于 20D 均值"]
  }
]
```

页面展示：

- “今天发生了什么”卡片。
- 每条变化可点击跳到行业详情。

### 7.4 导出与复现

新增按钮：

- 下载当前 report JSON。
- 下载因子 CSV。
- 复制当前视图链接。
- 复制行业详情摘要。

摘要模板：

```text
电子：当前处于「趋势扩散」，综合评分 72.4。主要贡献来自相对强弱、宽度扩散和成交确认；主要风险为近 20 日波动率偏高。数据口径：价格端为申万电子，宽度端为半导体/消费电子/光学光电子/电子元件聚合。
```

---

## 8. Codex 执行路线图

### Phase 0：工程护栏与文档

**目标**：在不改变现有功能的前提下，让项目更容易扩展。

任务：

1. 新增 `docs/architecture.md`，说明当前 pipeline。
2. 新增 `docs/methodology.md`，解释所有指标、权重、口径、局限。
3. 新增 `docs/data_sources.md`，解释数据源、更新时间、失败处理。
4. 新增 `config/scoring.default.yaml`，把当前固定权重配置化。
5. 新增 `tests/test_config_integrity.py`：
   - 行业数为 26。
   - 每个行业有价格源、宽度源、ETF rule。
   - benchmark code 存在。

验收：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

### Phase 1：因子面板与历史信号

**目标**：让每个行业每天的信号可保存、可比较、可回测。

任务：

1. 新增 `src/rollingold/factor_panel.py`。
2. 实现 `build_factor_panel(...) -> pd.DataFrame`。
3. 新增滚动 z-score、横截面 rank、宽度 slope、成交 z-score、波动率、回撤因子。
4. 在 `site.py` 中把当前 report 构建改为先生成 panel，再从 panel 取 latest。
5. 输出：

```text
data/history/signal_panel_daily.csv
data/history/signal_panel_weekly.csv
```

6. 增加 `reports/history/YYYY-MM-DD.json`，用于比较昨日变化。

验收：

```bash
python3 -m rollingold.site --mode data --offline-fixture tests/fixtures --output reports/latest.json
python3 -m pytest
```

新增测试：

- `test_factor_panel_has_required_columns`
- `test_factor_panel_no_lookahead_for_rolling_zscore`
- `test_factor_panel_has_26_industries_per_date`
- `test_factor_panel_handles_missing_breadth`

### Phase 2：评分与阶段机升级

**目标**：从固定总分升级为“可解释评分 + 阶段迁移”。

任务：

1. 新增 `src/rollingold/scoring.py`。
2. 迁移 `score_industry` 到配置驱动。
3. 输出 `score_breakdown`。
4. 新增 `src/rollingold/phase.py`。
5. 实现 `classify_phase(row)` 与 `detect_phase_transition(prev, current)`。
6. `report["industries"]` 中新增：

```json
"phase": "趋势扩散",
"phase_transition": "upgrade",
"score_breakdown": {...},
"confidence": 0.86
```

验收：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

新增测试：

- `test_scoring_config_weights_sum_to_one_or_normalize`
- `test_score_breakdown_total_matches_score`
- `test_phase_classification_rules`
- `test_phase_transition_detection`

### Phase 3：页面 UI 升级

**目标**：让更多用户能读懂并交互探索。

任务：

1. 将 `render.py` 中 CSS / JS 拆为：

```text
src/rollingold/render_assets.py
src/rollingold/render.py
```

2. 新增页面区块：
   - 今日变化
   - 分数贡献
   - 数据质量详情
   - 口径说明
3. 四象限图升级：
   - 点大小映射成交热度。
   - 透明度映射数据置信度。
   - hover tooltip 显示 phase、score、breadth、amount、risk。
4. 热力图升级：
   - 排序方式切换。
   - 最近 10 / 30 / 全部。
5. URL query 与 localStorage 保存状态。

验收：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

页面必须包含：

```text
今日变化
分数贡献
数据质量
口径说明
复制当前视图链接
```

### Phase 4：策略实验室与回测

**目标**：从“看信号”升级到“验证信号与规划策略”。

任务：

1. 新增 `src/rollingold/backtest.py`。
2. 实现 Top-N 行业轮动回测。
3. 增加策略配置：

```yaml
strategy_presets:
  top5_weekly:
    score_preset: balanced_v2
    top_n: 5
    rebalance_days: 5
    cost_bps: 10
    risk_filter: none
  top5_low_turnover:
    score_preset: balanced_v2
    top_n: 5
    rebalance_days: 10
    cost_bps: 10
    max_replacements: 2
```

4. report 中新增：

```json
"strategy_lab": {
  "presets": [...],
  "results": [...],
  "current_candidates": [...]
}
```

5. 页面新增：
   - 策略净值曲线
   - 回撤曲线
   - 指标表
   - 当前候选组合
   - 参数敏感性表

验收：

- 无前视偏差测试通过。
- 回测结果包含交易成本。
- 页面明确展示“历史模拟，不代表未来收益”。

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

### Phase 5：质量、可访问性与发布

**目标**：适合公开给更多用户使用。

任务：

1. 增加 Playwright 或轻量浏览器测试：
   - 页面可打开。
   - tab 切换有效。
   - 行业点击详情更新。
   - URL query 可恢复状态。
   - 移动端无核心内容遮挡。
2. 增加 JSON Schema：
   - `schemas/report.schema.json`
   - `tests/test_report_schema.py`
3. 增加 Lighthouse / 可访问性检查建议。
4. README 增加：
   - 功能介绍
   - 数据源说明
   - 本地运行
   - 发布方式
   - 免责声明
5. 发布页增加 methodology 链接。

验收：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

可选：

```bash
npx playwright test
```

---

## 9. 关键实现细节

### 9.1 report JSON 建议结构

```json
{
  "meta": {
    "generated_at": "2026-05-08T16:48:36",
    "latest_report_date": "2026-05-08",
    "price_date": "2026-05-07",
    "breadth_date": "2026-05-08",
    "etf_date": "2026-05-08",
    "date_alignment_status": "partial_aligned",
    "benchmark": {"name": "申万A指", "code": "801003"},
    "data_quality": {...},
    "methodology_version": "v2.0"
  },
  "industries": [
    {
      "name": "电子",
      "rank": 1,
      "score": 72.4,
      "score_delta_1d": 3.2,
      "score_breakdown": {...},
      "phase": "趋势扩散",
      "phase_transition": "upgrade",
      "quadrant": "领涨",
      "factors": {...},
      "risk": {...},
      "breadth": {...},
      "etf": {...},
      "data_quality": {...},
      "interpretation": "..."
    }
  ],
  "change_log": [...],
  "rankings": {...},
  "breadth": {...},
  "etfs": {...},
  "strategy_lab": {...},
  "methodology": {...}
}
```

### 9.2 评分解释模板

新增 `interpretation.py` 或在 `scoring.py` 中实现：

```python
def explain_industry_signal(item: dict) -> str:
    """Return a concise, non-advisory explanation for UI display."""
```

输出原则：

- 只解释信号，不建议用户买卖。
- 先说状态，再说贡献，再说风险，再说数据口径。
- 明确“观察点”。

示例：

```text
电子处于趋势扩散阶段，综合评分 72.4。分数主要来自相对强弱处于高位、20 日相对动量改善、MA20 宽度高于市场均值；风险项显示近 20 日波动率偏高。ETF 替代品与行业指数近 120 个共同交易日相关性为 0.76，属于一致。
```

### 9.3 不做的事

第一轮升级仍不做：

- 不做用户登录。
- 不做服务器后端。
- 不做实时交易提醒。
- 不做自动下单。
- 不做个股推荐。
- 不引入需授权的商业数据源作为默认依赖。
- 不输出“确定性买入 / 卖出”结论。

---

## 10. Codex 具体工作单

### Work Item A：配置化评分

```text
目标：把当前硬编码评分权重迁移到 config/scoring.default.yaml。
修改文件：
- config/scoring.default.yaml
- src/rollingold/config.py
- src/rollingold/scoring.py
- src/rollingold/site.py
- tests/test_scoring.py
验收：
- 当前 default_v1 分数与旧逻辑在 fixture 下基本一致，允许 ±0.1 浮点误差。
- python3 -m pytest 通过。
```

### Work Item B：因子面板

```text
目标：生成行业-日期级因子面板，后续评分与回测均从 panel 读取。
修改文件：
- src/rollingold/factor_panel.py
- src/rollingold/indicators.py
- src/rollingold/site.py
- tests/test_factor_panel.py
验收：
- panel 至少包含 26 个行业。
- 包含 price_x、momentum_y、breadth_ma20、breadth_delta_5d、amount_share、vol_20、drawdown_60。
- 滚动因子不能使用未来数据。
```

### Work Item C：阶段机与今日变化

```text
目标：为每个行业增加 phase、phase_transition、change_reason。
修改文件：
- src/rollingold/phase.py
- src/rollingold/report_builder.py 或 src/rollingold/site.py
- src/rollingold/render.py
- tests/test_phase.py
验收：
- 至少支持 6 种阶段。
- report 包含 change_log。
- 页面出现“今日变化”区块。
```

### Work Item D：页面解释能力

```text
目标：让用户能看懂为什么某行业高分或预警。
修改文件：
- src/rollingold/render.py
- src/rollingold/render_assets.py
- src/rollingold/scoring.py
验收：
- 行业详情包含分数贡献、主要贡献项、主要风险项、口径说明、数据质量。
- 热力图、四象限图、榜单点击仍可联动。
- 键盘可访问性测试不回退。
```

### Work Item E：策略实验室 MVP

```text
目标：实现 Top-N 行业轮动历史模拟。
修改文件：
- config/strategy_presets.yaml
- src/rollingold/backtest.py
- src/rollingold/strategy_lab.py
- src/rollingold/site.py
- src/rollingold/render.py
- tests/test_backtest.py
验收：
- 支持 Top-N、再平衡频率、交易成本。
- 输出净值、基准、回撤、换手和指标表。
- 明确标注“历史模拟，不代表未来收益”。
```

### Work Item F：数据质量详情

```text
目标：公开展示数据可信度，不把接口问题隐藏在总提示中。
修改文件：
- src/rollingold/data_contracts.py
- src/rollingold/data_sources.py
- src/rollingold/breadth.py
- src/rollingold/site.py
- src/rollingold/render.py
- tests/test_data_quality.py
验收：
- report.meta.data_quality 结构化。
- 每个行业有 industry.data_quality。
- 当宽度 fallback 时，页面可见 stale 状态和原因。
```

---

## 11. 风险与治理

### 11.1 数据源风险

| 风险 | 处理 |
|---|---|
| AKShare 接口字段变化 | `normalize_history` 增加字段 contract；测试 fixture 覆盖字段缺失 |
| 大盘云图接口失效 | fallback 保留；页面显示 stale；增加可替代宽度数据适配器预留 |
| ETF 名称匹配错误 | 显示候选数量、fallback 来源、相关性、一致性，不把 ETF 当作精准行业代理 |
| 价格、宽度、ETF 日期不一致 | report 中显式拆分日期，不再只展示一个混合 latest_date |

### 11.2 算法风险

| 风险 | 处理 |
|---|---|
| 固定权重被误读为真理 | 展示评分 preset、贡献拆解、参数敏感性 |
| 回测过拟合 | 默认展示多参数结果，不只展示最佳参数 |
| 前视偏差 | 回测信号必须 shift 到下一交易日执行；增加单元测试 |
| 高波动行业冲高分 | 加入风险惩罚和风险提示 |

### 11.3 产品表达风险

| 风险 | 处理 |
|---|---|
| 用户误解为投资建议 | 页面、策略实验室、导出摘要均保留免责声明 |
| 过多指标导致复杂 | 首页只展示结论；详情页展示解释；方法页展示完整口径 |
| 移动端不可用 | 关键卡片化，图表可横向滚动 |

---

## 12. 最终验收标准

完成本轮升级后，项目必须满足：

1. `docs/index.html` 可独立打开。
2. GitHub Pages 可访问最新页面。
3. 首页能展示：今日总览、今日变化、行业轮动图、综合评分榜、市场宽度热力图、行业详情、ETF 业绩、策略实验室。
4. 每个行业详情包含：阶段、综合评分、分数贡献、宽度、成交、风险、ETF 一致性、数据质量、口径说明。
5. `reports/latest.json` 结构化包含：`meta`、`industries`、`change_log`、`breadth`、`etfs`、`strategy_lab`、`methodology`。
6. 支持离线 fixture 生成完整页面。
7. 支持 Top-N 行业轮动历史模拟，且无前视偏差。
8. 数据源失败时不会覆盖上一版可用页面。
9. 所有新增功能有单元测试或页面生成测试覆盖。
10. 页面明确标注研究参考属性，不输出个股推荐、自动交易指令或确定性收益承诺。

---

## 13. 推荐优先级

按价值 / 成本 / 风险排序：

1. **Phase 0：工程护栏与文档**  
   成本低，能立即提高可维护性。

2. **Phase 1：因子面板与历史信号**  
   是后续评分、阶段、回测、策略实验室的基础。

3. **Phase 2：评分解释与阶段机**  
   直接提升用户理解力，是从报表到研究工具的关键。

4. **Phase 3：页面 UI 升级**  
   提升公开可用性，但应建立在数据结构稳定之后。

5. **Phase 4：策略实验室**  
   用户价值高，但必须在因子面板和无前视测试完成后做。

6. **Phase 5：质量、可访问性与发布**  
   适合作为公开推广前的最后强化。

---

## 14. 给 Codex 的执行提示

请按以下原则改造：

1. 每次只完成一个 Work Item，不要一次性重构全部文件。
2. 保留现有 CLI 与 GitHub Pages 发布路径。
3. 新增功能优先用 Python 标准库、pandas 和现有依赖；确需新依赖时先写入 `pyproject.toml` 并解释原因。
4. 所有新字段必须在离线 fixture 下可生成，不能依赖 live API 才能测试。
5. 任何数据源失败都不能覆盖上一版可用 report 和 HTML。
6. 所有策略与回测页面必须保留“研究参考，不构成投资建议；历史模拟，不代表未来收益”。
7. 改动后运行：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
```

8. 若修改 `render.py`，必须确认：
   - 日线 / 周线切换仍有效。
   - 行业点击详情仍有效。
   - 键盘可访问性不回退。
   - 移动端核心内容不遮挡。
