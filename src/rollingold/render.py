"""Static HTML renderer for Rollingold."""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Any


def render_html(report: dict[str, Any]) -> str:
    data_json = json.dumps(report, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    generated_at = html.escape(str(report["meta"]["generated_at"]))
    latest_date = html.escape(str(report["meta"]["latest_date"]))
    quality = html.escape(str(report["meta"].get("data_quality", "未知")))
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
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
      background: var(--surface);
      color: var(--muted);
      font-weight: 650;
      cursor: pointer;
    }}
    .switch button.active {{
      background: var(--ink);
      color: #fff;
    }}
    main {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 20px 24px 36px;
      display: grid;
      gap: 18px;
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
    .signal-item:focus-visible, .rank-item:focus-visible {{
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
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(320px, .65fr);
      gap: 18px;
      align-items: start;
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
      border: 1px solid var(--line);
      border-radius: 8px;
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
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
    }}
    .text-button:hover {{
      background: var(--panel);
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
    .sparkline {{
      width: 96px;
      height: 24px;
      display: block;
      margin: 0 auto;
    }}
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
      h1 {{ font-size: 24px; }}
      .section-head {{ align-items: flex-start; flex-direction: column; }}
      #rotation-svg {{ aspect-ratio: 1 / 1; }}
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
          <span class="pill">最新交易日：{latest_date}</span>
          <span class="pill">生成时间：{generated_at}</span>
          <span class="pill">数据质量：{quality}</span>
        </div>
      </div>
      <div class="switch" aria-label="周期切换">
        <button id="mode-daily" class="active" type="button">日线</button>
        <button id="mode-weekly" type="button">周线</button>
      </div>
    </div>
  </header>
  <main>
    <section>
      <div class="section-head">
        <h2>行业轮动判断</h2>
        <p class="hint">先看价格强弱，再用宽度扩散验证趋势质量。</p>
      </div>
      <div class="insight-grid" id="market-insights"></div>
      <div class="signal-grid" id="signal-groups"></div>
      <p class="method-note">口径：价格相对轮动使用行业相对申万 A 指的强弱 z-score 和动量 z-score；MA20 宽度为行业内成分站上 20 日均线比例，1 日 / 5 日变化均为百分点变化。</p>
    </section>

    <div class="grid">
      <section>
        <div class="section-head">
          <h2>价格相对轮动图</h2>
          <div class="chart-meta">
            <span id="history-label">最近 60 个交易日</span>
            <span>横轴相对强弱，纵轴相对动量</span>
          </div>
        </div>
        <svg id="rotation-svg" viewBox="0 0 720 420" role="img" aria-label="行业四象限轮动图"></svg>
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
          <p class="hint" id="heatmap-hint">默认展示最近 10 个交易日，按当前 MA20 宽度排序；趋势列为同一窗口首尾变化，绿色上升、红色下降。</p>
          <button class="text-button" id="heatmap-toggle" type="button">显示全部时间</button>
        </div>
      </div>
      <div class="heatmap-wrap" id="heatmap"></div>
    </section>

    <footer>
      数据来源：AKShare 申万一级行业指数、大盘云图 MA20 行业宽度接口。行业口径为“宽度行业口径 + 申万价格口径映射”，合成行业使用等权平均。页面仅供研究参考，不构成投资建议。
    </footer>
  </main>
  <script>
    const DATA = {data_json};
    let mode = 'daily';
    let selected = DATA.industries[0]?.name;
    let heatmapExpanded = false;

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
      renderAll();
      restoreFocus(focusKey);
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

    function renderRotation() {{
      const svg = document.getElementById('rotation-svg');
      const selectedItem = DATA.industries.find(item => item.name === selected) || DATA.industries[0];
      const selectedPoint = activePoint(selectedItem);
      const points = currentPoints();
      const limit = chartLimit(points, selectedPoint);
      const ticks = [-limit, -limit / 2, 0, limit / 2, limit];
      const labels = [
        ['走强', 214, 134], ['领涨', 506, 134], ['领跌', 214, 286], ['走弱', 506, 286]
      ];
      const pathPoints = selectedPoint.path || [];
      const path = pathPoints.map(p => `${{scaleX(p.x, limit)}},${{scaleY(p.y, limit)}}`).join(' ');
      const leadingPaths = points
        .filter(({{ item, point }}) => item.name !== selected && point.quadrant === '领涨')
        .map(({{ item }}) => activePoint(item).path || [])
        .filter(points => points.length > 1)
        .map(points => points.map(p => `${{scaleX(p.x, limit)}},${{scaleY(p.y, limit)}}`).join(' '));
      const startPoint = pathPoints[0];
      const endPoint = pathPoints[pathPoints.length - 1];
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
        ${{labels.map(([text,x,y]) => `<text x="${{x}}" y="${{y}}" fill="#66716d" font-size="34" font-weight="850" opacity=".48" text-anchor="middle" dominant-baseline="middle">${{text}}</text>`).join('')}}
        ${{leadingPaths.map(points => `<polyline points="${{points}}" fill="none" stroke="#9bd8b7" stroke-width="2" opacity=".36" stroke-linecap="round" stroke-linejoin="round"></polyline>`).join('')}}
        ${{path ? `<polyline points="${{path}}" fill="none" stroke="#17201c" stroke-width="3" opacity=".62" stroke-linecap="round" stroke-linejoin="round"></polyline>` : ''}}
        ${{pathPoints.map((point, index) => index % 6 === 0 ? `<circle cx="${{scaleX(point.x, limit)}}" cy="${{scaleY(point.y, limit)}}" r="2.4" fill="#17201c" opacity=".26"></circle>` : '').join('')}}
        ${{startPoint ? `<circle cx="${{scaleX(startPoint.x, limit)}}" cy="${{scaleY(startPoint.y, limit)}}" r="4" fill="#fff" stroke="#17201c" stroke-width="1.6"></circle>` : ''}}
        ${{endPoint ? `<circle cx="${{scaleX(endPoint.x, limit)}}" cy="${{scaleY(endPoint.y, limit)}}" r="7.5" fill="none" stroke="#17201c" stroke-width="2"></circle>` : ''}}
        ${{points.map(({{ item, point }}) => {{
          const color = colorMap[point.quadrant] || '#66716d';
          const isSelected = item.name === selected;
          const radius = isSelected ? 8 : 5;
          const x = scaleX(point.x, limit);
          const y = scaleY(point.y, limit);
          const labelX = clamp(x + 10, 78, 638);
          const labelY = clamp(y + 4, 66, 354);
          return `<g class="industry-dot" data-name="${{item.name}}" data-focus-key="dot-${{item.rank}}" role="button" tabindex="0" aria-label="选择${{item.name}}" style="cursor:pointer">
            <title>${{item.name}}｜${{point.quadrant}}｜强弱 ${{fmt(point.x)}}｜动量 ${{fmt(point.y)}}｜评分 ${{fmt(item.score)}}</title>
            <circle cx="${{x}}" cy="${{y}}" r="${{radius}}" fill="${{color}}" stroke="#fff" stroke-width="${{isSelected ? 2.4 : 1.5}}"></circle>
            <text class="dot-label ${{isSelected ? 'selected' : ''}}" x="${{labelX}}" y="${{labelY}}" fill="#17201c">${{item.name}}</text>
          </g>`;
        }}).join('')}}
      `;
      svg.querySelectorAll('.industry-dot').forEach(node => {{
        bindIndustryControl(node);
      }});
    }}

    function renderDetail() {{
      const item = DATA.industries.find(entry => entry.name === selected) || DATA.industries[0];
      const point = activePoint(item);
      document.getElementById('detail-panel').innerHTML = `
        <h3>${{item.name}}</h3>
        <div class="tags">
          <span class="tag">${{point.quadrant}}</span>
          <span class="tag">${{item.status}}</span>
          <span class="tag">成交${{item.amount_confirm ? '确认' : '偏弱'}}</span>
        </div>
        <div class="detail-grid">
          <div class="metric"><span>综合评分</span><strong>${{fmt(item.score)}}</strong></div>
          <div class="metric"><span>MA20 宽度</span><strong>${{fmt(item.breadth_ma20)}}%</strong></div>
          <div class="metric"><span>1 日变化</span><strong>${{signed(item.breadth_delta_1d)}}</strong></div>
          <div class="metric"><span>5 日变化</span><strong>${{signed(item.breadth_delta_5d)}}</strong></div>
          <div class="metric"><span>相对强弱</span><strong>${{fmt(point.x)}}</strong></div>
          <div class="metric"><span>相对动量</span><strong>${{fmt(point.y)}}</strong></div>
        </div>
        <p>${{item.comment}}</p>
        <div class="tags">${{item.divergences.map(text => `<span class="tag">${{text}}</span>`).join('')}}</div>
      `;
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

    function renderHeatmap() {{
      const windowSize = heatmapExpanded ? DATA.breadth.dates.length : Math.min(10, DATA.breadth.dates.length);
      const dates = DATA.breadth.dates.slice(-windowSize);
      const offset = DATA.breadth.dates.length - dates.length;
      const order = DATA.industries.slice()
        .sort((a, b) => (b.breadth_ma20 ?? -1) - (a.breadth_ma20 ?? -1))
        .map(item => item.name);
      const indexByName = new Map(DATA.breadth.industries.map((name, index) => [name, index]));
      const trendLabel = heatmapExpanded ? `趋势(全部${{dates.length}}日)` : `趋势(近${{dates.length}}日)`;
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
      document.getElementById('heatmap-toggle').textContent = heatmapExpanded ? '收起到近 10 日' : '显示全部时间';
      document.getElementById('heatmap-hint').textContent = heatmapExpanded
        ? `已展示全部 ${{dates.length}} 个交易日，趋势列为全部窗口首尾变化；绿色上升、红色下降、灰色持平。`
        : `默认展示最近 ${{dates.length}} 个交易日，按当前 MA20 宽度排序；趋势列为近 ${{dates.length}} 日首尾变化，绿色上升、红色下降、灰色持平。`;
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
    function signed(value) {{
      if (value == null || Number.isNaN(Number(value))) return '-';
      return `${{value > 0 ? '+' : ''}}${{Number(value).toFixed(1)}}`;
    }}
    function renderAll() {{
      document.getElementById('mode-daily').classList.toggle('active', mode === 'daily');
      document.getElementById('mode-weekly').classList.toggle('active', mode === 'weekly');
      document.getElementById('history-label').textContent = mode === 'weekly' ? '最近 52 周' : '最近 60 个交易日';
      renderMarketInsights();
      renderSignalGroups();
      renderRotation();
      renderDetail();
      renderRankings();
      renderHeatmap();
    }}
    document.getElementById('mode-daily').addEventListener('click', () => {{ mode = 'daily'; renderAll(); }});
    document.getElementById('mode-weekly').addEventListener('click', () => {{ mode = 'weekly'; renderAll(); }});
    document.getElementById('heatmap-toggle').addEventListener('click', () => {{ heatmapExpanded = !heatmapExpanded; renderHeatmap(); }});
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
    }
