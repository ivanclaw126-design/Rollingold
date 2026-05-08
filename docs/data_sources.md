# Rollingold 数据源说明

## 价格数据

- 来源：AKShare `index_hist_sw`
- 口径：申万一级行业指数，默认基准为 `801003` 申万 A 指。
- 必需字段：`日期`、`收盘`、`成交额`
- 失败处理：缓存存在时优先保留上一版可用数据；字段缺失会在测试和生成阶段报错。

## 市场宽度

- 来源：大盘云图公开 MA20 行业宽度接口。
- 口径：接口二级行业映射到 26 个页面行业。
- 必需字段：`dates`、`industries`、`data`
- 失败处理：若接口失败且 `data/state/breadth_history.json` 存在，则沿用上一版并在 `report.meta.data_quality` 和页面数据质量区块标注 `stale`。

## ETF

- 来源：AKShare `fund_etf_spot_em` 与 `fund_etf_hist_em`
- 作用：展示行业 ETF 替代关系、规模、走势一致性和相关性。
- 限制：ETF 不等同于完整行业指数；近似映射会在页面口径说明中展示。

## 日期对齐

报告拆分展示：

- `price_date`
- `breadth_date`
- `etf_date`
- `latest_report_date`
- `date_alignment_status`

当 ETF 是当日实时而行业价格仍为上一交易日时，页面不会只展示一个混合日期。
