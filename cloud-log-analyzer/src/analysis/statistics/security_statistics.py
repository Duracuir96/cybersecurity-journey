# src/analysis/statistics/security_statistics.py

import pandas as pd


class SecurityStatistics:
    """
    Computes security posture statistics from HeuristicEngine results.
    Aggregates and correlates detection outputs into actionable insights.

    Risk scoring (v2.0 — Risk-Based Alerting):
      The score is accumulated PER ENTITY (an IP or a username), not per
      detection type. An entity flagged by several detectors, or seen with
      high intensity, accumulates a higher score. The global risk score is
      the score of the single most dangerous entity — which is how real SIEMs
      (Splunk RBA, Sentinel) reason about incidents.
    """

    # Base weight of each detection.
    DETECTION_WEIGHTS = {
        "critical_events":    25,  # log tampering — active incident
        "credential_abuse":   20,  # stolen key in use
        "data_exfiltration":  15,  # network exfiltration / log deletion
        "iam_changes":        15,  # privilege escalation
        "s3_exfiltration":    10,  # data theft
        "ec2_suspicious":     10,  # compute compromise
        "lambda_abuse":       10,  # serverless tampering
        "role_chaining":       8,  # progressive escalation
        "failed_logins":       7,  # brute force
        "iam_enumeration":     5,  # reconnaissance
        "api_calls_by_ip":     5,  # high volume scanning
    }

    # Per-detection cap for (base weight + volumetric bonus).
    RISK_CAPS = {
        "failed_logins":     21,
        "iam_changes":       25,
        "s3_exfiltration":   20,
        "credential_abuse":  30,
        "role_chaining":     16,
        "iam_enumeration":   12,
        "api_calls_by_ip":   12,
    }

    # How each detection contributes to an entity's score.
    #   entity_col : column identifying the actor (IP or user)
    #   count_col  : per-row intensity column, or None for raw-event detections
    #   coeff      : bonus = intensity * coeff  (int division when < 1)
    #   div        : intensity is divided by this before applying coeff
    # Raw-event detections (count_col=None) contribute their base weight, plus
    # an optional per-event bonus (used by iam_changes).
    ENTITY_CONFIG = {
        "failed_logins":     {"entity_col": "sourceIPAddress", "count_col": "login_count",       "div": 5,  "coeff": 1},
        "iam_enumeration":   {"entity_col": "userName",        "count_col": "enumeration_count", "div": 1,  "coeff": 1},
        "credential_abuse":  {"entity_col": "userName",        "count_col": "unique_ip_count",   "div": 1,  "coeff": 5},
        "role_chaining":     {"entity_col": "userName",        "count_col": "assume_role_count", "div": 1,  "coeff": 2},
        "api_calls_by_ip":   {"entity_col": "sourceIPAddress", "count_col": "call_count",        "div": 20, "coeff": 1},
        "s3_exfiltration":   {"entity_col": "userName",        "count_col": "s3_event_count",    "div": 10, "coeff": 1},
        "iam_changes":       {"entity_col": "userName",        "count_col": None,                "per_event": 2},
        "critical_events":   {"entity_col": "userName",        "count_col": None},
        "ec2_suspicious":    {"entity_col": "sourceIPAddress", "count_col": None},
        "lambda_abuse":      {"entity_col": "userName",        "count_col": None},
        "data_exfiltration": {"entity_col": "sourceIPAddress", "count_col": None},
    }

    # ─── Detection summary ───────────────────────────────────

    def detection_summary(self, results):
        """
        Summarizes how many events each detector found.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : DataFrame with detection name, count, status
        """
        if not results:
            return pd.DataFrame(columns=["detection", "count", "status"])

        summary = []
        for name, result_df in results.items():
            count = len(result_df)
            summary.append({
                "detection": name,
                "count": count,
                "status": "ALERT" if count > 0 else "CLEAR"
            })

        summary_df = pd.DataFrame(summary)
        return summary_df.sort_values(
            "count", ascending=False
        ).reset_index(drop=True)

    # ─── Risk score by entity (v2.0) ─────────────────────────

    def risk_score_by_entity(self, results):
        """
        Accumulates a risk score per entity (IP or username).

        Each detection contributes to the entities it flagged. Detections with
        a per-row intensity column (login_count, call_count, ...) contribute a
        volumetric weight; raw-event detections contribute their base weight
        (plus an optional per-event bonus). Each detection's contribution to a
        single entity is capped, then the entity's total is capped at 100.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : dict {entity: score} sorted high to low
        """
        scores = {}

        for name, cfg in self.ENTITY_CONFIG.items():
            df = self._get(results, name)
            if df.empty:
                continue

            entity_col = cfg["entity_col"]
            if entity_col not in df.columns:
                continue

            base = self.DETECTION_WEIGHTS[name]
            cap = self.RISK_CAPS.get(name)

            if cfg["count_col"] is None:
                # Raw-event detection: weight per entity, +bonus per event.
                per_event = cfg.get("per_event", 0)
                grouped = df.groupby(entity_col).size()
                for entity, n in grouped.items():
                    if pd.isna(entity):
                        continue
                    contrib = base + int(n) * per_event
                    if cap is not None:
                        contrib = min(contrib, cap)
                    scores[entity] = scores.get(entity, 0) + contrib
            else:
                # Volumetric detection: intensity is per row, per entity.
                count_col = cfg["count_col"]
                if count_col not in df.columns:
                    # Column missing — fall back to base weight per entity.
                    for entity in df[entity_col].dropna().unique():
                        scores[entity] = scores.get(entity, 0) + base
                    continue

                div = cfg["div"]
                coeff = cfg["coeff"]
                # Highest intensity row per entity drives that entity's bonus.
                grouped = df.groupby(entity_col)[count_col].max()
                for entity, intensity in grouped.items():
                    if pd.isna(entity):
                        continue
                    bonus = int(intensity) // div * coeff
                    contrib = base + bonus
                    if cap is not None:
                        contrib = min(contrib, cap)
                    scores[entity] = scores.get(entity, 0) + contrib

        # Cap each entity at 100 and sort by score descending.
        scores = {e: min(s, 100) for e, s in scores.items()}
        return dict(sorted(scores.items(), key=lambda kv: kv[1], reverse=True))

    def risk_score(self, results):
        """
        Global risk score from 0 to 100.

        v2.0 — defined as the score of the most dangerous entity. The public
        interface is unchanged (returns a plain int), so full_report(), the
        dashboard KPI and the email notifier keep working untouched.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : integer between 0 and 100
        """
        entity_scores = self.risk_score_by_entity(results)
        if not entity_scores:
            return 0
        return min(max(entity_scores.values()), 100)

    # ─── Helpers ─────────────────────────────────────────────

    @staticmethod
    def _get(results, name):
        """Returns the result DataFrame for a detection, or an empty one."""
        df = results.get(name)
        return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

    # ─── Cross-detection entities ────────────────────────────

    def cross_detection_entities(self, results, min_detections=2):
        """
        Finds IPs and usernames appearing in multiple detection results.
        An entity flagged by several detectors is far more suspicious
        than one flagged by a single detector.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : DataFrame with entity, detection_count, detections, risk_score
        """
        entity_detections = {}

        for name, result_df in results.items():
            if result_df.empty:
                continue

            entities = set()
            if "sourceIPAddress" in result_df.columns:
                entities.update(result_df["sourceIPAddress"].dropna().unique())
            if "userName" in result_df.columns:
                entities.update(result_df["userName"].dropna().unique())

            for entity in entities:
                entity_detections.setdefault(entity, set()).add(name)

        # Per-entity risk scores (reused so the table matches the global score).
        entity_scores = self.risk_score_by_entity(results)

        rows = []
        for entity, detections in entity_detections.items():
            if len(detections) >= min_detections:
                rows.append({
                    "entity": entity,
                    "detection_count": len(detections),
                    "detections": ", ".join(sorted(detections)),
                    "risk_score": entity_scores.get(entity, 0),
                })

        result_df = pd.DataFrame(
            rows,
            columns=["entity", "detection_count", "detections", "risk_score"],
        )
        if not result_df.empty:
            result_df = result_df.sort_values(
                "risk_score", ascending=False
            ).reset_index(drop=True)

        return result_df