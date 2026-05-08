# Rollingold 架构说明

Rollingold 保持 GitHub Pages 静态发布优先：Python 负责抓取、归一化、计算和生成 `reports/latest.json`，`render.py` 将报告数据注入单文件 HTML，最终发布到 `docs/index.html`。

## Pipeline

1. `rollingold.breadth` 抓取或读取大盘云图 MA20 行业宽度，并聚合到 26 个页面行业。
2. `rollingold.site` 读取 `config/industry_mapping.yaml`、申万行业指数、ETF 现货与历史数据。
3. `factor_panel.py` 生成行业 x 日期因子面板，包含价格相对强弱、动量、宽度、成交、风险与置信度。
4. `scoring.py` 按 `config/scoring.default.yaml` 计算可解释评分和贡献拆解。
5. `phase.py` 输出轮动阶段与阶段迁移。
6. `strategy_lab.py` 调用 `backtest.py` 生成 Top-N 行业轮动历史模拟。
7. `render.py` 注入 report JSON，生成可独立打开的静态页面。

## CLI

```bash
python3 -m rollingold.breadth --output data/state/breadth_history.json
python3 -m rollingold.site --mode data --refresh-cache --output reports/latest.json
python3 -m rollingold.site --output docs/index.html
python3 -m rollingold.site --offline-fixture tests/fixtures --output /tmp/rollingold-fixture.html
python3 -m rollingold.site --mode panel --output data/history/signal_panel_daily.csv
python3 -m rollingold.site --mode backtest --output data/history/backtest_summary.json
```

`--mode data` 会同步写出 `data/history/signal_panel_daily.csv`、`data/history/signal_panel_weekly.csv` 和 `reports/history/YYYY-MM-DD.json`。

## 质量与可访问性检查建议

基础门禁：

```bash
python3 -m pytest
python3 -m rollingold.site --offline-fixture tests/fixtures --output /tmp/rollingold-fixture.html
```

浏览器检查：

- 页面首屏能加载，无 JavaScript 运行时错误。
- 日线 / 周线切换后 URL query 同步变化。
- 行业点、榜单、今日变化点击后行业详情更新。
- ETF tab 可切换并渲染走势图和表格。
- 移动端横向滚动区域不遮挡核心内容。

公开发布前建议增加 Lighthouse 或等价检查，重点看：

- color contrast
- keyboard navigation
- heading order
- button accessible name
- mobile viewport layout
