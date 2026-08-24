# src/dashboard/components/charts.py
#
# Three hand-built charts, faithful to the design spec (section 5):
#   - Detection Status : log-scaled bars, severity-coloured
#   - Top Services     : SVG donut (stroke-dasharray) + HTML legend
#   - Event Timeline   : SVG line chart (viewBox 0 0 620 146) + area fill
#
# No Plotly. Everything is computed in Python and injected as HTML/SVG.

import math
import streamlit as st
import pandas as pd

from dashboard.config.theme import DETECTION_TAGS, hex_to_rgba
from dashboard.config.render import html


def render_charts(t, report):
    """
    Renders the 3-chart row.
    Layout : [DETECTION STATUS] [TOP SERVICES] [EVENT TIMELINE]
    """
    html("<div style='margin-bottom:8px;'></div>")

    col1, col2, col3 = st.columns([1.25, 0.85, 1.4])

    with col1:
        _render_detection_status(t, report)
    with col2:
        _render_top_services(t, report)
    with col3:
        _render_event_timeline(t, report)


# ── Detection Status (log bars) ───────────────────────────────

def _render_detection_status(t, report):
    _section_label(t, "DETECTION STATUS", right="MATCHES / RULE")

    summary = report.get("detection_summary", pd.DataFrame())
    if summary is None or summary.empty:
        _empty_chart(t, height=170)
        return

    dets     = summary["detection"].tolist()
    counts   = [int(c) for c in summary["count"].tolist()]
    statuses = summary["status"].tolist()
    codes    = [DETECTION_TAGS.get(d, d[:3].upper()) for d in dets]

    max_c = max(counts) if counts else 0

    def bar_h(c):
        # Logarithmic scale — counts span 0..~1800.
        if max_c <= 0:
            return 4.0
        return max(4.0, math.log(c + 1) / math.log(max_c + 1) * 120.0)

    bars = ""
    for c, s in zip(counts, statuses):
        col = _bar_color(t, s, c)
        bars += (
            '<div style="flex:1;display:flex;flex-direction:column;'
            'align-items:center;justify-content:flex-end;height:100%;">'
            f'<div style="font-family:var(--mono);font-size:9px;'
            f'color:{t["fg2"]};margin-bottom:3px;">{c}</div>'
            f'<div style="width:62%;max-width:24px;height:{bar_h(c):.1f}px;'
            f'background:{col};border-radius:2px 2px 0 0;"></div>'
            '</div>'
        )

    codes_row = ""
    for code in codes:
        codes_row += (
            '<div style="flex:1;text-align:center;font-family:var(--mono);'
            f'font-size:8.5px;color:{t["mute"]};letter-spacing:.04em;">{code}</div>'
        )

    html(
        f'<div style="display:flex;align-items:flex-end;gap:6px;height:132px;'
        f'border-bottom:1px solid {t["chart_axis"]};">{bars}</div>'
        f'<div style="display:flex;gap:6px;margin-top:6px;">{codes_row}</div>'
    )


def _bar_color(t, status, count):
    """Severity colour if ALERT, muted if CLEAR/disabled."""
    if status != "ALERT":
        return "#2F3846"
    if count >= 10:
        return t["critical"]
    if count >= 5:
        return t["high"]
    return t["medium"]


# ── Top Services (SVG donut) ──────────────────────────────────

def _render_top_services(t, report):
    _section_label(t, "TOP SERVICES")

    ts           = report.get("top_services", pd.DataFrame())
    total_events = report.get("total_events", 0)

    if ts is None or ts.empty:
        _empty_chart(t, height=170)
        return

    labels = [s.replace(".amazonaws.com", "") for s in ts["eventSource"].tolist()][:6]
    values = [int(v) for v in ts["count"].tolist()][:6]
    total  = sum(values) or 1
    palette = t["donut"]

    cx = cy = 59
    r  = 46
    sw = 13
    C  = 2 * math.pi * r

    track = (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="{t["bd_fine"]}" stroke-width="{sw}"></circle>'
    )

    segs = ""
    offset = 0.0
    for i, v in enumerate(values):
        seg = (v / total) * C
        color = palette[i % len(palette)]
        segs += (
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-dasharray="{seg:.2f} {C - seg:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}"></circle>'
        )
        offset += seg

    center = _fmt_count(total_events)

    svg = (
        '<svg width="118" height="118" viewBox="0 0 118 118">'
        f'<g transform="rotate(-90 {cx} {cy})">{track}{segs}</g>'
        f'<text x="59" y="56" text-anchor="middle" fill="{t["text_primary"]}" '
        'style="font-family:Inter;font-size:17px;font-weight:600;">'
        f'{center}</text>'
        f'<text x="59" y="71" text-anchor="middle" fill="{t["mute"]}" '
        'style="font-family:Inter;font-size:8.5px;font-weight:600;'
        'letter-spacing:.14em;">EVENTS</text>'
        '</svg>'
    )

    leg = ""
    for i, (l, v) in enumerate(zip(labels, values)):
        pct = int(v / total * 100)
        color = palette[i % len(palette)]
        leg += (
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:7px;">'
            f'<span style="width:7px;height:7px;border-radius:2px;'
            f'background:{color};display:inline-block;flex-shrink:0;"></span>'
            f'<span style="flex:1;color:{t["fg2"]};font-size:11px;'
            'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{l}</span>'
            f'<span style="font-family:var(--mono);font-size:10px;'
            f'color:{t["mute"]};">{pct}%</span>'
            '</div>'
        )

    html(
        '<div style="display:flex;align-items:center;gap:16px;">'
        f'{svg}<div style="flex:1;min-width:0;">{leg}</div></div>'
    )


# ── Event Timeline (SVG line) ─────────────────────────────────

def _render_event_timeline(t, report):
    _section_label(
        t, "EVENT TIMELINE",
        legend=[("ALL EVENTS", t["chart_line_1"]),
                ("DETECTIONS", t["chart_line_2"])],
    )

    tl      = report.get("events_per_hour", pd.DataFrame())
    summary = report.get("detection_summary", pd.DataFrame())

    if tl is None or tl.empty:
        _empty_chart(t, height=170)
        return

    counts = [float(c) for c in tl["count"].tolist()]
    n = len(counts)
    if n < 2:
        _empty_chart(t, height=170)
        return

    total_det = (
        int(summary["count"].sum())
        if (summary is not None and not summary.empty) else 0
    )
    scale = total_det / max(sum(counts), 1)
    det = [max(0.0, c * scale) for c in counts]

    W, H, top, base = 620, 146, 1, 118
    maxv = max(max(counts), max(det), 1.0)

    def X(i):
        return (i / (n - 1)) * W

    def Y(v):
        return base - (v / maxv) * (base - top)

    pts_all = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(counts))
    pts_det = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(det))
    area = (
        f"M0,{base:.1f} "
        + " ".join(f"L{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(counts))
        + f" L{W},{base:.1f} Z"
    )

    grid = ""
    for gy, gc in [(1, t["bd_fine"]), (40, t["bd_fine"]),
                   (79, t["bd_fine"]), (118, t["chart_axis"])]:
        grid += (
            f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="{gc}" '
            'stroke-width="1" vector-effect="non-scaling-stroke"></line>'
        )

    peaks = sorted(range(n), key=lambda i: counts[i], reverse=True)[:2]
    marks = ""
    for i in peaks:
        marks += (
            f'<circle cx="{X(i):.1f}" cy="{Y(counts[i]):.1f}" r="3" '
            f'fill="{t["card"]}" stroke="{t["critical"]}" stroke-width="1.4" '
            'vector-effect="non-scaling-stroke"></circle>'
        )

    a1 = hex_to_rgba(t["chart_line_1"], 0.22)
    a0 = hex_to_rgba(t["chart_line_1"], 0.0)

    svg = (
        f'<svg viewBox="0 0 {W} {H}" preserveAspectRatio="none" '
        'style="width:100%;height:146px;display:block;">'
        '<defs><linearGradient id="tlGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{a1}"></stop>'
        f'<stop offset="100%" stop-color="{a0}"></stop></linearGradient></defs>'
        f'{grid}'
        f'<path d="{area}" fill="url(#tlGrad)" stroke="none"></path>'
        f'<polyline points="{pts_all}" fill="none" stroke="{t["chart_line_1"]}" '
        'stroke-width="1.6" vector-effect="non-scaling-stroke"></polyline>'
        f'<polyline points="{pts_det}" fill="none" stroke="{t["chart_line_2"]}" '
        'stroke-width="1.4" vector-effect="non-scaling-stroke"></polyline>'
        f'{marks}</svg>'
    )

    ticks = ""
    for hh in range(0, 25, 4):
        ticks += (
            f'<span style="font-family:var(--mono);font-size:9px;'
            f'color:{t["mute"]};">{hh:02d}:00</span>'
        )

    html(
        svg
        + '<div style="display:flex;justify-content:space-between;'
          f'margin-top:4px;">{ticks}</div>'
    )


# ── Helpers ───────────────────────────────────────────────────

def _section_label(t, label, right=None, legend=None):
    right_html = ""
    if right:
        right_html = f'<span class="cla-col">{right}</span>'
    elif legend:
        for name, color in legend:
            right_html += (
                '<span style="display:inline-flex;align-items:center;gap:5px;'
                'margin-left:12px;">'
                f'<span style="width:16px;height:2px;background:{color};'
                'border-radius:1px;display:inline-block;"></span>'
                f'<span class="cla-col">{name}</span></span>'
            )

    html(
        '<div style="display:flex;justify-content:space-between;'
        'align-items:center;margin-bottom:8px;">'
        f'<span class="cla-label">{label}</span>'
        f'<div style="display:flex;align-items:center;">{right_html}</div></div>'
    )


def _empty_chart(t, height=200):
    html(
        f'<div style="height:{height}px;display:flex;align-items:center;'
        f'justify-content:center;background:{t["card"]};'
        f'border:1px solid {t["border"]};border-radius:5px;color:{t["mute"]};'
        'font-size:0.72rem;text-transform:uppercase;letter-spacing:.1em;">'
        'NO DATA AVAILABLE</div>'
    )


def _fmt_count(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,}"