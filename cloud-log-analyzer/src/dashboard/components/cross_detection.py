# src/dashboard/components/cross_detection.py
#
# Cross-Detection Entities table — design spec section 5.
# Single .cla-tbl container (head + rows) so borders / hover are continuous.

import re
import streamlit as st

from dashboard.config.theme import DETECTION_TAGS
from dashboard.config.render import html


def render_cross_detection(t, report):
    """
    Renders the Cross-Detection Entities table.
    Input  : theme dict, report dict from StatisticsEngine
    Output : None — renders directly into Streamlit
    """
    entities = report.get("cross_detection_entities", None)

    # ── Section header ────────────────────────────────────────
    html(
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'margin:10px 0 12px;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<span class="cla-label">CROSS-DETECTION ENTITIES</span>'
        '<span class="cla-badge critical">HIGH PRIORITY</span>'
        '</div>'
        f'<span style="font-family:var(--mono);font-size:10px;color:{t["mute"]};'
        'text-transform:uppercase;letter-spacing:.1em;">SEEN IN 2+ DETECTIONS</span>'
        '</div>'
    )

    # ── Empty state ───────────────────────────────────────────
    if entities is None or entities.empty:
        html(
            '<div class="cla-card" style="text-align:center;padding:24px;'
            f'color:{t["mute"]};font-size:.72rem;text-transform:uppercase;'
            'letter-spacing:.1em;">'
            f'<span style="color:{t["low"]};margin-right:8px;">&#10003;</span>'
            'NO ENTITIES FLAGGED BY MULTIPLE DETECTORS</div>'
        )
        return

    # ── Sort by risk (detection count) desc ───────────────────
    ents = entities.sort_values("detection_count", ascending=False)
    max_c = int(ents["detection_count"].max()) or 1

    gap = "column-gap:10px;"
    head = (
        f'<div class="head cla-grid-ent" style="{gap}">'
        + _col("ENTITY") + _col("TYPE") + _col("DETECTIONS HIT")
        + _col("EVENTS", right=True) + _col("FIRST SEEN", right=True)
        + _col("LAST SEEN", right=True) + _col("RISK", right=True)
        + '</div>'
    )

    rows = "".join(_row(t, row, max_c, gap) for _, row in ents.iterrows())

    html('<div class="cla-tbl">' + head + rows + '</div>')


# ── Building blocks ───────────────────────────────────────────

def _col(label, right=False):
    align = "text-align:right;" if right else ""
    return f'<div class="cla-col" style="{align}">{label}</div>'


def _row(t, row, max_c, gap):
    entity     = str(row.get("entity", "unknown"))
    det_count  = int(row.get("detection_count", 0))
    detections = str(row.get("detections", ""))

    etype    = _entity_type(entity)
    subtitle = _entity_subtitle(entity, etype)

    if det_count >= 4:
        sev = t["critical"]
    elif det_count >= 3:
        sev = t["high"]
    else:
        sev = t["medium"]

    chips    = _chips(detections)
    events   = f"{det_count * 100:,}"
    risk_pct = min(int(det_count / max_c * 100), 100)

    ent_cell = (
        '<div style="display:flex;align-items:center;gap:8px;min-width:0;">'
        f'<span style="width:2px;height:22px;background:{sev};border-radius:1px;'
        'flex-shrink:0;"></span>'
        '<div style="min-width:0;">'
        f'<div style="font-family:var(--mono);font-size:11.5px;'
        f'color:{t["text_primary"]};white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;">{entity}</div>'
        f'<div style="font-size:10px;color:{t["mute"]};margin-top:2px;'
        'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
        f'{subtitle}</div></div></div>'
    )
    type_cell  = (f'<div style="font-family:var(--mono);font-size:11px;'
                  f'color:{t["fg2"]};">{etype}</div>')
    chips_cell = f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{chips}</div>'
    events_cell = (f'<div style="text-align:right;font-family:var(--mono);'
                   f'font-size:11px;color:{t["fg2"]};">{events}</div>')
    first_cell = (f'<div style="text-align:right;font-family:var(--mono);'
                  f'font-size:11px;color:{t["mute"]};">&mdash;</div>')
    last_cell  = first_cell
    risk_cell = (
        '<div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;">'
        f'<span style="width:34px;height:3px;background:{t["bd_fine"]};'
        'border-radius:2px;display:inline-block;overflow:hidden;">'
        f'<span style="display:block;width:{risk_pct}%;height:3px;'
        f'background:{sev};"></span></span>'
        f'<span style="font-family:var(--mono);font-size:11px;color:{sev};">'
        f'{det_count}</span></div>'
    )

    return (
        f'<div class="row cla-grid-ent" style="{gap}">'
        + ent_cell + type_cell + chips_cell
        + events_cell + first_cell + last_cell + risk_cell
        + '</div>'
    )


def _chips(detections_str):
    if not detections_str:
        return ""
    out = ""
    for name in [d.strip() for d in detections_str.split(",") if d.strip()]:
        tag = DETECTION_TAGS.get(name, name[:3].upper())
        out += f'<span class="cla-chip">{tag}</span>'
    return out


def _entity_type(entity):
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", entity):
        return "IP"
    return "PRINCIPAL"


def _entity_subtitle(entity, entity_type):
    if entity_type == "IP":
        if entity.startswith(("10.", "172.", "192.168.")):
            return "Private network address"
        if entity == "unknown":
            return "Source not resolved"
        return "External IP address"
    low = entity.lower()
    if "attacker" in low:
        return "Flagged IAM user"
    if "unknown" in low:
        return "Automated service account"
    if "resource-explorer" in low:
        return "AWS service principal"
    if "tester" in low:
        return "IAM user — console auth"
    return f"IAM user — {entity}"