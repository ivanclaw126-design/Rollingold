"""Small render assets kept outside the HTML shell."""

EXTRA_CSS = """
    .action-row, .mini-controls {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }
    .quality-grid, .strategy-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }
    .quality-item, .strategy-item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfcfa;
      padding: 10px;
      min-width: 0;
    }
    .breakdown-list {
      display: grid;
      gap: 7px;
      margin: 10px 0;
    }
    .breakdown-row {
      display: grid;
      grid-template-columns: 76px minmax(0, 1fr) 46px;
      gap: 8px;
      align-items: center;
      font-size: 12px;
    }
    .breakdown-track {
      height: 8px;
      background: #e4e9e4;
      border-radius: 999px;
      overflow: hidden;
    }
    .breakdown-fill {
      display: block;
      height: 100%;
      min-width: 2px;
      background: var(--green);
    }
    .breakdown-fill.negative { background: var(--red); }
    .muted-block {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.55;
      margin: 8px 0 0;
    }
"""


EXTRA_JS = """
    function safeCopy(text) {
      if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
      const area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.style.position = 'fixed';
      area.style.left = '-9999px';
      document.body.appendChild(area);
      area.select();
      document.execCommand('copy');
      document.body.removeChild(area);
      return Promise.resolve();
    }
"""
