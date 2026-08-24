# src/dashboard/config/theme.py
#
# Colour tokens adapted to the Cloud Log Analyzer design spec.
# The DARK / LIGHT dicts are the single source of truth for hex values.
# CSS (config/css.py) derives its :root variables from the same dict,
# and Python logic / Plotly read hex values straight from here.

# ── DARK ──────────────────────────────────────────────────────
DARK = {
    # Backgrounds
    "bg_primary":    "#0F1117",   # page
    "panel":         "#12141B",   # sidebar / header / table head
    "bg_secondary":  "#151821",   # cards  (legacy key — kept)
    "card":          "#151821",
    "hover":         "#181C25",   # row hover
    "bg_tertiary":   "#1A1F29",   # active / chip (legacy key — kept)
    "chip":          "#1A1F29",
    "bg_input":      "#12141B",   # input fields

    # Borders
    "border":        "#1F2430",   # card border
    "border_subtle": "#1D212B",   # fine separator (legacy key — kept)
    "bd_fine":       "#1D212B",
    "bd_input":      "#2A303C",

    # Text
    "text_primary":  "#E6E9EF",
    "fg2":           "#B4BCCC",   # secondary text
    "fg3":           "#9AA2B4",   # tertiary text
    "text_secondary":"#6E7688",   # UPPERCASE labels (legacy key — kept)
    "label":         "#6E7688",
    "text_muted":    "#5C6474",   # muted (legacy key — kept)
    "mute":          "#5C6474",
    "text_code":     "#B4BCCC",   # monospace / rule logic

    # Severity
    "critical":      "#F04452",
    "high":          "#FF8A3D",
    "medium":        "#F5C842",
    "low":           "#00D4AA",
    "info":          "#6E7688",

    # Severity tints (badge bg / border)
    "critical_bg":   "#1D1518", "critical_bd": "#3A2A2E",
    "high_bg":       "#1F1811", "high_bd":     "#3A2B1B",
    "medium_bg":     "#1E1B12", "medium_bd":   "#38311B",
    "low_bg":        "#101C1A", "low_bd":      "#1B3A34",

    # Accent
    "accent":        "#00D4AA",
    "accent_dim":    "#00D4AA22",

    # Tags
    "tag_bg":        "#1A1F29",
    "tag_text":      "#B4BCCC",

    # Status
    "status_ingesting": "#00D4AA",
    "status_error":     "#F04452",

    # Chart
    "chart_bg":      "#151821",
    "chart_grid":    "#1D212B",
    "chart_axis":    "#232733",
    "chart_line_1":  "#00D4AA",   # all events
    "chart_line_2":  "#F04452",   # detections

    # Donut palette (6 slices, decreasing)
    "donut": ["#00D4AA", "#00A88C", "#00806E", "#5A6B7A", "#3E4757", "#2A303C"],
}

# ── LIGHT ─────────────────────────────────────────────────────
LIGHT = {
    "bg_primary":    "#F6F7F9",
    "panel":         "#F1F3F6",
    "bg_secondary":  "#FFFFFF",
    "card":          "#FFFFFF",
    "hover":         "#F3F5F8",
    "bg_tertiary":   "#EEF1F5",
    "chip":          "#EEF1F5",
    "bg_input":      "#FFFFFF",

    "border":        "#E3E7EE",
    "border_subtle": "#E6E9EF",
    "bd_fine":       "#E6E9EF",
    "bd_input":      "#D3D9E2",

    "text_primary":  "#12141B",
    "fg2":           "#374151",
    "fg3":           "#4B5563",
    "text_secondary":"#6B7280",
    "label":         "#6B7280",
    "text_muted":    "#6B7280",
    "mute":          "#6B7280",
    "text_code":     "#374151",

    "critical":      "#F04452",
    "high":          "#FF8A3D",
    "medium":        "#F5C842",
    "low":           "#00D4AA",
    "info":          "#6B7280",

    "critical_bg":   "#FDECEE", "critical_bd": "#F6C6CC",
    "high_bg":       "#FFF2E4", "high_bd":     "#FFD9B2",
    "medium_bg":     "#FFF8DF", "medium_bd":   "#F0E1A0",
    "low_bg":        "#E4FBF5", "low_bd":      "#AEEADB",

    "accent":        "#00D4AA",
    "accent_dim":    "#00D4AA22",

    "tag_bg":        "#EEF1F5",
    "tag_text":      "#374151",

    "status_ingesting": "#00D4AA",
    "status_error":     "#F04452",

    "chart_bg":      "#FFFFFF",
    "chart_grid":    "#E6E9EF",
    "chart_axis":    "#D3D9E2",
    "chart_line_1":  "#00D4AA",
    "chart_line_2":  "#F04452",

    "donut": ["#00D4AA", "#00A88C", "#00806E", "#5A6B7A", "#7C8797", "#AEB6C4"],
}

THEMES = {
    "dark":  DARK,
    "light": LIGHT,
}


# ── Severity helpers ──────────────────────────────────────────

def get_severity_color(score, t):
    """Returns colour based on risk score."""
    if score >= 75:
        return t["critical"]
    elif score >= 50:
        return t["high"]
    elif score >= 25:
        return t["medium"]
    return t["low"]


def get_severity_label(score):
    """Returns severity label based on risk score."""
    if score >= 75:
        return "CRITICAL"
    elif score >= 50:
        return "HIGH"
    elif score >= 25:
        return "MEDIUM"
    return "LOW"


def get_detection_color(status, t):
    """Returns colour for ALERT or CLEAR status."""
    return t["critical"] if status == "ALERT" else t["low"]


def severity_class(status, matches=0):
    """
    Maps a detection status/matches to a CSS badge class
    (used with .cla-badge). Returns 'critical' | 'high' | 'medium' | 'clear'.
    """
    if status != "ALERT":
        return "clear"
    if matches >= 10:
        return "critical"
    if matches >= 5:
        return "high"
    return "medium"


# ── Tag abbreviations ─────────────────────────────────────────

DETECTION_TAGS = {
    "failed_logins":     "BF",
    "iam_changes":       "IAM",
    "credential_abuse":  "KEY",
    "critical_events":   "CTL",
    "s3_exfiltration":   "S3PUB",
    "ec2_suspicious":    "EC2",
    "lambda_abuse":      "LMB",
    "data_exfiltration": "S3DL",
    "role_chaining":     "ROOT",
    "iam_enumeration":   "ENUM",
    "api_calls_by_ip":   "API",
}


# ── MITRE ATT&CK mapping ──────────────────────────────────────

MITRE_MAPPING = {
    "failed_logins":     ("T1110", "Brute Force"),
    "iam_changes":       ("T1098", "Account Manipulation"),
    "credential_abuse":  ("T1078", "Valid Accounts"),
    "critical_events":   ("T1562", "Impair Defenses"),
    "s3_exfiltration":   ("T1530", "Data from Cloud Storage"),
    "ec2_suspicious":    ("T1578", "Modify Cloud Compute"),
    "lambda_abuse":      ("T1648", "Serverless Execution"),
    "data_exfiltration": ("T1041", "Exfiltration over C2"),
    "role_chaining":     ("T1548", "Abuse Elevation Control"),
    "iam_enumeration":   ("T1087", "Account Discovery"),
    "api_calls_by_ip":   ("T1046", "Network Service Discovery"),
}


# ── Rule logic display ────────────────────────────────────────

RULE_LOGIC = {
    "failed_logins": (
        "eventName = ConsoleLogin\n"
        "AND sourceIPAddress COUNT >= threshold\n"
        "GROUP BY sourceIPAddress"
    ),
    "iam_changes": (
        "eventName IN (\n"
        "  CreateUser, DeleteUser,\n"
        "  AttachUserPolicy, DetachUserPolicy,\n"
        "  CreateAccessKey, DeleteAccessKey\n"
        ")"
    ),
    "credential_abuse": (
        "eventName = GetCallerIdentity\n"
        "AND sourceIPAddress DISTINCT COUNT >= 2\n"
        "GROUP BY userName"
    ),
    "critical_events": (
        "eventName IN (\n"
        "  DeleteFlowLogs,\n"
        "  StopLogging,\n"
        "  DeleteTrail\n"
        ")"
    ),
    "s3_exfiltration": (
        "eventName IN (\n"
        "  GetObject, ListBuckets,\n"
        "  GetBucketAcl, ListObjects\n"
        ")\n"
        "AND COUNT >= threshold\n"
        "GROUP BY userName"
    ),
    "ec2_suspicious": (
        "eventName IN (\n"
        "  RunInstances, CreateKeyPair,\n"
        "  AuthorizeSecurityGroupIngress,\n"
        "  ModifyInstanceAttribute\n"
        ")"
    ),
    "lambda_abuse": (
        "eventName IN (\n"
        "  UpdateFunctionCode,\n"
        "  UpdateFunctionConfiguration,\n"
        "  AddPermission, CreateFunction\n"
        ")"
    ),
    "data_exfiltration": (
        "eventName IN (\n"
        "  DeleteFlowLogs,\n"
        "  CreateVpcPeeringConnection,\n"
        "  StopLogging, DeleteTrail\n"
        ")"
    ),
    "role_chaining": (
        "eventName = AssumeRole\n"
        "AND COUNT >= threshold\n"
        "GROUP BY userName"
    ),
    "iam_enumeration": (
        "eventName IN (\n"
        "  ListUsers, ListRoles,\n"
        "  ListPolicies, ListGroups,\n"
        "  GetAccountAuthorizationDetails\n"
        ")\n"
        "AND COUNT >= threshold\n"
        "GROUP BY userName"
    ),
    "api_calls_by_ip": (
        "eventName = *\n"
        "AND COUNT >= threshold\n"
        "GROUP BY sourceIPAddress"
    ),
}


# ── Plotly helpers ────────────────────────────────────────────

def hex_to_rgba(hex_color, alpha=0.12):
    """Converts #RRGGBB to an rgba() string for Plotly fillcolor."""
    h = hex_color.lstrip("#")
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def plotly_layout(t):
    """
    Base Plotly layout matching the design spec (section 6).
    Applied to every chart for visual consistency.
    """
    return {
        "paper_bgcolor": t["chart_bg"],
        "plot_bgcolor":  t["chart_bg"],
        "font": {
            "family": "Inter, system-ui, sans-serif",
            "size":   11,
            "color":  t["fg2"],
        },
        "margin": {"l": 0, "r": 0, "t": 8, "b": 0},
        "xaxis": {
            "gridcolor":     t["chart_grid"],
            "zeroline":      False,
            "linecolor":     t["chart_axis"],
            "tickfont": {"family": "JetBrains Mono, monospace",
                         "size": 9, "color": t["mute"]},
        },
        "yaxis": {
            "gridcolor":     t["chart_grid"],
            "zeroline":      False,
            "showline":      False,
            "tickfont": {"family": "JetBrains Mono, monospace",
                         "size": 9, "color": t["mute"]},
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "font":    {"size": 10, "color": t["fg2"]},
        },
        "hoverlabel": {
            "bgcolor":     t["chip"],
            "bordercolor": t["bd_input"],
            "font": {"family": "JetBrains Mono, monospace",
                     "size": 11, "color": t["text_primary"]},
        },
    }