# src/analysis/heuristic_engine.py

import pandas as pd
from .detectors.iam_detector import IAMDetector
from .detectors.s3_detector import S3Detector
from .detectors.ec2_detector import EC2Detector
from .detectors.network_detector import NetworkDetector
from .detectors.lambda_detector import LambdaDetector


class HeuristicEngine:
    """
    Facade orchestrating all security detectors.
    Single entry point for the rest of the application.
    Aggregates results from all specialized detectors.
    """

    def __init__(self):
        # Each detector handles its own domain
        self.iam     = IAMDetector()
        self.s3      = S3Detector()
        self.ec2     = EC2Detector()
        self.network = NetworkDetector()
        self.lambda_ = LambdaDetector()

    # ─── IAM detections ──────────────────────────────────────

    def detect_failed_logins(self, df, threshold=3):
        """Delegates to IAMDetector"""
        return self.iam.detect_failed_logins(df, threshold)

    def detect_iam_changes(self, df):
        """Delegates to IAMDetector"""
        return self.iam.detect_iam_changes(df)

    def detect_iam_enumeration(self, df, threshold=3):
        """Delegates to IAMDetector"""
        return self.iam.detect_iam_enumeration(df, threshold)

    def detect_credential_abuse(self, df, ip_threshold=2):
        """Delegates to IAMDetector"""
        return self.iam.detect_credential_abuse(df, ip_threshold)

    def detect_role_chaining(self, df, threshold=3):
        """Delegates to IAMDetector"""
        return self.iam.detect_role_chaining(df, threshold)

    def count_api_calls_by_ip(self, df, threshold=10):
        """Delegates to IAMDetector"""
        return self.iam.count_api_calls_by_ip(df, threshold)

    # ─── S3 detections ───────────────────────────────────────

    def detect_s3_exfiltration(self, df, threshold=5):
        """Delegates to S3Detector"""
        return self.s3.detect_s3_exfiltration(df, threshold)

    # ─── EC2 detections ──────────────────────────────────────

    def detect_ec2_suspicious_activity(self, df):
        """Delegates to EC2Detector"""
        return self.ec2.detect_ec2_suspicious_activity(df)

    # ─── Network detections ──────────────────────────────────

    def detect_data_exfiltration(self, df):
        """Delegates to NetworkDetector"""
        return self.network.detect_data_exfiltration(df)

    def detect_critical_events(self, df):
        """Delegates to NetworkDetector"""
        return self.network.detect_critical_events(df)

    # ─── Lambda detections ───────────────────────────────────

    def detect_lambda_abuse(self, df):
        """Delegates to LambdaDetector"""
        return self.lambda_.detect_lambda_abuse(df)

    # ─── Master method ───────────────────────────────────────

    def run_all_detections(self, df):
        """
        Runs all detectors and returns a consolidated summary.
        Single call to get the full security picture.

        Input  : clean DataFrame from DataValidator
        Output : dict with all detection results
        """
        return {
            # IAM
            "failed_logins":      self.detect_failed_logins(df),
            "iam_changes":        self.detect_iam_changes(df),
            "iam_enumeration":    self.detect_iam_enumeration(df),
            "credential_abuse":   self.detect_credential_abuse(df),
            "role_chaining":      self.detect_role_chaining(df),
            "api_calls_by_ip":    self.count_api_calls_by_ip(df),
            # S3
            "s3_exfiltration":    self.detect_s3_exfiltration(df),
            # EC2
            "ec2_suspicious":     self.detect_ec2_suspicious_activity(df),
            # Network
            "data_exfiltration":  self.detect_data_exfiltration(df),
            "critical_events":    self.detect_critical_events(df),
            # Lambda
            "lambda_abuse":       self.detect_lambda_abuse(df)
        }