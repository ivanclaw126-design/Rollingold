"""Static HTML renderer for Rollingold."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any

from .render_assets import EXTRA_CSS, EXTRA_JS


def render_html(report: dict[str, Any]) -> str:
    data_json = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    generated_at = html.escape(str(report["meta"]["generated_at"]))
    latest_date = html.escape(str(report["meta"]["latest_date"]))
    price_latest_date = html.escape(str(report["meta"].get("price_latest_date", "")))
    etf_latest_date = html.escape(str(report["meta"].get("etf_latest_date", "")))
    quality_payload = report["meta"].get("data_quality", {})
    quality = html.escape(
        str(quality_payload.get("summary", "未知") if isinstance(quality_payload, dict) else quality_payload)
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <title>Rollingold 行业轮动</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f4;
      --surface: #ffffff;
      --ink: #17201c;
      --muted: #66716d;
      --line: #dfe5dc;
      --green: #16885d;
      --red: #c74d42;
      --amber: #c3841d;
      --blue: #2e6fab;
      --panel: #eef3ed;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: "Avenir Next", "Helvetica Neue", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
      letter-spacing: 0;
    }}
    header {{
      padding: 22px 24px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    .topbar {{
      max-width: 1280px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 16px;
      align-items: center;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      line-height: 1.15;
      font-weight: 780;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 5px 10px;
      background: #fbfcfa;
      white-space: nowrap;
    }}
    .switch {{
      display: inline-grid;
      grid-template-columns: 1fr 1fr;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      min-width: 156px;
    }}
    .switch button {{
      border: 0;
      padding: 9px 13px;
      min-height: 44px;
      background: var(--surface);
      color: var(--muted);
      font-weight: 650;
      cursor: pointer;
    }}
    .switch button.active {{
      background: var(--ink);
      color: #fff;
    }}
    .page-tabs {{
      max-width: 1280px;
      margin: 14px auto 0;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .page-tab {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
      color: var(--muted);
      min-height: 40px;
      padding: 8px 12px;
      font-weight: 750;
      cursor: pointer;
    }}
    .page-tab.active {{
      background: var(--ink);
      color: #fff;
      border-color: var(--ink);
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 36px;
      display: grid;
      gap: 18px;
    }}
    .tab-panel {{
      display: grid;
      gap: 18px;
    }}
    .tab-panel[hidden] {{
      display: none;
    }}
    .insight-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .insight-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfa;
      min-width: 0;
    }}
    .insight-card strong {{
      display: block;
      font-size: 28px;
      line-height: 1.1;
      margin-bottom: 4px;
      font-variant-numeric: tabular-nums;
    }}
    .insight-card span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .signal-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .signal-card {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      min-width: 0;
      background: #fff;
    }}
    .signal-title {{
      padding: 9px 10px;
      font-weight: 760;
      font-size: 13px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
    }}
    .signal-title.good {{ background: #e8f5ed; color: var(--green); }}
    .signal-title.watch {{ background: #eef4fb; color: var(--blue); }}
    .signal-title.warn {{ background: #fbf1df; color: #8b5a12; }}
    .signal-title.bad {{ background: #fbebe8; color: var(--red); }}
    .signal-rule {{
      padding: 8px 10px;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
      border-bottom: 1px solid var(--line);
      background: #fbfcfa;
    }}
    .signal-item {{
      width: 100%;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 8px 10px;
      min-height: 44px;
      border-bottom: 1px solid var(--line);
      border-left: 0;
      border-right: 0;
      border-top: 0;
      font-size: 13px;
      cursor: pointer;
      min-width: 0;
      color: inherit;
      background: transparent;
      font: inherit;
      text-align: left;
    }}
    .signal-item:last-child {{ border-bottom: 0; }}
    .signal-item:hover, .signal-item:focus-visible {{ background: #f8faf7; }}
    button:focus-visible, .signal-item:focus-visible, .rank-item:focus-visible {{
      outline: 2px solid var(--green);
      outline-offset: -2px;
    }}
    .signal-item span:first-child {{
      min-width: 0;
      overflow-wrap: anywhere;
      font-weight: 680;
    }}
    .signal-item span:last-child {{
      color: var(--muted);
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
    }}
    section {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      min-width: 0;
    }}
    .section-head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      margin-bottom: 12px;
    }}
    h2 {{
      margin: 0;
      font-size: 17px;
      line-height: 1.25;
    }}
    .hint {{
      margin: 0;
      color: var(--muted);
      font-size: 12px;
    }}
    .method-note {{
      margin: 10px 0 0;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.6;
    }}
    .chart-meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      color: var(--muted);
      font-size: 12px;
    }}
    .chart-meta span {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      background: #fbfcfa;
      white-space: nowrap;
    }}
    .trace-switch {{
      display: inline-grid;
      grid-template-columns: repeat(3, auto);
      border: 1px solid var(--line);
      border-radius: 999px;
      overflow: hidden;
      background: #fbfcfa;
    }}
    .trace-switch button {{
      border: 0;
      border-right: 1px solid var(--line);
      min-height: 28px;
      padding: 4px 9px;
      color: var(--muted);
      background: transparent;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      white-space: nowrap;
    }}
    .trace-switch button:last-child {{
      border-right: 0;
    }}
    .trace-switch button.active {{
      background: var(--ink);
      color: #fff;
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, .65fr);
      gap: 18px;
      align-items: start;
    }}
    .rotation-scroll {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    #rotation-svg {{
      width: 100%;
      aspect-ratio: 12 / 7;
      display: block;
      background: #fbfcfa;
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    .detail {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 324px;
    }}
    .detail h3 {{
      margin: 0 0 8px;
      font-size: 20px;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin: 12px 0;
    }}
    .metric {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      min-width: 0;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 4px;
    }}
    .metric strong {{
      display: block;
      font-size: 17px;
      line-height: 1.2;
      overflow-wrap: anywhere;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin: 10px 0;
    }}
    .tag {{
      font-size: 12px;
      border-radius: 999px;
      padding: 4px 8px;
      background: #fff;
      border: 1px solid var(--line);
    }}
    .rankings {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
    }}
    .rank-list {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      min-width: 0;
    }}
    .rank-title {{
      background: var(--panel);
      padding: 9px 10px;
      font-weight: 720;
      font-size: 13px;
    }}
    .rank-item {{
      width: 100%;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 9px 10px;
      min-height: 44px;
      border-top: 1px solid var(--line);
      border-left: 0;
      border-right: 0;
      border-bottom: 0;
      font-size: 13px;
      cursor: pointer;
      min-width: 0;
      color: inherit;
      background: transparent;
      font: inherit;
      text-align: left;
    }}
    .rank-item span {{
      min-width: 0;
      overflow-wrap: anywhere;
    }}
    .rank-item:hover, .rank-item:focus-visible {{
      background: #f8faf7;
    }}
    .score {{
      font-variant-numeric: tabular-nums;
      font-weight: 760;
    }}
    .heatmap-wrap {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: inset -16px 0 18px -22px rgba(23, 32, 28, .65);
    }}
    .heatmap-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .text-button {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
      color: var(--ink);
      padding: 6px 10px;
      min-height: 44px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .text-button:hover {{
      background: var(--panel);
    }}
    .text-button.active {{
      background: var(--ink);
      color: #fff;
      border-color: var(--ink);
    }}
    table {{
      width: max-content;
      min-width: max(100%, 940px);
      border-collapse: collapse;
      font-size: 12px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      border-right: 1px solid var(--line);
      padding: 6px;
      text-align: center;
      white-space: nowrap;
    }}
    th:first-child, td:first-child {{
      position: sticky;
      left: 0;
      background: #fff;
      z-index: 1;
      text-align: left;
      font-weight: 700;
    }}
    .heatmap-status {{
      font-weight: 720;
      color: var(--muted);
    }}
    .trend-cell {{
      width: 112px;
      min-width: 112px;
    }}
    .heatmap-delta.positive {{ color: var(--green); font-weight: 760; }}
    .heatmap-delta.negative {{ color: var(--red); font-weight: 760; }}
    .etf-controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      justify-content: flex-end;
    }}
    .window-switch {{
      display: inline-grid;
      grid-template-columns: repeat(4, auto);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #fbfcfa;
    }}
    .window-switch button {{
      border: 0;
      border-right: 1px solid var(--line);
      min-height: 36px;
      padding: 6px 10px;
      background: transparent;
      color: var(--muted);
      font-weight: 750;
      cursor: pointer;
    }}
    .window-switch button:last-child {{ border-right: 0; }}
    .window-switch button.active {{
      background: var(--ink);
      color: #fff;
    }}
    .etf-chart-scroll {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }}
    #etf-chart {{
      width: 100%;
      min-width: 820px;
      aspect-ratio: 16 / 7;
      display: block;
      background: #fbfcfa;
      border: 1px solid var(--line);
      border-radius: 6px;
    }}
    .etf-line-hit,
    .etf-end-label {{
      cursor: pointer;
    }}
    .etf-line-hit:focus-visible,
    .etf-end-label:focus-visible {{
      outline: none;
    }}
    .etf-line-hit:focus-visible + .etf-line-visible {{
      stroke-width: 3.2;
      opacity: .96;
    }}
    .etf-end-label text {{
      paint-order: stroke;
      stroke: #fbfcfa;
      stroke-width: 3px;
      stroke-linejoin: round;
    }}
    .etf-summary {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin-bottom: 12px;
    }}
    .etf-summary .metric {{
      background: #fbfcfa;
    }}
    .etf-table-wrap {{
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .etf-table-wrap tr.selected td {{
      background: #eef3ed;
    }}
    .etf-row {{
      cursor: pointer;
    }}
    .etf-row:hover td {{
      background: #f8faf7;
    }}
    .consistency-pill {{
      display: inline-block;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 7px;
      background: #fff;
      font-weight: 760;
    }}
    .consistency-pill.good {{ color: var(--green); border-color: #acd8c3; }}
    .consistency-pill.mid {{ color: var(--blue); border-color: #b9d0e5; }}
    .consistency-pill.bad {{ color: var(--red); border-color: #e5b9b4; }}
    .sparkline {{
      width: 96px;
      height: 24px;
      display: block;
      margin: 0 auto;
    }}
    {EXTRA_CSS}
    footer {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
      padding: 4px 2px 0;
    }}
    .dot-label {{
      font-size: 12px;
      dominant-baseline: middle;
      pointer-events: none;
      paint-order: stroke;
      stroke: #fbfcfa;
      stroke-width: 4px;
      stroke-linejoin: round;
    }}
    .dot-label.selected {{
      font-size: 15px;
      font-weight: 800;
    }}
    .industry-dot:focus-visible .dot-label {{
      paint-order: stroke;
      stroke: #fff;
      stroke-width: 4px;
      font-weight: 800;
    }}
    .axis-label {{
      font-size: 12px;
      fill: #66716d;
    }}
    @media (max-width: 900px) {{
      header {{ padding: 18px 14px; }}
      .topbar {{ grid-template-columns: 1fr; }}
      main {{ padding: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
      .insight-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .signal-grid {{ grid-template-columns: 1fr; }}
      .rankings {{ grid-template-columns: 1fr; }}
      .etf-summary {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      h1 {{ font-size: 24px; }}
      .section-head {{ align-items: flex-start; flex-direction: column; }}
      .rotation-scroll {{
        margin-right: -2px;
        padding-bottom: 4px;
      }}
      #rotation-svg {{
        min-width: 640px;
        aspect-ratio: 12 / 7;
      }}
      table {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="topbar">
      <div>
        <h1>Rollingold 行业轮动</h1>
        <div class="meta">
          <span class="pill">最新数据日：{latest_date}</span>
          <span class="pill">行业价格：{price_latest_date}</span>
          <span class="pill">ETF：{etf_latest_date}</span>
          <span class="pill">生成时间：{generated_at}</span>
          <span class="pill">数据质量：{quality}</span>
        </div>
      </div>
      <div class="switch" aria-label="周期切换">
        <button id="mode-daily" class="active" type="button">日线</button>
        <button id="mode-weekly" type="button">周线</button>
      </div>
    </div>
    <div class="page-tabs" role="tablist" aria-label="页面切换">
      <button id="tab-rotation" class="page-tab active" data-tab="rotation" type="button" role="tab" aria-controls="panel-rotation" aria-selected="true">行业轮动</button>
      <button id="tab-etf" class="page-tab" data-tab="etf" type="button" role="tab" aria-controls="panel-etf" aria-selected="false">ETF 业绩</button>
    </div>
  </header>
  <main>
    <div id="panel-rotation" class="tab-panel" role="tabpanel" aria-labelledby="tab-rotation">
    <section>
      <div class="section-head">
        <h2>行业轮动判断</h2>
        <div class="action-row">
          <p class="hint">先看价格强弱，再用宽度扩散验证趋势质量。</p>
          <button class="text-button" id="copy-view-link" type="button">复制当前视图链接</button>
          <button class="text-button" id="reset-view" type="button">恢复默认</button>
          <button class="text-button" id="download-report" type="button">下载当前 report JSON</button>
          <button class="text-button" id="download-factor-csv" type="button">下载因子 CSV</button>
        </div>
      </div>
      <div class="insight-grid" id="market-insights"></div>
      <div class="signal-grid" id="signal-groups"></div>
      <p class="method-note">口径：价格相对轮动使用行业相对申万 A 指的强弱 z-score 和动量 z-score；MA20 宽度为行业内成分站上 20 日均线比例，1 日 / 5 日变化均为百分点变化。</p>
    </section>

    <section>
      <div class="section-head">
        <h2>今日变化</h2>
        <p class="hint">展示阶段迁移、分数变化和主要触发原因。</p>
      </div>
      <div class="change-list" id="change-log"></div>
    </section>

    <div class="grid">
      <section>
        <div class="section-head">
          <h2>价格相对轮动图</h2>
          <div class="chart-meta">
            <span id="history-label">最近 20 个交易日</span>
            <div class="trace-switch" aria-label="轨迹范围切换">
              <button class="active" data-trace-mode="20" type="button">20日</button>
              <button data-trace-mode="60" type="button">60日</button>
              <button data-trace-mode="latest" type="button">仅点位</button>
            </div>
            <span>横轴相对强弱，纵轴相对动量</span>
          </div>
        </div>
        <div class="rotation-scroll" aria-label="行业四象限轮动图，窄屏可横向滑动查看">
          <svg id="rotation-svg" viewBox="0 0 720 420" role="img" aria-label="行业四象限轮动图"></svg>
        </div>
      </section>
      <section class="detail" id="detail-panel" aria-label="行业详情"></section>
    </div>

    <section>
      <div class="section-head">
        <h2>综合评分榜</h2>
        <p class="hint">评分由价格、动量、宽度、宽度改善和成交确认合成，范围 0-100。</p>
      </div>
      <div class="rankings" id="rankings"></div>
      <p class="method-note">评分口径：价格相对强弱 30%，相对动量 25%，MA20 宽度 20%，5 日宽度改善 15%，成交额占比是否高于 20 日均值 10%。分组口径：当前强势取综合评分前列，边际改善 / 恶化按 5 日宽度变化排序，弱势修复偏向走强象限，走弱预警偏向走弱象限或强势放缓。</p>
    </section>

    <section>
      <div class="section-head">
        <h2>市场宽度热力图</h2>
        <div class="heatmap-actions">
          <p class="hint" id="heatmap-hint">默认展示最近 10 个交易日，按当前 MA20 宽度排序；窄屏可横向滑动。</p>
          <div class="mini-controls" aria-label="热力图排序">
            <button class="text-button" data-heatmap-sort="score" type="button">按分数</button>
            <button class="text-button" data-heatmap-sort="breadth" type="button">按宽度</button>
            <button class="text-button" data-heatmap-sort="phase" type="button">按阶段</button>
          </div>
          <div class="mini-controls" aria-label="热力图时间范围">
            <button class="text-button" data-heatmap-window="10" type="button">近10日</button>
            <button class="text-button" data-heatmap-window="30" type="button">近30日</button>
            <button class="text-button" data-heatmap-window="all" type="button">全部</button>
          </div>
        </div>
      </div>
      <div class="heatmap-wrap" id="heatmap"></div>
    </section>

    <section>
      <div class="section-head">
        <h2>数据质量</h2>
        <p class="hint">拆分价格、宽度和 ETF 数据状态，避免把接口失败隐藏成单一日期。</p>
      </div>
      <div class="quality-grid" id="quality-grid"></div>
    </section>

    <section>
      <div class="section-head">
        <h2>策略实验室</h2>
        <p class="hint">Top-N 行业轮动历史模拟；历史模拟，不代表未来收益。</p>
      </div>
      <div class="strategy-grid" id="strategy-lab"></div>
      <div class="etf-chart-scroll" aria-label="策略实验室净值和回撤曲线，窄屏可横向滑动查看">
        <svg id="strategy-chart" viewBox="0 0 960 360" role="img" aria-label="策略实验室净值和回撤曲线"></svg>
      </div>
      <p class="method-note">策略仅用于验证信号与规划观察框架，默认使用申万行业指数收益、下一交易日执行和交易成本，不使用 ETF 收益。</p>
    </section>

    <footer>
      数据来源：AKShare 申万一级行业指数、大盘云图 MA20 行业宽度接口。行业口径为“宽度行业口径 + 申万价格口径映射”，合成行业使用等权平均。页面仅供研究参考，不构成投资建议。
      <a href="methodology.md">方法论</a> · <a href="data_sources.md">数据源说明</a>
    </footer>
    </div>

    <div id="panel-etf" class="tab-panel" role="tabpanel" aria-labelledby="tab-etf" hidden>
      <section>
        <div class="section-head">
          <div>
            <h2>行业 ETF 归一化业绩</h2>
            <p class="hint" id="etf-hint">按当前行业口径选取每个行业规模最大的对应场内 ETF。</p>
          </div>
          <div class="etf-controls">
            <div class="window-switch" aria-label="ETF 走势图时间范围">
              <button class="active" data-etf-window="20" type="button">20日</button>
              <button data-etf-window="60" type="button">60日</button>
              <button data-etf-window="120" type="button">120日</button>
              <button data-etf-window="240" type="button">240日</button>
            </div>
          </div>
        </div>
        <div class="etf-summary" id="etf-summary"></div>
        <div class="etf-chart-scroll" aria-label="行业 ETF 归一化业绩走势图，窄屏可横向滑动查看">
          <svg id="etf-chart" viewBox="0 0 960 420" role="img" aria-label="行业 ETF 归一化业绩走势图"></svg>
        </div>
        <p class="method-note">归一化口径：所选时间窗口第一个有效收盘价记为 0%，后续展示累计涨跌幅；走势一致性用 ETF 与对应页面行业指数最近 120 个共同交易日的日收益相关系数和同涨跌比例判断。</p>
      </section>
      <section>
        <div class="section-head">
          <h2>ETF 对应关系与一致性</h2>
          <p class="hint">点击表格行可高亮走势图；“近似”行业会在备注中说明口径差异。</p>
        </div>
        <div class="etf-table-wrap" id="etf-table"></div>
      </section>
      <footer>
        ETF 行情来源：AKShare 东方财富 ETF 实时行情与历史行情接口；规模按当前总市值口径排序。页面仅供研究参考，不构成投资建议。
      </footer>
    </div>
  </main>
  <script>
    const DATA = {data_json};
    {EXTRA_JS}
    const initialParams = new URLSearchParams(window.location.search);
    const storedState = (() => {{
      try {{ return JSON.parse(localStorage.getItem('rollingold:view') || '{{}}'); }}
      catch (_) {{ return {{}}; }}
    }})();
    let activeTab = initialParams.get('tab') || storedState.tab || 'rotation';
    let mode = initialParams.get('period') === 'weekly' ? 'weekly' : (storedState.mode || 'daily');
    let selected = initialParams.get('industry') || storedState.industry || DATA.industries[0]?.name;
    let selectedEtf = storedState.etf || DATA.etfs?.items?.[0]?.code;
    let etfWindow = Number(storedState.etfWindow || 20);
    let hovered = null;
    let traceMode = initialParams.get('trace') || storedState.trace || '20';
    let heatmapSort = initialParams.get('sort') || storedState.sort || 'breadth';
    let heatmapWindow = initialParams.get('heatmap') || storedState.heatmap || '10';

    const colorMap = {{
      '领涨': '#16885d',
      '走强': '#2e6fab',
      '走弱': '#c3841d',
      '领跌': '#c74d42'
    }};

    function activePoint(item) {{
      if (mode === 'weekly') {{
        return {{
          x: item.weekly.price_x,
          y: item.weekly.momentum_y,
          quadrant: item.weekly.quadrant,
          path: item.path_weekly
        }};
      }}
      return {{
        x: item.price_x,
        y: item.momentum_y,
        quadrant: item.quadrant,
        path: item.path_daily
      }};
    }}

    function restoreFocus(focusKey) {{
      if (!focusKey) return;
      const node = document.querySelector(`[data-focus-key="${{focusKey}}"]`);
      node?.focus({{ preventScroll: true }});
    }}

    function selectIndustry(name, focusKey) {{
      if (selected === name) {{
        restoreFocus(focusKey);
        return;
      }}
      selected = name;
      saveState();
      renderAll();
      restoreFocus(focusKey);
    }}

    function saveState(updateUrl = true) {{
      const payload = {{ tab: activeTab, mode, industry: selected, trace: traceMode, sort: heatmapSort, heatmap: heatmapWindow, etf: selectedEtf, etfWindow }};
      localStorage.setItem('rollingold:view', JSON.stringify(payload));
      if (!updateUrl) return;
      const params = new URLSearchParams();
      params.set('period', mode);
      params.set('score', DATA.methodology?.score_preset || 'balanced_v2');
      params.set('trace', traceMode);
      params.set('sort', heatmapSort);
      params.set('industry', selected || '');
      if (activeTab !== 'rotation') params.set('tab', activeTab);
      const next = `${{window.location.pathname}}?${{params.toString()}}${{window.location.hash}}`;
      window.history.replaceState(null, '', next);
    }}

    function onIndustryKey(event, name, focusKey) {{
      if (event.key !== 'Enter' && event.key !== ' ') return;
      event.preventDefault();
      selectIndustry(name, focusKey);
    }}

    function bindIndustryControl(node) {{
      const pick = () => selectIndustry(node.dataset.name, node.dataset.focusKey);
      node.addEventListener('click', pick);
      node.addEventListener('focus', pick);
      node.addEventListener('keydown', event => onIndustryKey(event, node.dataset.name, node.dataset.focusKey));
    }}

    function clamp(value, low, high) {{ return Math.max(low, Math.min(high, value)); }}
    function currentPoints() {{
      return DATA.industries.map(item => ({{ item, point: activePoint(item) }}));
    }}
    function chartLimit(points, selectedPoint) {{
      const values = [];
      points.forEach(entry => values.push(Math.abs(entry.point.x), Math.abs(entry.point.y)));
      (selectedPoint.path || []).forEach(point => values.push(Math.abs(point.x), Math.abs(point.y)));
      const raw = Math.max(1.2, ...values.filter(Number.isFinite));
      return Math.min(3.4, Math.ceil((raw + 0.25) * 10) / 10);
    }}
    function scaleX(x, limit) {{ return 360 + clamp(x, -limit, limit) * (292 / limit); }}
    function scaleY(y, limit) {{ return 210 - clamp(y, -limit, limit) * (152 / limit); }}
    function traceUnit() {{ return mode === 'weekly' ? '周' : '交易日'; }}
    function traceWindow() {{
      if (mode === 'weekly') return traceMode === '60' ? 26 : 8;
      return traceMode === '60' ? 60 : 20;
    }}
    function traceLabel() {{
      if (traceMode === 'latest') return '仅显示最新位置';
      return mode === 'weekly' ? `最近 ${{traceWindow()}} 周` : `最近 ${{traceWindow()}} 个交易日`;
    }}
    function traceModeLabel(value) {{
      if (value === 'latest') return '仅点位';
      if (mode === 'weekly') return value === '60' ? '26周' : '8周';
      return value === '60' ? '60日' : '20日';
    }}
    function displayPath(points) {{
      const source = points || [];
      if (!source.length) return [];
      if (traceMode === 'latest') return [];
      return source.slice(-traceWindow());
    }}
    function hexToRgb(hex) {{
      const normalized = hex.replace('#', '');
      return [
        parseInt(normalized.slice(0, 2), 16),
        parseInt(normalized.slice(2, 4), 16),
        parseInt(normalized.slice(4, 6), 16)
      ];
    }}
    function mixColor(from, to, ratio) {{
      const start = hexToRgb(from);
      const end = hexToRgb(to);
      const channel = index => Math.round(start[index] + (end[index] - start[index]) * ratio);
      return `rgb(${{channel(0)}}, ${{channel(1)}}, ${{channel(2)}})`;
    }}
    function lineSegments(points, limit, options = {{}}) {{
      if (!points || points.length < 2) return '';
      const startColor = options.startColor || '#d6eee3';
      const endColor = options.endColor || '#16885d';
      const opacityStart = options.opacityStart ?? .18;
      const opacityEnd = options.opacityEnd ?? .88;
      const widthStart = options.widthStart ?? 1.2;
      const widthEnd = options.widthEnd ?? 2.8;
      const dash = options.dash ? ` stroke-dasharray="${{options.dash}}"` : '';
      return points.slice(1).map((point, index) => {{
        const previous = points[index];
        const ratio = (index + 1) / Math.max(1, points.length - 1);
        const opacity = opacityStart + (opacityEnd - opacityStart) * ratio;
        const width = widthStart + (widthEnd - widthStart) * ratio;
        return `<line x1="${{scaleX(previous.x, limit)}}" y1="${{scaleY(previous.y, limit)}}" x2="${{scaleX(point.x, limit)}}" y2="${{scaleY(point.y, limit)}}" stroke="${{mixColor(startColor, endColor, ratio)}}" stroke-width="${{width.toFixed(2)}}" opacity="${{opacity.toFixed(2)}}" stroke-linecap="round"${{dash}}></line>`;
      }}).join('');
    }}
    function renderRotation() {{
      const svg = document.getElementById('rotation-svg');
      const selectedItem = DATA.industries.find(item => item.name === selected) || DATA.industries[0];
      const focusName = hovered || selected;
      const focusItem = DATA.industries.find(item => item.name === focusName) || selectedItem;
      const focusPoint = activePoint(focusItem);
      const points = currentPoints();
      const limit = chartLimit(points, focusPoint);
      const ticks = [-limit, -limit / 2, 0, limit / 2, limit];
      const labels = [
        ['走强', 214, 134], ['领涨', 506, 134], ['领跌', 214, 286], ['走弱', 506, 286]
      ];
      const focusPathPoints = displayPath(focusPoint.path);
      const focusStart = focusPathPoints[0];
      const focusEnd = focusPathPoints[focusPathPoints.length - 1];
      svg.innerHTML = `
        <rect x="0" y="0" width="720" height="420" fill="#fbfcfa"></rect>
        <rect x="68" y="58" width="292" height="152" fill="#f2f7f3" opacity=".72"></rect>
        <rect x="360" y="58" width="292" height="152" fill="#eef6f1" opacity=".85"></rect>
        <rect x="68" y="210" width="292" height="152" fill="#fbf1ef" opacity=".65"></rect>
        <rect x="360" y="210" width="292" height="152" fill="#fbf5e9" opacity=".70"></rect>
        ${{ticks.map(tick => `
          <line x1="${{scaleX(tick, limit)}}" y1="58" x2="${{scaleX(tick, limit)}}" y2="362" stroke="#d8e0da" stroke-width="${{tick === 0 ? 1.8 : 1}}"></line>
          <line x1="68" y1="${{scaleY(tick, limit)}}" x2="652" y2="${{scaleY(tick, limit)}}" stroke="#d8e0da" stroke-width="${{tick === 0 ? 1.8 : 1}}"></line>
          <text class="axis-label" x="${{scaleX(tick, limit)}}" y="382" text-anchor="middle">${{tick.toFixed(1)}}</text>
          <text class="axis-label" x="50" y="${{scaleY(tick, limit) + 4}}" text-anchor="end">${{tick.toFixed(1)}}</text>
        `).join('')}}
        <text class="axis-label" x="608" y="402">相对强弱</text>
        <text class="axis-label" x="76" y="42">相对动量</text>
        ${{labels.map(([text,x,y]) => `<text x="${{x}}" y="${{y}}" fill="#66716d" font-size="34" font-weight="850" opacity=".34" text-anchor="middle" dominant-baseline="middle">${{text}}</text>`).join('')}}
        ${{lineSegments(focusPathPoints, limit, {{ startColor: '#a9beb6', endColor: '#143b31', opacityStart: .42, opacityEnd: .80, widthStart: 1.55, widthEnd: 2.9 }})}}
        ${{focusStart ? `<circle cx="${{scaleX(focusStart.x, limit)}}" cy="${{scaleY(focusStart.y, limit)}}" r="4" fill="#fff" stroke="#143b31" stroke-width="1.6" opacity=".82"></circle>` : ''}}
        ${{focusEnd ? `<circle cx="${{scaleX(focusEnd.x, limit)}}" cy="${{scaleY(focusEnd.y, limit)}}" r="7.5" fill="none" stroke="#143b31" stroke-width="2.2"></circle>` : ''}}
        ${{points.map(({{ item, point }}) => {{
          const color = colorMap[point.quadrant] || '#66716d';
          const isSelected = item.name === selected;
          const isFocused = item.name === focusName;
          const heat = Math.max(0, Math.min(1, (item.amount_share || 0) * 16));
          const radius = isSelected ? 9 : (isFocused ? 8 : 5 + heat * 4);
          const opacity = Math.max(.42, Math.min(1, item.confidence || .75));
          const x = scaleX(point.x, limit);
          const y = scaleY(point.y, limit);
          const labelX = clamp(x + 10, 78, 638);
          const labelY = clamp(y + 4, 66, 354);
          return `<g class="industry-dot" data-name="${{item.name}}" data-focus-key="dot-${{item.rank}}" role="button" tabindex="0" aria-label="选择${{item.name}}" style="cursor:pointer">
            <title>${{item.name}}｜${{item.phase}}｜强弱 ${{fmt(point.x)}}｜动量 ${{fmt(point.y)}}｜评分 ${{fmt(item.score)}}｜宽度 ${{fmt(item.breadth_ma20)}}｜成交 ${{fmt((item.amount_share || 0) * 100)}}%｜风险 ${{signedPct((item.risk?.vol_20 || 0) * 100)}}</title>
            <rect x="${{x - 22}}" y="${{y - 22}}" width="44" height="44" fill="transparent"></rect>
            <circle cx="${{x}}" cy="${{y}}" r="${{radius}}" fill="${{color}}" stroke="${{isFocused ? '#17201c' : '#fff'}}" stroke-width="${{isSelected || isFocused ? 2.4 : 1.5}}" opacity="${{hovered && !isFocused ? .46 : opacity}}"></circle>
            <text class="dot-label ${{isSelected ? 'selected' : ''}}" x="${{labelX}}" y="${{labelY}}" fill="#17201c">${{item.name}}</text>
          </g>`;
        }}).join('')}}
      `;
      svg.onpointermove = event => {{
        const node = event.target.closest?.('.industry-dot');
        const next = node?.dataset.name || null;
        if (next && next !== hovered) {{
          hovered = next;
          renderRotation();
        }}
      }};
      svg.onpointerleave = () => {{
        if (!hovered) return;
        hovered = null;
        renderRotation();
      }};
      svg.querySelectorAll('.industry-dot').forEach(node => {{
        bindIndustryControl(node);
      }});
    }}

    function breakdownHtml(item) {{
      const labels = {{ trend: '趋势', momentum: '动量', breadth: '宽度', liquidity: '成交', risk: '风险', data_quality: '数据' }};
      const entries = Object.entries(item.score_breakdown || {{}}).filter(([key]) => key !== 'total');
      return `<div class="breakdown-list">${{entries.map(([key, value]) => {{
        const width = Math.min(100, Math.abs(Number(value) || 0) * 1.6);
        return `<div class="breakdown-row"><span>${{labels[key] || key}}</span><span class="breakdown-track"><span class="breakdown-fill ${{value < 0 ? 'negative' : ''}}" style="width:${{width}}%"></span></span><strong>${{fmt(value)}}</strong></div>`;
      }}).join('')}}</div>`;
    }}

    function renderDetail() {{
      const item = DATA.industries.find(entry => entry.name === selected) || DATA.industries[0];
      const point = activePoint(item);
      document.getElementById('detail-panel').innerHTML = `
        <h3>${{item.name}}</h3>
        <div class="tags">
          <span class="tag">${{point.quadrant}}</span>
          <span class="tag">${{item.phase}}</span>
          <span class="tag">${{item.status}}</span>
          <span class="tag">成交${{item.amount_confirm ? '确认' : '偏弱'}}</span>
          <span class="tag">置信度 ${{fmt((item.confidence || 0) * 100)}}%</span>
        </div>
        <div class="detail-grid">
          <div class="metric"><span>综合评分</span><strong>${{fmt(item.score)}}</strong></div>
          <div class="metric"><span>分数变化</span><strong>${{signed(item.score_delta_1d)}}</strong></div>
          <div class="metric"><span>MA20 宽度</span><strong>${{fmt(item.breadth_ma20)}}%</strong></div>
          <div class="metric"><span>1 日变化</span><strong>${{signed(item.breadth_delta_1d)}}</strong></div>
          <div class="metric"><span>5 日变化</span><strong>${{signed(item.breadth_delta_5d)}}</strong></div>
          <div class="metric"><span>相对强弱</span><strong>${{fmt(point.x)}}</strong></div>
          <div class="metric"><span>相对动量</span><strong>${{fmt(point.y)}}</strong></div>
          <div class="metric"><span>20日波动</span><strong>${{signedPct((item.risk?.vol_20 || 0) * 100)}}</strong></div>
        </div>
        <h2>分数贡献</h2>
        ${{breakdownHtml(item)}}
        <p>${{item.comment}}</p>
        <p class="muted-block">${{item.interpretation}}</p>
        <button class="text-button" id="copy-industry-summary" type="button">复制行业详情摘要</button>
        <div class="tags">${{item.divergences.map(text => `<span class="tag">${{text}}</span>`).join('')}}</div>
        <h2>口径说明</h2>
        <p class="muted-block">${{item.methodology_note}}</p>
        <h2>数据质量</h2>
        <p class="muted-block">${{item.data_quality?.message || '-'}}；价格：${{item.data_quality?.price}}，宽度：${{item.data_quality?.breadth}}，ETF：${{item.data_quality?.etf}}。</p>
      `;
      document.getElementById('copy-industry-summary')?.addEventListener('click', event => {{
        safeCopy(`${{item.name}}：当前处于「${{item.phase}}」，综合评分 ${{fmt(item.score)}}。${{item.interpretation}} 口径：${{item.methodology_note}}`).then(() => {{
          event.currentTarget.textContent = '已复制行业摘要';
        }});
      }});
    }}

    function renderRankings() {{
      const groups = [
        ['当前强势行业', DATA.rankings.top_strength],
        ['边际改善行业', DATA.rankings.improving],
        ['边际恶化行业', DATA.rankings.deteriorating],
        ['弱势修复行业', DATA.rankings.weak_repair],
        ['走弱预警行业', DATA.rankings.slowing]
      ];
      document.getElementById('rankings').innerHTML = groups.map(([title, items], groupIndex) => `
        <div class="rank-list">
          <div class="rank-title">${{title}}</div>
          ${{items.map((name, itemIndex) => {{
            const item = DATA.industries.find(entry => entry.name === name);
            return `<button class="rank-item" data-name="${{name}}" data-focus-key="rank-${{groupIndex}}-${{itemIndex}}" type="button" aria-label="选择${{name}}"><span>${{name}}</span><span class="score">${{fmt(item?.score)}}</span></button>`;
          }}).join('') || '<div class="rank-item"><span>暂无</span><span></span></div>'}}
        </div>
      `).join('');
      document.querySelectorAll('.rank-item[data-name]').forEach(node => {{
        bindIndustryControl(node);
      }});
    }}

    function signalBuckets() {{
      const items = DATA.industries.map(item => {{
        const point = activePoint(item);
        return {{ ...item, activeQuadrant: point.quadrant, activeX: point.x, activeY: point.y }};
      }});
      const strong = items
        .filter(item => item.activeQuadrant === '领涨' && item.breadth_ma20 >= 65 && item.breadth_delta_5d >= 0)
        .sort((a, b) => b.score - a.score);
      const early = items
        .filter(item => item.breadth_delta_5d >= 8 && (item.activeQuadrant === '走强' || item.activeQuadrant === '领跌'))
        .sort((a, b) => (b.breadth_delta_5d || 0) - (a.breadth_delta_5d || 0));
      const cooling = items
        .filter(item => item.breadth_ma20 >= 60 && (item.breadth_delta_5d || 0) < 0)
        .sort((a, b) => (a.breadth_delta_5d || 0) - (b.breadth_delta_5d || 0));
      const weak = items
        .filter(item => item.breadth_ma20 < 45 && item.activeQuadrant === '领跌')
        .sort((a, b) => a.score - b.score);
      return {{ strong, early, cooling, weak, items }};
    }}

    function renderMarketInsights() {{
      const buckets = signalBuckets();
      const breadthValues = buckets.items.map(item => item.breadth_ma20).filter(Number.isFinite);
      const avg = DATA.breadth.latest_market_average ?? (
        breadthValues.length ? breadthValues.reduce((sum, value) => sum + value, 0) / breadthValues.length : null
      );
      const above70 = buckets.items.filter(item => item.breadth_ma20 >= 70).length;
      const below30 = buckets.items.filter(item => item.breadth_ma20 < 30).length;
      const improving = buckets.items.filter(item => (item.breadth_delta_1d || 0) > 0).length;
      const worsening = buckets.items.filter(item => (item.breadth_delta_1d || 0) < 0).length;
      document.getElementById('market-insights').innerHTML = [
        [fmt(avg) + '%', '全行业平均 MA20 宽度'],
        [above70, '宽度超过 70% 的行业数'],
        [below30, '宽度低于 30% 的行业数'],
        [`${{improving}} / ${{worsening}}`, '今日改善 / 走弱行业数']
      ].map(([value, label]) => `
        <div class="insight-card"><strong>${{value}}</strong><span>${{label}}</span></div>
      `).join('');
    }}

    function renderSignalGroups() {{
      const buckets = signalBuckets();
      const groups = [
        ['强势扩散', 'good', '领涨象限，MA20 宽度不低于 65%，且 5 日宽度未回落。', buckets.strong, item => `${{fmt(item.breadth_ma20)}}% / ${{signed(item.breadth_delta_5d)}}`],
        ['潜在启动', 'watch', '5 日宽度改善不低于 8 个百分点，且价格仍在走强或领跌修复阶段。', buckets.early, item => `${{item.activeQuadrant}} / ${{signed(item.breadth_delta_5d)}}`],
        ['高位退潮', 'warn', 'MA20 宽度不低于 60%，但 5 日宽度已经转为回落。', buckets.cooling, item => `${{fmt(item.breadth_ma20)}}% / ${{signed(item.breadth_delta_5d)}}`],
        ['弱势回避', 'bad', 'MA20 宽度低于 45%，且价格相对轮动仍在领跌象限。', buckets.weak, item => `${{fmt(item.score)}}分`]
      ];
      document.getElementById('signal-groups').innerHTML = groups.map(([title, tone, rule, items, meta], groupIndex) => `
        <div class="signal-card">
          <div class="signal-title ${{tone}}">${{title}}</div>
          <div class="signal-rule">${{rule}}</div>
          ${{items.slice(0, 5).map((item, itemIndex) => `
            <button class="signal-item" data-name="${{item.name}}" data-focus-key="signal-${{groupIndex}}-${{itemIndex}}" type="button" aria-label="选择${{item.name}}">
              <span>${{item.name}}</span><span>${{meta(item)}}</span>
            </button>
          `).join('') || '<div class="signal-item"><span>暂无</span><span></span></div>'}}
        </div>
      `).join('');
      document.querySelectorAll('.signal-item[data-name]').forEach(node => {{
        bindIndustryControl(node);
      }});
    }}

    function renderChangeLog() {{
      const changes = DATA.change_log || [];
      document.getElementById('change-log').innerHTML = changes.slice(0, 8).map((change, index) => `
        <div class="change-item">
          <button type="button" data-name="${{change.industry}}" data-focus-key="change-${{index}}">${{change.industry}}：${{change.from || '-'}} → ${{change.to || '-'}}</button>
          <p class="muted-block">分数变化 ${{signed(change.score_delta)}}；${{(change.reason || []).join('、')}}</p>
        </div>
      `).join('') || '<div class="change-item">暂无显著变化</div>';
      document.querySelectorAll('.change-item button[data-name]').forEach(node => bindIndustryControl(node));
    }}

    function renderQuality() {{
      const quality = DATA.meta?.data_quality || {{}};
      const sources = quality.sources || [];
      document.getElementById('quality-grid').innerHTML = [
        `<div class="quality-item"><strong>总体：${{quality.summary || '-'}}</strong><p class="muted-block">日期状态：${{DATA.meta?.date_alignment_status || '-'}}；综合置信度 ${{fmt((quality.confidence || 0) * 100)}}%</p></div>`,
        ...sources.map(source => `
          <div class="quality-item">
            <strong>${{source.source}}</strong>
            <p class="muted-block">最新日：${{source.latest_date || '-'}}；行数：${{source.rows ?? '-'}}</p>
            <p class="muted-block">${{source.is_fresh ? 'fresh' : 'stale'}}${{source.stale_reason ? '：' + source.stale_reason : ''}}</p>
          </div>
        `)
      ].join('');
    }}

    function renderStrategyLab() {{
      const lab = DATA.strategy_lab || {{}};
      const results = lab.results || [];
      document.getElementById('strategy-lab').innerHTML = [
        ...results.slice(0, 3).map(result => `
          <div class="strategy-item">
            <strong>Top ${{result.config.top_n}} / ${{result.config.rebalance_days}}D</strong>
            <p class="muted-block">年化 ${{signedPct((result.metrics.annual_return || 0) * 100)}}｜回撤 ${{signedPct((result.metrics.max_drawdown || 0) * 100)}}｜换手 ${{fmt(result.metrics.turnover_average)}}</p>
            <p class="muted-block">当前候选：${{(result.holdings?.at(-1)?.industries || []).join('、') || '-'}}</p>
          </div>
        `),
        `<div class="strategy-item"><strong>参数敏感性</strong><p class="muted-block">${{(lab.sensitivity || []).map(row => `Top${{row.top_n}}/${{row.rebalance_days}}D 回撤 ${{signedPct((row.max_drawdown || 0) * 100)}}`).join('；')}}</p></div>`,
        `<div class="strategy-item"><strong>风险说明</strong><p class="muted-block">${{lab.disclaimer || '研究参考，不构成投资建议；历史模拟，不代表未来收益'}}</p></div>`
      ].join('');
      renderStrategyChart(results[0]);
    }}

    function renderStrategyChart(result) {{
      const svg = document.getElementById('strategy-chart');
      if (!result?.equity_curve?.length) {{
        svg.innerHTML = '<text x="480" y="180" text-anchor="middle" fill="#66716d">暂无策略曲线</text>';
        return;
      }}
      const dates = result.dates || [];
      const equity = result.equity_curve || [];
      const benchmark = result.benchmark_curve || [];
      const drawdown = result.drawdown_curve || [];
      const left = 70, right = 900, top = 42, mid = 178, bottom = 308;
      const allValues = equity.concat(benchmark).filter(Number.isFinite);
      const min = Math.min(...allValues, 1);
      const max = Math.max(...allValues, 1);
      const span = Math.max(.01, max - min);
      const x = index => left + index * ((right - left) / Math.max(1, dates.length - 1));
      const yEq = value => mid - (value - min) * ((mid - top) / span);
      const yDd = value => bottom - (value - Math.min(...drawdown, -.01)) * ((bottom - 210) / Math.max(.01, 0 - Math.min(...drawdown, -.01)));
      const path = (values, y) => values.map((value, index) => `${{x(index).toFixed(1)}},${{y(value).toFixed(1)}}`).join(' ');
      svg.innerHTML = `
        <rect x="0" y="0" width="960" height="360" fill="#fbfcfa"></rect>
        <text class="axis-label" x="70" y="28">策略净值 / 基准净值</text>
        <line x1="${{left}}" y1="${{mid}}" x2="${{right}}" y2="${{mid}}" stroke="#d8e0da"></line>
        <polyline points="${{path(benchmark, yEq)}}" fill="none" stroke="#9ca7a2" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></polyline>
        <polyline points="${{path(equity, yEq)}}" fill="none" stroke="#16885d" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"></polyline>
        <text class="axis-label" x="70" y="202">回撤曲线</text>
        <line x1="${{left}}" y1="210" x2="${{right}}" y2="210" stroke="#d8e0da"></line>
        <polyline points="${{path(drawdown, yDd)}}" fill="none" stroke="#c74d42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"></polyline>
        <text class="axis-label" x="${{left}}" y="338">${{dates[0] || ''}}</text>
        <text class="axis-label" x="${{right}}" y="338" text-anchor="end">${{dates.at(-1) || ''}}</text>
      `;
    }}

    function renderHeatmap() {{
      const requestedWindow = heatmapWindow === 'all' ? DATA.breadth.dates.length : Number(heatmapWindow || 10);
      const windowSize = Math.min(requestedWindow, DATA.breadth.dates.length);
      const dates = DATA.breadth.dates.slice(-windowSize);
      const offset = DATA.breadth.dates.length - dates.length;
      const order = DATA.industries.slice()
        .sort((a, b) => {{
          if (heatmapSort === 'score') return (b.score ?? -1) - (a.score ?? -1);
          if (heatmapSort === 'phase') return String(a.phase || '').localeCompare(String(b.phase || ''));
          return (b.breadth_ma20 ?? -1) - (a.breadth_ma20 ?? -1);
        }})
        .map(item => item.name);
      const indexByName = new Map(DATA.breadth.industries.map((name, index) => [name, index]));
      const trendLabel = heatmapWindow === 'all' ? `趋势(全部${{dates.length}}日)` : `趋势(近${{dates.length}}日)`;
      const header = `<tr><th>行业</th><th>状态</th><th>当前</th><th>1日</th><th>5日</th><th class="trend-cell">${{trendLabel}}</th>${{dates.map(date => `<th>${{date.slice(5)}}</th>`).join('')}}</tr>`;
      const rows = order.map(name => {{
        const item = DATA.industries.find(entry => entry.name === name) || {{}};
        const row = DATA.breadth.values[indexByName.get(name)] || [];
        const recent = row.slice(offset);
        const cells = dates.map((_, idx) => {{
          const value = row[offset + idx];
          return `<td style="background:${{heatColor(value)}}">${{value == null ? '-' : value.toFixed(1)}}</td>`;
        }}).join('');
        return `<tr>
          <td>${{name}}</td>
          <td class="heatmap-status">${{breadthState(item)}}</td>
          <td><strong>${{fmt(item.breadth_ma20)}}%</strong></td>
          <td class="heatmap-delta ${{deltaClass(item.breadth_delta_1d)}}">${{signed(item.breadth_delta_1d)}}</td>
          <td class="heatmap-delta ${{deltaClass(item.breadth_delta_5d)}}">${{signed(item.breadth_delta_5d)}}</td>
          <td class="trend-cell">${{sparkline(recent)}}</td>
          ${{cells}}
        </tr>`;
      }}).join('');
      document.getElementById('heatmap').innerHTML = `<table>${{header}}${{rows}}</table>`;
      document.querySelectorAll('[data-heatmap-sort]').forEach(node => node.classList.toggle('active', node.dataset.heatmapSort === heatmapSort));
      document.querySelectorAll('[data-heatmap-window]').forEach(node => node.classList.toggle('active', node.dataset.heatmapWindow === heatmapWindow));
      document.getElementById('heatmap-hint').textContent = heatmapWindow === 'all'
        ? `已展示全部 ${{dates.length}} 个交易日；窄屏可横向滑动。`
        : `展示最近 ${{dates.length}} 个交易日，当前按${{heatmapSort === 'score' ? '分数' : heatmapSort === 'phase' ? '阶段' : '宽度'}}排序。`;
    }}

    function switchTab(tab) {{
      activeTab = tab;
      document.querySelectorAll('[data-tab]').forEach(node => {{
        const active = node.dataset.tab === tab;
        node.classList.toggle('active', active);
        node.setAttribute('aria-selected', active ? 'true' : 'false');
      }});
      document.getElementById('panel-rotation').hidden = tab !== 'rotation';
      document.getElementById('panel-etf').hidden = tab !== 'etf';
      document.querySelector('.switch').style.visibility = tab === 'rotation' ? 'visible' : 'hidden';
      saveState();
      if (tab === 'etf') renderEtf();
    }}

    function etfItems() {{
      return DATA.etfs?.items || [];
    }}

    function etfSeries(item) {{
      const points = (item.points || []).filter(point => Number.isFinite(point.close)).slice(-etfWindow);
      if (points.length < 2) return [];
      const base = points[0].close;
      if (!base) return [];
      return points.map(point => ({{
        date: point.date,
        close: point.close,
        daily: point.return,
        value: (point.close / base - 1) * 100
      }}));
    }}

    function etfWindowReturn(item) {{
      const series = etfSeries(item);
      return series.length ? series[series.length - 1].value : null;
    }}

    function selectEtf(code, options = {{}}) {{
      const focusKey = options.focusKey;
      if (!code || selectedEtf === code) {{
        restoreFocus(focusKey);
        return;
      }}
      selectedEtf = code;
      if (options.persist) saveState(false);
      renderEtf();
      restoreFocus(focusKey);
    }}

    function etfColor(index) {{
      const palette = ['#16885d', '#2e6fab', '#c3841d', '#8c5fbf', '#c74d42', '#31746f', '#8f6b1c', '#5766a6', '#9b4f62', '#4f7f3f'];
      return palette[index % palette.length];
    }}

    function consistencyClass(label) {{
      if (label === '一致') return 'good';
      if (label === '部分一致') return 'mid';
      return 'bad';
    }}

    function renderEtf() {{
      document.querySelectorAll('[data-etf-window]').forEach(node => {{
        node.classList.toggle('active', Number(node.dataset.etfWindow) === etfWindow);
      }});
      renderEtfSummary();
      renderEtfChart();
      renderEtfTable();
    }}

    function renderEtfSummary() {{
      const items = etfItems();
      const ranked = items
        .map(item => ({{ item, value: etfWindowReturn(item) }}))
        .filter(entry => Number.isFinite(entry.value))
        .sort((a, b) => b.value - a.value);
      const best = ranked[0];
      const worst = ranked[ranked.length - 1];
      const consistent = items.filter(item => item.consistency === '一致').length;
      const spotDate = DATA.etfs?.meta?.spot_date || DATA.etfs?.meta?.latest_date || '-';
      document.getElementById('etf-summary').innerHTML = [
        [items.length, '覆盖行业 ETF 数'],
        [best ? `${{best.item.industry}} ${{signedPct(best.value)}}` : '-', `${{etfWindow}} 日最强`],
        [worst ? `${{worst.item.industry}} ${{signedPct(worst.value)}}` : '-', `${{etfWindow}} 日最弱`],
        [`${{consistent}} / ${{items.length}}`, `走势一致｜规模日 ${{spotDate}}`]
      ].map(([value, label]) => `
        <div class="metric"><span>${{label}}</span><strong>${{value}}</strong></div>
      `).join('');
      document.getElementById('etf-hint').textContent = `按当前行业口径选取每个行业规模最大的对应场内 ETF，当前窗口 ${{etfWindow}} 个交易日。`;
    }}

    function renderEtfChart() {{
      const svg = document.getElementById('etf-chart');
      const series = etfItems().map((item, index) => ({{
        item,
        index,
        points: etfSeries(item)
      }})).filter(entry => entry.points.length > 1);
      if (!series.length) {{
        svg.innerHTML = '<text x="480" y="210" text-anchor="middle" fill="#66716d">暂无 ETF 业绩数据</text>';
        return;
      }}
      const dates = Array.from(new Set(series.flatMap(entry => entry.points.map(point => point.date)))).sort();
      const dateIndex = new Map(dates.map((date, index) => [date, index]));
      const values = series.flatMap(entry => entry.points.map(point => point.value)).filter(Number.isFinite);
      const rawMin = Math.min(0, ...values);
      const rawMax = Math.max(0, ...values);
      const pad = Math.max(1.2, (rawMax - rawMin) * 0.12);
      const min = rawMin - pad;
      const max = rawMax + pad;
      const span = Math.max(1, max - min);
      const left = 70;
      const right = 760;
      const top = 42;
      const bottom = 348;
      const x = date => left + (dateIndex.get(date) || 0) * ((right - left) / Math.max(1, dates.length - 1));
      const y = value => bottom - (value - min) * ((bottom - top) / span);
      const ticks = [min, min + span * .25, min + span * .5, min + span * .75, max];
      const selectedEntry = series.find(entry => entry.item.code === selectedEtf) || series[0];
      selectedEtf = selectedEntry.item.code;
      const drawOrder = series.slice().sort((a, b) => (a.item.code === selectedEtf ? 1 : 0) - (b.item.code === selectedEtf ? 1 : 0));
      const lines = drawOrder.map(entry => {{
        const selectedLine = entry.item.code === selectedEtf;
        const color = selectedLine ? '#17201c' : etfColor(entry.index);
        const points = entry.points.map(point => `${{x(point.date).toFixed(1)}},${{y(point.value).toFixed(1)}}`).join(' ');
        const focusKey = `etf-line-${{entry.item.code}}`;
        const label = `${{entry.item.industry}} ${{signedPct(entry.points[entry.points.length - 1].value)}}`;
        return `<g>
          <polyline class="etf-line-hit" data-etf-code="${{entry.item.code}}" data-focus-key="${{focusKey}}" role="button" tabindex="0" aria-label="选择${{label}}" points="${{points}}" fill="none" stroke="transparent" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" pointer-events="stroke"></polyline>
          <polyline class="etf-line-visible" points="${{points}}" fill="none" stroke="${{color}}" stroke-width="${{selectedLine ? 3.2 : 1.45}}" opacity="${{selectedLine ? .96 : .34}}" stroke-linecap="round" stroke-linejoin="round" pointer-events="none"></polyline>
        </g>`;
      }}).join('');
      const labelTop = 48;
      const labelBottom = 342;
      const endpointEntries = series.map(entry => {{
        const last = entry.points[entry.points.length - 1];
        return {{
          entry,
          last,
          endX: x(last.date),
          endY: y(last.value),
          labelY: clamp(y(last.value), labelTop, labelBottom)
        }};
      }}).sort((a, b) => a.endY - b.endY);
      const minLabelGap = Math.min(13, (labelBottom - labelTop) / Math.max(1, endpointEntries.length - 1));
      for (let index = 1; index < endpointEntries.length; index += 1) {{
        endpointEntries[index].labelY = Math.max(endpointEntries[index].labelY, endpointEntries[index - 1].labelY + minLabelGap);
      }}
      if (endpointEntries.length) {{
        endpointEntries[endpointEntries.length - 1].labelY = Math.min(endpointEntries[endpointEntries.length - 1].labelY, labelBottom);
      }}
      for (let index = endpointEntries.length - 2; index >= 0; index -= 1) {{
        endpointEntries[index].labelY = Math.min(endpointEntries[index].labelY, endpointEntries[index + 1].labelY - minLabelGap);
      }}
      if (endpointEntries.length) {{
        endpointEntries[0].labelY = Math.max(endpointEntries[0].labelY, labelTop);
      }}
      const labelX = right + 18;
      const labelDrawOrder = endpointEntries.slice().sort((a, b) => (a.entry.item.code === selectedEtf ? 1 : 0) - (b.entry.item.code === selectedEtf ? 1 : 0));
      const endLabels = labelDrawOrder.map(labelEntry => {{
        const selectedLine = labelEntry.entry.item.code === selectedEtf;
        const color = selectedLine ? '#17201c' : etfColor(labelEntry.entry.index);
        const opacity = selectedLine ? .98 : .72;
        const focusKey = `etf-label-${{labelEntry.entry.item.code}}`;
        const text = `${{labelEntry.entry.item.industry}} ${{signedPct(labelEntry.last.value)}}`;
        return `<g class="etf-end-label" data-etf-code="${{labelEntry.entry.item.code}}" data-focus-key="${{focusKey}}" role="button" tabindex="0" aria-label="选择${{text}}">
          <line x1="${{labelEntry.endX.toFixed(1)}}" y1="${{labelEntry.endY.toFixed(1)}}" x2="${{(labelX - 7).toFixed(1)}}" y2="${{labelEntry.labelY.toFixed(1)}}" stroke="${{color}}" stroke-width="${{selectedLine ? 1.6 : 1}}" opacity="${{opacity * .55}}"></line>
          <circle cx="${{labelEntry.endX.toFixed(1)}}" cy="${{labelEntry.endY.toFixed(1)}}" r="${{selectedLine ? 6.4 : 3.1}}" fill="${{color}}" stroke="#fff" stroke-width="${{selectedLine ? 2 : 1.3}}" opacity="${{opacity}}"></circle>
          <text x="${{labelX.toFixed(1)}}" y="${{(labelEntry.labelY + 3.4).toFixed(1)}}" fill="${{color}}" font-size="${{selectedLine ? 13 : 10.4}}" font-weight="${{selectedLine ? 850 : 720}}" opacity="${{opacity}}">${{text}}</text>
        </g>`;
      }}).join('');
      const zeroY = y(0);
      svg.innerHTML = `
        <rect x="0" y="0" width="960" height="420" fill="#fbfcfa"></rect>
        <line x1="${{left}}" y1="${{zeroY}}" x2="${{right}}" y2="${{zeroY}}" stroke="#9ca7a2" stroke-width="1.4" stroke-dasharray="4 4"></line>
        ${{ticks.map(tick => `
          <line x1="${{left}}" y1="${{y(tick).toFixed(1)}}" x2="${{right}}" y2="${{y(tick).toFixed(1)}}" stroke="#d8e0da" stroke-width="1"></line>
          <text class="axis-label" x="58" y="${{(y(tick) + 4).toFixed(1)}}" text-anchor="end">${{signedPct(tick)}}</text>
        `).join('')}}
        ${{dates.filter((_, index) => index === 0 || index === dates.length - 1 || index % Math.max(1, Math.floor(dates.length / 5)) === 0).map(date => `
          <text class="axis-label" x="${{x(date).toFixed(1)}}" y="376" text-anchor="middle">${{date.slice(5)}}</text>
        `).join('')}}
        <text class="axis-label" x="688" y="402">窗口归一化累计涨跌幅</text>
        ${{lines}}
        ${{endLabels}}
      `;
      svg.querySelectorAll('.etf-line-hit, .etf-end-label').forEach(node => {{
        const pick = persist => selectEtf(node.dataset.etfCode, {{ focusKey: node.dataset.focusKey, persist }});
        node.addEventListener('pointerenter', () => pick(false));
        node.addEventListener('pointermove', () => pick(false));
        node.addEventListener('click', () => pick(true));
        node.addEventListener('focus', () => pick(false));
        node.addEventListener('keydown', event => {{
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault();
          pick(true);
        }});
      }});
    }}

    function renderEtfTable() {{
      const rows = etfItems().map(item => ({{
        item,
        windowReturn: etfWindowReturn(item)
      }})).sort((a, b) => (b.windowReturn ?? -999) - (a.windowReturn ?? -999));
      const header = '<tr><th>行业</th><th>ETF</th><th>代码</th><th>规模(亿元)</th><th>最新日涨跌</th><th>行业指数日涨跌</th><th>窗口收益</th><th>走势一致性</th><th>相关</th><th>同涨跌</th><th>备注</th></tr>';
      const body = rows.map(({{ item, windowReturn }}) => `
        <tr class="etf-row ${{item.code === selectedEtf ? 'selected' : ''}}" data-etf-code="${{item.code}}" data-focus-key="etf-row-${{item.code}}" role="button" tabindex="0">
          <td>${{item.industry}}</td>
          <td>${{item.name}}</td>
          <td>${{item.code}}</td>
          <td>${{fmt2(item.market_value_100m)}}</td>
          <td class="heatmap-delta ${{deltaClass(item.latest_return_pct)}}">${{signedPct(item.latest_return_pct)}}</td>
          <td class="heatmap-delta ${{deltaClass(item.industry_latest_return_pct)}}">${{signedPct(item.industry_latest_return_pct)}}</td>
          <td class="heatmap-delta ${{deltaClass(windowReturn)}}">${{signedPct(windowReturn)}}</td>
          <td><span class="consistency-pill ${{consistencyClass(item.consistency)}}">${{item.consistency}}</span></td>
          <td>${{fmt2(item.correlation)}}</td>
          <td>${{fmt(item.direction_match_pct)}}%</td>
          <td>${{item.match_note}}</td>
        </tr>
      `).join('');
      document.getElementById('etf-table').innerHTML = `<table>${{header}}${{body}}</table>`;
      document.querySelectorAll('.etf-row').forEach(node => {{
        const pick = () => selectEtf(node.dataset.etfCode, {{ focusKey: node.dataset.focusKey, persist: true }});
        node.addEventListener('click', pick);
        node.addEventListener('keydown', event => {{
          if (event.key !== 'Enter' && event.key !== ' ') return;
          event.preventDefault();
          pick();
        }});
      }});
    }}

    function breadthState(item) {{
      const breadth = item.breadth_ma20;
      const delta = item.breadth_delta_5d || 0;
      if (breadth >= 70 && delta >= 0) return '扩散';
      if (breadth >= 60 && delta < 0) return '退潮';
      if (breadth < 50 && delta >= 6) return '修复';
      if (breadth < 45 && delta < 0) return '弱势';
      return '震荡';
    }}

    function deltaClass(value) {{
      if (value > 0) return 'positive';
      if (value < 0) return 'negative';
      return '';
    }}

    function sparkline(values) {{
      const valid = values.filter(Number.isFinite);
      if (!valid.length) return '';
      const min = Math.min(...valid);
      const max = Math.max(...valid);
      const span = Math.max(1, max - min);
      const points = values.map((value, index) => {{
        const x = 4 + index * (88 / Math.max(1, values.length - 1));
        const y = 20 - ((Number.isFinite(value) ? value : min) - min) * (16 / span);
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }}).join(' ');
      const last = values[values.length - 1];
      const first = values[0];
      const stroke = Math.abs(last - first) < 0.05 ? '#8b9691' : (last > first ? '#16885d' : '#c74d42');
      return `<svg class="sparkline" viewBox="0 0 96 24" aria-hidden="true">
        <polyline points="${{points}}" fill="none" stroke="${{stroke}}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></polyline>
      </svg>`;
    }}

    function heatColor(value) {{
      if (value == null) return '#f0f2ef';
      const clamped = Math.max(0, Math.min(100, value));
      const hue = clamped < 50 ? 16 + clamped * .6 : 80 + (clamped - 50) * 1.1;
      const light = 92 - clamped * .32;
      return `hsl(${{hue}} 62% ${{light}}%)`;
    }}

    function fmt(value) {{
      return value == null || Number.isNaN(Number(value)) ? '-' : Number(value).toFixed(1);
    }}
    function fmt2(value) {{
      return value == null || Number.isNaN(Number(value)) ? '-' : Number(value).toFixed(2);
    }}
    function signed(value) {{
      if (value == null || Number.isNaN(Number(value))) return '-';
      return `${{value > 0 ? '+' : ''}}${{Number(value).toFixed(1)}}`;
    }}
    function signedPct(value) {{
      if (value == null || Number.isNaN(Number(value))) return '-';
      return `${{value > 0 ? '+' : ''}}${{Number(value).toFixed(2)}}%`;
    }}
    function renderAll() {{
      if (!DATA.industries.some(item => item.name === selected)) selected = DATA.industries[0]?.name;
      document.getElementById('mode-daily').classList.toggle('active', mode === 'daily');
      document.getElementById('mode-weekly').classList.toggle('active', mode === 'weekly');
      document.querySelectorAll('[data-trace-mode]').forEach(node => {{
        node.classList.toggle('active', node.dataset.traceMode === traceMode);
        node.textContent = traceModeLabel(node.dataset.traceMode);
      }});
      document.getElementById('history-label').textContent = traceLabel();
      renderMarketInsights();
      renderSignalGroups();
      renderChangeLog();
      renderRotation();
      renderDetail();
      renderRankings();
      renderHeatmap();
      renderQuality();
      renderStrategyLab();
      if (activeTab === 'etf') renderEtf();
    }}
    document.querySelectorAll('[data-tab]').forEach(node => {{
      node.addEventListener('click', () => switchTab(node.dataset.tab));
    }});
    document.getElementById('mode-daily').addEventListener('click', () => {{ mode = 'daily'; hovered = null; saveState(); renderAll(); }});
    document.getElementById('mode-weekly').addEventListener('click', () => {{ mode = 'weekly'; hovered = null; saveState(); renderAll(); }});
    document.querySelectorAll('[data-trace-mode]').forEach(node => {{
      node.addEventListener('click', () => {{
        traceMode = node.dataset.traceMode;
        hovered = null;
        saveState();
        renderAll();
      }});
    }});
    document.querySelectorAll('[data-etf-window]').forEach(node => {{
      node.addEventListener('click', () => {{
        etfWindow = Number(node.dataset.etfWindow);
        saveState(false);
        renderEtf();
      }});
    }});
    document.querySelectorAll('[data-heatmap-sort]').forEach(node => {{
      node.addEventListener('click', () => {{
        heatmapSort = node.dataset.heatmapSort;
        saveState();
        renderHeatmap();
      }});
    }});
    document.querySelectorAll('[data-heatmap-window]').forEach(node => {{
      node.addEventListener('click', () => {{
        heatmapWindow = node.dataset.heatmapWindow;
        saveState();
        renderHeatmap();
      }});
    }});
    document.getElementById('copy-view-link').addEventListener('click', event => {{
      saveState();
      safeCopy(window.location.href).then(() => {{ event.currentTarget.textContent = '已复制视图链接'; }});
    }});
    document.getElementById('reset-view').addEventListener('click', () => {{
      activeTab = 'rotation';
      mode = 'daily';
      selected = DATA.industries[0]?.name;
      traceMode = '20';
      heatmapSort = 'breadth';
      heatmapWindow = '10';
      saveState();
      switchTab('rotation');
      renderAll();
    }});
    document.getElementById('download-report').addEventListener('click', () => {{
      const blob = new Blob([JSON.stringify(DATA, null, 2)], {{ type: 'application/json' }});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `rollingold-report-${{DATA.meta?.latest_report_date || 'latest'}}.json`;
      link.click();
      URL.revokeObjectURL(link.href);
    }});
    document.getElementById('download-factor-csv').addEventListener('click', () => {{
      const columns = ['date', 'industry', 'score', 'rs', 'breadth'];
      const rows = Object.entries(DATA.factor_history || {{}}).flatMap(([industry, series]) =>
        (series.dates || []).map((date, index) => [date, industry, series.score?.[index], series.rs?.[index], series.breadth?.[index]])
      );
      const csv = [columns.join(','), ...rows.map(row => row.map(value => value == null ? '' : `"${{String(value).replaceAll('"', '""')}}"`).join(','))].join('\\n');
      const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8' }});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `rollingold-factor-${{DATA.meta?.latest_report_date || 'latest'}}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    }});
    switchTab(activeTab);
    renderAll();
  </script>
</body>
</html>
"""


def default_report_shell() -> dict[str, Any]:
    return {
        "meta": {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "latest_date": "",
            "data_quality": "无数据",
        },
        "industries": [],
        "rankings": {},
        "breadth": {"dates": [], "industries": [], "values": []},
        "etfs": {"meta": {}, "items": []},
    }
