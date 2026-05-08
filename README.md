# Rollingold

Rollingold 是一个面向盘后研究的行业轮动静态页面。第一版组合三类信号：

- 价格相对轮动：申万一级行业相对默认基准 `801003` 申万 A 指的相对强弱和动量。
- 市场宽度确认：大盘云图二级行业 MA20 站上率聚合到 26 个页面行业。
- 综合评分排序：价格、动量、宽度、宽度改善和成交确认合成 0-100 分。

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

离线 fixture 生成：

```bash
python3 -m rollingold.site --offline-fixture tests/fixtures --output docs/index.html
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
