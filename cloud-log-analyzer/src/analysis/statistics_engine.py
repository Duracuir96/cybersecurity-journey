# src/analysis/statistics_engine.py

from .statistics.general_statistics import GeneralStatistics
from .statistics.security_statistics import SecurityStatistics


class StatisticsEngine:
    """
    Facade orchestrating general traffic statistics and
    security posture statistics. Single entry point for the dashboard.
    """

    def __init__(self):
        self.general  = GeneralStatistics()
        self.security = SecurityStatistics()

    # ─── General statistics ──────────────────────────────────

    def total_events(self, df):
        """Delegates to GeneralStatistics"""
        return self.general.total_events(df)

    def top_services(self, df, top_n=5):
        """Delegates to GeneralStatistics"""
        return self.general.top_services(df, top_n)

    def unique_ip_count(self, df):
        """Delegates to GeneralStatistics"""
        return self.general.unique_ip_count(df)

    def top_users(self, df, top_n=5):
        """Delegates to GeneralStatistics"""
        return self.general.top_users(df, top_n)

    def events_per_hour(self, df):
        """Delegates to GeneralStatistics"""
        return self.general.events_per_hour(df)

    # ─── Security statistics ─────────────────────────────────

    def detection_summary(self, results):
        """Delegates to SecurityStatistics"""
        return self.security.detection_summary(results)

    def risk_score(self, results):
        """Delegates to SecurityStatistics"""
        return self.security.risk_score(results)

    def cross_detection_entities(self, results, min_detections=2):
        """Delegates to SecurityStatistics"""
        return self.security.cross_detection_entities(results, min_detections)

    # ─── Master method ────────────────────────────────────────

    def full_report(self, df, results):
        """
        Generates a complete statistics report combining
        general traffic stats and security posture stats.

        Input  : clean DataFrame (Layer 3) + detection results (Layer 4)
        Output : dict with all computed statistics
        """
        return {
            "total_events":     self.total_events(df),
            "unique_ips":       self.unique_ip_count(df),
            "top_services":     self.top_services(df),
            "top_users":        self.top_users(df),
            "events_per_hour":  self.events_per_hour(df),
            "detection_summary":        self.detection_summary(results),
            "risk_score":               self.risk_score(results),
            "cross_detection_entities": self.cross_detection_entities(results)
        }