# src/analysis/detectors/network_detector.py

import pandas as pd


class NetworkDetector:
    """
    Detects network-level attacks and VPC exfiltration.
    Covers: VPC peering abuse, flow log deletion, ACL manipulation.
    """

    # Network events indicating exfiltration or covering tracks
    NETWORK_EXFILTRATION_EVENTS = [
        "CreateVpcPeeringConnection",   # connecting to external VPC
        "AcceptVpcPeeringConnection",   # accepting external peering
        "CreateNetworkAcl",             # creating network rules
        "CreateNetworkAclEntry",        # adding network rules
        "DeleteNetworkAcl",             # removing network protection
        "DeleteFlowLogs",               # deleting VPC logs — very suspicious
        "StopLogging",                  # stopping CloudTrail — critical alert
        "DeleteTrail",                  # deleting audit trail — critical alert
        "ModifyVpcAttribute"            # modifying VPC settings
    ]

    # Critical events that require immediate attention
    CRITICAL_EVENTS = [
        "DeleteFlowLogs",
        "StopLogging",
        "DeleteTrail"
    ]

    def detect_data_exfiltration(self, df):
        """
        Detects network-level exfiltration and log tampering.
        DeleteFlowLogs / StopLogging / DeleteTrail = attacker covering tracks.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with all suspicious network events found
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        return df[
            df["eventName"].isin(self.NETWORK_EXFILTRATION_EVENTS)
        ].reset_index(drop=True)

    def detect_critical_events(self, df):
        """
        Detects critical events requiring immediate response.
        Attacker deleting logs = active incident in progress.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with critical events only
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        return df[
            df["eventName"].isin(self.CRITICAL_EVENTS)
        ].reset_index(drop=True)