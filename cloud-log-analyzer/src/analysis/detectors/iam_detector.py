# src/analysis/detectors/iam_detector.py

import pandas as pd


class IAMDetector:
    """
    Detects IAM-related attacks and suspicious behaviors.
    Covers: brute force, privilege escalation, enumeration,
            credential abuse, role chaining, high volume API calls.
    """

    # Events that modify IAM — dangerous by definition
    IAM_DANGEROUS_EVENTS = [
        "CreateUser",
        "DeleteUser",
        "AttachUserPolicy",
        "DetachUserPolicy",
        "CreateAccessKey",
        "DeleteAccessKey",
        "PutUserPolicy",
        "DeleteUserPolicy"
    ]

    # Events used during IAM reconnaissance phase
    IAM_ENUMERATION_EVENTS = [
        "ListUsers",
        "ListRoles",
        "ListPolicies",
        "ListGroups",
        "ListAttachedUserPolicies",
        "ListAttachedRolePolicies",
        "GetAccountAuthorizationDetails",  # most dangerous — dumps everything
        "GetAccountSummary"
    ]

    def detect_failed_logins(self, df, threshold=3):
        """
        Detects IPs attempting ConsoleLogin more than threshold times.
        Indicates a brute force or credential stuffing attack.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with suspicious IPs and their login count
        """
        if df.empty:
            return pd.DataFrame(columns=["sourceIPAddress", "login_count"])

        logins = df[df["eventName"] == "ConsoleLogin"]

        if logins.empty:
            return pd.DataFrame(columns=["sourceIPAddress", "login_count"])

        counts = (
            logins
            .groupby("sourceIPAddress")
            .size()
            .reset_index(name="login_count")
        )

        suspicious = counts[counts["login_count"] >= threshold]

        return suspicious.sort_values(
            "login_count", ascending=False
        ).reset_index(drop=True)

    def detect_iam_changes(self, df):
        """
        Detects dangerous IAM modification events.
        Any match in IAM_DANGEROUS_EVENTS is suspicious by definition.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with all dangerous IAM events found
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        return df[
            df["eventName"].isin(self.IAM_DANGEROUS_EVENTS)
        ].reset_index(drop=True)

    def detect_iam_enumeration(self, df, threshold=3):
        """
        Detects users performing IAM reconnaissance.
        Multiple enumeration calls from same user = attacker mapping the environment.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with suspicious users and their enumeration count
        """
        if df.empty:
            return pd.DataFrame(columns=["userName", "enumeration_count"])

        enum_events = df[df["eventName"].isin(self.IAM_ENUMERATION_EVENTS)]

        if enum_events.empty:
            return pd.DataFrame(columns=["userName", "enumeration_count"])

        counts = (
            enum_events
            .groupby("userName")
            .size()
            .reset_index(name="enumeration_count")
        )

        suspicious = counts[counts["enumeration_count"] >= threshold]

        return suspicious.sort_values(
            "enumeration_count", ascending=False
        ).reset_index(drop=True)

    def detect_credential_abuse(self, df, ip_threshold=2):
        """
        Detects stolen credentials being used from multiple IPs.
        GetCallerIdentity is the first call attackers make to verify a stolen key.
        Same user calling from multiple IPs = key potentially compromised.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with suspicious users and their unique IP count
        """
        if df.empty:
            return pd.DataFrame(columns=["userName", "unique_ip_count"])

        # GetCallerIdentity = attacker verifying the stolen key works
        caller_identity = df[df["eventName"] == "GetCallerIdentity"]

        if caller_identity.empty:
            return pd.DataFrame(columns=["userName", "unique_ip_count"])

        # Count unique IPs per user — multiple IPs = suspicious
        ip_counts = (
            caller_identity
            .groupby("userName")["sourceIPAddress"]
            .nunique()
            .reset_index(name="unique_ip_count")
        )

        suspicious = ip_counts[ip_counts["unique_ip_count"] >= ip_threshold]

        return suspicious.sort_values(
            "unique_ip_count", ascending=False
        ).reset_index(drop=True)

    def detect_role_chaining(self, df, threshold=3):
        """
        Detects privilege escalation via role chaining.
        Attacker assumes one role, then another, then another
        to progressively gain higher privileges.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with users assuming an abnormal number of roles
        """
        if df.empty:
            return pd.DataFrame(columns=["userName", "assume_role_count"])

        assume_events = df[df["eventName"] == "AssumeRole"]

        if assume_events.empty:
            return pd.DataFrame(columns=["userName", "assume_role_count"])

        counts = (
            assume_events
            .groupby("userName")
            .size()
            .reset_index(name="assume_role_count")
        )

        suspicious = counts[counts["assume_role_count"] >= threshold]

        return suspicious.sort_values(
            "assume_role_count", ascending=False
        ).reset_index(drop=True)

    def count_api_calls_by_ip(self, df, threshold=10):
        """
        Counts total API calls per IP address.
        High volume from single IP = potential scanner or automated attack.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with IPs exceeding the call threshold
        """
        if df.empty:
            return pd.DataFrame(columns=["sourceIPAddress", "call_count"])

        counts = (
            df
            .groupby("sourceIPAddress")
            .size()
            .reset_index(name="call_count")
        )

        suspicious = counts[counts["call_count"] >= threshold]

        return suspicious.sort_values(
            "call_count", ascending=False
        ).reset_index(drop=True)