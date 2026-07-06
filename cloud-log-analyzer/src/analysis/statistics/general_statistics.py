# src/analysis/statistics/general_statistics.py

import pandas as pd


class GeneralStatistics:
    """
    Computes general traffic statistics from CloudTrail data.
    Pure descriptive stats — no security judgment, just numbers.
    """

    def total_events(self, df):
        """
        Counts total number of events in the DataFrame.

        Input  : clean DataFrame from DataValidator
        Output : integer
        """
        return len(df)

    def top_services(self, df, top_n=5):
        """
        Returns the most frequently called AWS services.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with eventSource and count, sorted descending
        """
        if df.empty:
            return pd.DataFrame(columns=["eventSource", "count"])

        counts = (
            df
            .groupby("eventSource")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        return counts.head(top_n).reset_index(drop=True)

    def unique_ip_count(self, df):
        """
        Counts the number of distinct source IP addresses.

        Input  : clean DataFrame from DataValidator
        Output : integer
        """
        if df.empty:
            return 0

        return df["sourceIPAddress"].nunique()

    def top_users(self, df, top_n=5):
        """
        Returns the most active users by event count.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with userName and count, sorted descending
        """
        if df.empty:
            return pd.DataFrame(columns=["userName", "count"])

        counts = (
            df
            .groupby("userName")
            .size()
            .reset_index(name="count")
            .sort_values("count", ascending=False)
        )

        return counts.head(top_n).reset_index(drop=True)

    def events_per_hour(self, df):
        """
        Aggregates event counts by hour — useful for timeline visualization.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with hour and count, sorted chronologically
        """
        if df.empty:
            return pd.DataFrame(columns=["hour", "count"])

        df_copy = df.copy()

        # Floor each timestamp to the hour (10:23 -> 10:00)
        df_copy["hour"] = df_copy["eventTime"].dt.floor("h")

        counts = (
            df_copy
            .groupby("hour")
            .size()
            .reset_index(name="count")
            .sort_values("hour")
        )

        return counts.reset_index(drop=True)