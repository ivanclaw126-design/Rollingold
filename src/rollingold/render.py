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
    section {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
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
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
    }}
    .rank-list {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    .rank-title {{
      background: var(--panel);
      padding: 9px 10px;
      font-weight: 720;
      font-size: 13px;
    }}
    .rank-item {{
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 9px 10px;
      border-top: 1px solid var(--line);
      font-size: 13px;
      cursor: pointer;
    }}
    .rank-item:hover {{
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
    table {{
      width: 100%;
      border-collapse: collapse;
      min-width: 940px;
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
    footer {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.7;
      padding: 4px 2px 0;
    }}
    .dot-label {{
      font-size: 11px;
      dominant-baseline: middle;
      pointer-events: none;
    }}
    @media (max-width: 900px) {{
      header {{ padding: 18px 14px; }}
      .topbar {{ grid-template-columns: 1fr; }}
      main {{ padding: 14px; }}
      .grid {{ grid-template-columns: 1fr; }}
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
    <div class="grid">
      <section>
        <div class="section-head">
          <h2>价格相对轮动图</h2>
          <p class="hint">横轴相对强弱，纵轴相对动量；点击行业查看详情。</p>
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
    </section>

    <section>
      <div class="section-head">
        <h2>市场宽度热力图</h2>
        <p class="hint">最近约 30 个交易日 MA20 站上率，0 值按无数据过滤后聚合。</p>
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

    function scaleX(x) {{ return 360 + Math.max(-3, Math.min(3, x)) * 92; }}
    function scaleY(y) {{ return 210 - Math.max(-3, Math.min(3, y)) * 58; }}

    function renderRotation() {{
      const svg = document.getElementById('rotation-svg');
      const selectedItem = DATA.industries.find(item => item.name === selected) || DATA.industries[0];
      const selectedPoint = activePoint(selectedItem);
      const labels = [
        ['走强', 120, 64], ['领涨', 585, 64], ['领跌', 120, 360], ['走弱', 585, 360]
      ];
      const path = (selectedPoint.path || []).map(p => `${{scaleX(p.x)}},${{scaleY(p.y)}}`).join(' ');
      svg.innerHTML = `
        <rect x="0" y="0" width="720" height="420" fill="#fbfcfa"></rect>
        <line x1="360" y1="28" x2="360" y2="392" stroke="#b8c3bb" stroke-width="1"></line>
        <line x1="36" y1="210" x2="684" y2="210" stroke="#b8c3bb" stroke-width="1"></line>
        <text x="666" y="232" fill="#66716d" font-size="12">相对强弱</text>
        <text x="374" y="42" fill="#66716d" font-size="12">相对动量</text>
        ${{labels.map(([text,x,y]) => `<text x="${{x}}" y="${{y}}" fill="#66716d" font-size="18" font-weight="700">${{text}}</text>`).join('')}}
        ${{path ? `<polyline points="${{path}}" fill="none" stroke="#17201c" stroke-width="2" opacity=".55"></polyline>` : ''}}
        ${{DATA.industries.map(item => {{
          const point = activePoint(item);
          const color = colorMap[point.quadrant] || '#66716d';
          const radius = item.name === selected ? 7 : 4.5;
          return `<g class="industry-dot" data-name="${{item.name}}" style="cursor:pointer">
            <circle cx="${{scaleX(point.x)}}" cy="${{scaleY(point.y)}}" r="${{radius}}" fill="${{color}}" stroke="#fff" stroke-width="1.5"></circle>
            <text class="dot-label" x="${{scaleX(point.x) + 8}}" y="${{scaleY(point.y)}}" fill="#17201c">${{item.name}}</text>
          </g>`;
        }}).join('')}}
      `;
      svg.querySelectorAll('.industry-dot').forEach(node => {{
        node.addEventListener('click', () => {{
          selected = node.dataset.name;
          renderAll();
        }});
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
      document.getElementById('rankings').innerHTML = groups.map(([title, items]) => `
        <div class="rank-list">
          <div class="rank-title">${{title}}</div>
          ${{items.map(name => {{
            const item = DATA.industries.find(entry => entry.name === name);
            return `<div class="rank-item" data-name="${{name}}"><span>${{name}}</span><span class="score">${{fmt(item?.score)}}</span></div>`;
          }}).join('') || '<div class="rank-item"><span>暂无</span><span></span></div>'}}
        </div>
      `).join('');
      document.querySelectorAll('.rank-item[data-name]').forEach(node => {{
        node.addEventListener('click', () => {{
          selected = node.dataset.name;
          renderAll();
        }});
      }});
    }}

    function renderHeatmap() {{
      const dates = DATA.breadth.dates.slice(-30);
      const offset = DATA.breadth.dates.length - dates.length;
      const order = DATA.industries.slice().sort((a, b) => b.score - a.score).map(item => item.name);
      const indexByName = new Map(DATA.breadth.industries.map((name, index) => [name, index]));
      const header = `<tr><th>行业</th>${{dates.map(date => `<th>${{date.slice(5)}}</th>`).join('')}}</tr>`;
      const rows = order.map(name => {{
        const row = DATA.breadth.values[indexByName.get(name)] || [];
        const cells = dates.map((_, idx) => {{
          const value = row[offset + idx];
          return `<td style="background:${{heatColor(value)}}">${{value == null ? '-' : value.toFixed(1)}}</td>`;
        }}).join('');
        return `<tr><td>${{name}}</td>${{cells}}</tr>`;
      }}).join('');
      document.getElementById('heatmap').innerHTML = `<table>${{header}}${{rows}}</table>`;
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
      renderRotation();
      renderDetail();
      renderRankings();
      renderHeatmap();
    }}
    document.getElementById('mode-daily').addEventListener('click', () => {{ mode = 'daily'; renderAll(); }});
    document.getElementById('mode-weekly').addEventListener('click', () => {{ mode = 'weekly'; renderAll(); }});
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
