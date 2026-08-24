# src/dashboard/config/css.py
#
# Injects the global stylesheet.  Only the :root block is derived from the
# theme dict (so dark/light switching works); everything else is static and
# references CSS variables — which keeps components free of colour interpolation.

import streamlit as st


def apply_css(t):
    """
    Injects the design-spec stylesheet into Streamlit.

    Input  : t (theme dict — DARK or LIGHT)
    Output : None — injects styles directly into the page
    """
    root = f"""
:root {{
  --bg:{t['bg_primary']}; --panel:{t['panel']}; --card:{t['card']};
  --hover:{t['hover']}; --chip:{t['chip']};
  --bd:{t['border']}; --bd-fine:{t['bd_fine']}; --bd-input:{t['bd_input']};
  --fg:{t['text_primary']}; --fg2:{t['fg2']}; --fg3:{t['fg3']};
  --label:{t['label']}; --mute:{t['mute']};
  --accent:{t['accent']};
  --critical:{t['critical']}; --high:{t['high']}; --medium:{t['medium']}; --low:{t['low']};
  --crit-bg:{t['critical_bg']}; --crit-bd:{t['critical_bd']};
  --high-bg:{t['high_bg']};     --high-bd:{t['high_bd']};
  --med-bg:{t['medium_bg']};    --med-bd:{t['medium_bd']};
  --low-bg:{t['low_bg']};       --low-bd:{t['low_bd']};
  --mono:'JetBrains Mono', ui-monospace, monospace;
}}
"""

    static = """
/* ── Base ─────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: Inter, system-ui, sans-serif; }
* { box-sizing: border-box; }
.stApp { background: var(--bg); color: var(--fg); }
.block-container { padding: 0 24px 40px; max-width: 100%; }
header[data-testid="stHeader"] { display: none; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none; }

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--bd-fine); }
section[data-testid="stSidebar"] .block-container { padding: 16px; }

/* ── Tabs (native, restyled) ──────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { gap: 0; border-bottom: 1px solid var(--bd);
  background: transparent; overflow-x: auto; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 0; padding: 10px 16px 8px;
  min-width: 0; white-space: nowrap; flex: 0 0 auto; color: #8A92A4;
  font-size: 11px; font-weight: 500; }
.stTabs [aria-selected="true"] { background: var(--chip); color: var(--fg);
  border-bottom: 2px solid var(--accent); }

/* ── Buttons ──────────────────────────────────────────────── */
[data-testid="stButton"] button { background: transparent; color: var(--fg);
  border: 1px solid var(--bd); border-radius: 4px; font-size: 0.72rem; font-weight: 500;
  text-transform: uppercase; letter-spacing: 0.08em; padding: 6px 16px; transition: all 0.15s ease; }
[data-testid="stButton"] button:hover { background: var(--chip); border-color: var(--accent); }
[data-testid="stButton"] button[kind="primary"] { background: var(--accent); color: #0F1117;
  border-color: var(--accent); font-weight: 600; }

/* ── Inputs / selects / expander ──────────────────────────── */
[data-testid="stSelectbox"] > div > div { background: var(--panel); border: 1px solid var(--bd-input);
  border-radius: 4px; color: var(--fg); font-size: 0.8rem; }
[data-testid="stTextInput"] input { background: var(--panel); border: 1px solid var(--bd-input);
  border-radius: 4px; color: var(--fg); font-size: 0.8rem; font-family: var(--mono); }
[data-testid="stTextInput"] input:focus { border-color: var(--accent); }
[data-testid="stNumberInput"] input { background: var(--panel); border: 1px solid var(--bd-input);
  border-radius: 4px; color: var(--fg); font-family: var(--mono); font-size: 0.85rem; }
[data-testid="stNumberInput"] button { background: var(--chip); border: 1px solid var(--bd-input);
  color: var(--fg2); }
[data-testid="stNumberInput"] button:hover { border-color: var(--accent); color: var(--accent); }
[data-testid="stExpander"] { background: var(--card); border: 1px solid var(--bd); border-radius: 4px; }
.stCheckbox label p { font-size: 11.5px !important; color: #C8CEDA !important; }
[data-testid="stRadio"] label p { font-family: var(--mono); font-size: 11px; color: var(--fg2); }
[data-testid="stRadio"] [role="radiogroup"] { gap: 2px; }
.stSlider [data-baseweb="slider"] div[role="slider"] { background: var(--accent); }

/* ── DataFrame ────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid var(--bd); border-radius: 4px; }
[data-testid="stDataFrame"] th { background: var(--panel) !important; color: var(--label) !important;
  font-size: 0.62rem !important; font-weight: 600 !important; text-transform: uppercase !important;
  letter-spacing: 0.1em !important; border-bottom: 1px solid var(--bd) !important; }
[data-testid="stDataFrame"] td { color: var(--fg2) !important; font-size: 0.72rem !important;
  border-bottom: 1px solid var(--bd-fine) !important; font-family: var(--mono); }

hr { border: none; border-top: 1px solid var(--bd); margin: 16px 0; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--bd); border-radius: 2px; }

/* ══ SPEC CLASSES (.cla-*) ════════════════════════════════ */

.cla-label { font-size: 9.5px; font-weight: 600; letter-spacing: .14em;
  text-transform: uppercase; color: var(--label); }
.cla-col { font-size: 9px; font-weight: 600; letter-spacing: .13em;
  text-transform: uppercase; color: var(--mute); }
.cla-mono { font-family: var(--mono); font-variant-numeric: tabular-nums; }

.cla-card { background: var(--card); border: 1px solid var(--bd); border-radius: 5px; padding: 14px 16px; }

/* KPI */
.cla-kpi-val { font-size: 27px; font-weight: 600; letter-spacing: -.02em;
  font-variant-numeric: tabular-nums; color: var(--fg); }
.cla-kpi-unit { font-size: 11px; color: var(--mute); }
.cla-bar { height: 2px; background: var(--bd-fine); border-radius: 2px; overflow: hidden; }
.cla-bar > i { display: block; height: 2px; background: var(--accent); }

/* status badge */
.cla-badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 7px; border-radius: 3px;
  font-size: 9px; font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
  white-space: nowrap; border: 1px solid; }
.cla-badge.critical { color: var(--critical); background: var(--crit-bg); border-color: var(--crit-bd); }
.cla-badge.high     { color: var(--high);     background: var(--high-bg); border-color: var(--high-bd); }
.cla-badge.medium   { color: var(--medium);   background: var(--med-bg);  border-color: var(--med-bd); }
.cla-badge.clear    { color: var(--low);      background: var(--low-bg);  border-color: var(--low-bd); }

/* table */
.cla-tbl { border: 1px solid var(--bd); border-radius: 4px; overflow: hidden; }
.cla-tbl .head { background: var(--panel); border-bottom: 1px solid var(--bd); padding: 9px 16px; }
.cla-tbl .row { padding: 11px 16px; border-bottom: 1px solid #1A1E27; }
.cla-tbl .row:hover { background: var(--hover); }
.cla-tbl .mono { font-family: var(--mono); font-size: 11px; color: var(--fg2); }
.cla-grid-ent { display: grid; grid-template-columns: 1.5fr .7fr 1.6fr .6fr .8fr .8fr .7fr; align-items: center; }
.cla-grid-ev  { display: grid; grid-template-columns: .75fr 1.2fr .9fr 1.3fr .8fr .7fr; align-items: center; }

/* detection chip */
.cla-chip { padding: 2px 6px; border: 1px solid var(--bd-input); border-radius: 3px; background: var(--chip);
  font-family: var(--mono); font-size: 9.5px; color: var(--fg2); }

/* rule logic code block */
.cla-code { background: var(--bg); border: 1px solid var(--bd); border-radius: 4px; padding: 10px 12px;
  font-family: var(--mono); font-size: 11px; color: var(--fg2); line-height: 1.7; white-space: pre-wrap; }

/* pipeline blinking dot */
.cla-pulse { animation: pulse 2.4s infinite; }
@keyframes pulse { 0% { opacity: 1; } 50% { opacity: .35; } 100% { opacity: 1; } }

/* ══ LEGACY CLASSES (kept during transition, re-pointed to vars) ══ */

.kpi-bar-track { height: 2px; background: var(--bd-fine); border-radius: 2px; margin-top: 8px; width: 100%; }
.kpi-bar-fill  { height: 2px; border-radius: 2px; transition: width 0.3s ease; }
.section-label { color: var(--label); font-size: 0.62rem; font-weight: 600; text-transform: uppercase;
  letter-spacing: 0.12em; margin: 0 0 12px 0; }
.det-tag { display: inline-block; background: var(--chip); color: var(--fg2); font-size: 0.6rem;
  font-weight: 600; letter-spacing: 0.06em; padding: 2px 6px; border-radius: 3px; margin-right: 4px;
  font-family: var(--mono); }
.status-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; margin-right: 6px;
  vertical-align: middle; }
.card { background: var(--card); border: 1px solid var(--bd); border-radius: 6px; padding: 20px; }
.rule-logic { background: var(--bg); border: 1px solid var(--bd); border-radius: 4px; padding: 12px 16px;
  font-family: var(--mono); font-size: 0.78rem; color: var(--fg2); line-height: 1.6;
  white-space: pre; overflow-x: auto; }
.mitre-badge { display: inline-block; color: var(--accent); font-size: 0.75rem; font-weight: 600;
  font-family: var(--mono); margin-bottom: 2px; }
.priority-badge { display: inline-block; background: var(--crit-bg); color: var(--critical);
  border: 1px solid var(--crit-bd); font-size: 0.6rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.1em; padding: 3px 8px; border-radius: 3px; margin-left: 10px; vertical-align: middle; }
.active-alerts-badge { display: inline-flex; align-items: center; gap: 6px; background: var(--crit-bg);
  color: var(--critical); border: 1px solid var(--crit-bd); font-size: 0.72rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.08em; padding: 5px 12px; border-radius: 4px; }
.ingesting-status { display: flex; align-items: center; gap: 6px; color: var(--accent); font-size: 0.7rem;
  font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }
.signal-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.signal-label { color: var(--label); font-size: 0.75rem; min-width: 120px; }
.signal-value { color: var(--fg); font-size: 0.75rem; font-weight: 600; min-width: 50px; text-align: right; }
.signal-bar-track { flex: 1; height: 3px; background: var(--bd-fine); border-radius: 2px; margin: 0 12px; }
.signal-bar-fill { height: 3px; border-radius: 2px; }
"""

    link = ('<link rel="stylesheet" '
            'href="https://fonts.googleapis.com/css2?'
            'family=Inter:wght@400;500;600;700&'
            'family=JetBrains+Mono:wght@400;500&display=swap">')

    css = link + "<style>" + root + static + "</style>"

    # Collapse to a SINGLE line. Streamlit runs this string through its
    # Markdown parser; any line starting with "* ", "#", "-" or a digit
    # (all common in CSS: "* {", "#MainMenu", ...) would be turned into a
    # bullet or heading, which breaks the <style> tag and leaks the CSS as
    # visible text. With no line breaks there are no line-starts to misread,
    # and CSS is whitespace-insensitive so nothing else changes.
    css = " ".join(line.strip() for line in css.splitlines())

    st.markdown(css, unsafe_allow_html=True)