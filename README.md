# Rollingold

Rollingold 是一个面向 A 股行业/板块轮动的静态研究工作台。页面用于盘后研究、信号解释和历史模拟，不输出个股推荐、不生成自动交易指令、不承诺收益。

核心功能：

- 价格相对轮动：申万一级行业相对默认基准 `801003` 申万 A 指的相对强弱和动量。
- 市场宽度确认：大盘云图二级行业 MA20 站上率聚合到 26 个页面行业。
- 可解释评分排序：趋势、动量、宽度、成交、风险和数据质量合成 0-100 分，并展示分数贡献。
- 轮动阶段：低位修复、价格确认、趋势扩散、高位背离、动能衰退、弱势下行。
- 数据质量：拆分价格、宽度、ETF 日期和接口状态。
- 策略实验室：Top-N 行业轮动历史模拟，计入交易成本并明确标注“历史模拟，不代表未来收益”。

页面是纯静态文件，目标发布路径为 `docs/index.html`，适合 GitHub Pages 的 `main:/docs` 来源。

## 本地生成

首次使用先安装本地包和测试依赖：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

```bash
python3 -m rollingold.breadth --output data/state/breadth_history.json
python3 -m rollingold.site --mode data --refresh-cache --output reports/latest.json
python3 -m rollingold.site --output docs/index.html
```

离线 fixture 只用于测试页面结构，不代表真实行情；不要用它覆盖发布用的 `docs/index.html` 或 `reports/latest.json`。建议输出到临时文件：

```bash
python3 -m rollingold.site --offline-fixture tests/fixtures --output /tmp/rollingold-fixture.html
```

生成因子面板和回测摘要：

```bash
python3 -m rollingold.site --mode panel --output data/history/signal_panel_daily.csv
python3 -m rollingold.site --mode backtest --output data/history/backtest_summary.json
```

## 测试

```bash
python3 -m pytest
```

如果还没有安装测试依赖，回到首次安装步骤执行：

```bash
python3 -m pip install -e ".[dev]"
```

## 自动更新

```bash
bash scripts/publish_daily.sh
```

脚本会在周一至周五 18:30 后生成当日页面；如果最新交易日没有变化，则跳过提交。生成失败或价格/宽度数据日期未对齐时，不会覆盖上一版 `reports/latest.json` 或 `docs/index.html`。

自动更新脚本会优先使用项目 `.venv/bin/python`，也可以通过 `ROLLINGOLD_PYTHON=/path/to/python` 指定运行环境。盘后更新会强制刷新 AKShare 价格缓存；宽度接口失败时会沿用上一版 `data/state/breadth_history.json` 并在页面数据质量里标注。

安装本机 launchd：

```bash
bash scripts/install_launchd.sh
```

计划任务文件：

```text
~/Library/LaunchAgents/com.spicyclaw.rollingold.daily.plist
```

## 发布

计划公开仓库：

```text
ivanclaw126-design/Rollingold
```

GitHub Pages URL：

```text
https://ivanclaw126-design.github.io/Rollingold/
```

页面只用于研究参考，不构成投资建议。

## 方法与数据源

- [架构说明](docs/architecture.md)
- [方法论](docs/methodology.md)
- [数据源说明](docs/data_sources.md)

数据来自 AKShare 申万行业指数、AKShare ETF 行情和大盘云图公开宽度接口。任何数据源失败、日期不一致或 ETF 近似口径都会在页面数据质量和行业详情中展示。
