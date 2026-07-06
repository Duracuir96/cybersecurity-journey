# src/analysis/statistics/security_statistics.py

import pandas as pd


class SecurityStatistics:
    """
    Computes security posture statistics from HeuristicEngine results.
    Aggregates and correlates detection outputs into actionable insights.
    """

    # Weight of each detection in the global risk score.
    # Higher weight = more critical if this detection fires.
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

    def risk_score(self, results):
        """
        Computes a global risk score from 0 to 100.
        Each active detection contributes its weight to the total.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : integer between 0 and 100
        """
        score = 0

        for name, result_df in results.items():
            if not result_df.empty:
                weight = self.DETECTION_WEIGHTS.get(name, 5)
                score += weight

        # Cap at 100 — risk score is a percentage-like indicator
        return min(score, 100)

    def cross_detection_entities(self, results, min_detections=2):
        """
        Finds IPs and usernames appearing in multiple detection results.
        An entity flagged by several detectors is far more suspicious
        than one flagged by a single detector.

        Input  : dict from HeuristicEngine.run_all_detections()
        Output : DataFrame with entity, detection_count, detections list
        """
        # Map each entity (IP or username) to the set of detections
        # that flagged it
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

        # Keep only entities flagged by multiple detectors
        rows = []
        for entity, detections in entity_detections.items():
            if len(detections) >= min_detections:
                rows.append({
                    "entity": entity,
                    "detection_count": len(detections),
                    "detections": ", ".join(sorted(detections))
                })

        result_df = pd.DataFrame(
            rows, columns=["entity", "detection_count", "detections"]
        )

        if not result_df.empty:
            result_df = result_df.sort_values(
                "detection_count", ascending=False
            ).reset_index(drop=True)

        return result_df