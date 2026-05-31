# src/analysis/detectors/s3_detector.py

import pandas as pd


class S3Detector:
    """
    Detects S3-related attacks and data exfiltration attempts.
    Covers: mass download, bucket discovery, permission probing.
    """

    # S3 events indicating data exfiltration
    S3_EXFILTRATION_EVENTS = [
        "GetObject",        # downloading a file — mass usage = exfiltration
        "ListBuckets",      # discovering all buckets
        "ListObjects",      # listing bucket contents
        "GetBucketAcl",     # checking bucket permissions
        "GetBucketPolicy",  # reading bucket policy
        "GetBucketLocation" # discovering bucket region
    ]

    def detect_s3_exfiltration(self, df, threshold=5):
        """
        Detects mass S3 access patterns indicating data theft.
        Attacker downloads many files or probes many buckets.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with suspicious users and their S3 event count
        """
        if df.empty:
            return pd.DataFrame(columns=["userName", "s3_event_count"])

        s3_events = df[df["eventName"].isin(self.S3_EXFILTRATION_EVENTS)]

        if s3_events.empty:
            return pd.DataFrame(columns=["userName", "s3_event_count"])

        counts = (
            s3_events
            .groupby("userName")
            .size()
            .reset_index(name="s3_event_count")
        )

        suspicious = counts[counts["s3_event_count"] >= threshold]

        return suspicious.sort_values(
            "s3_event_count", ascending=False
        ).reset_index(drop=True)