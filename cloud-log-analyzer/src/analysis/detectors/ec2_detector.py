# src/analysis/detectors/ec2_detector.py

import pandas as pd


class EC2Detector:
    """
    Detects EC2-related attacks.
    Covers: unauthorized instance launch, security group modification,
            SSH key creation, crypto-mining indicators.
    """

    # EC2 events that indicate compromise or abuse
    EC2_SUSPICIOUS_EVENTS = [
        "RunInstances",                  # launching new instances (crypto-mining)
        "AuthorizeSecurityGroupIngress", # opening inbound ports (backdoor)
        "AuthorizeSecurityGroupEgress",  # opening outbound ports (exfiltration)
        "ModifyInstanceAttribute",       # modifying running instance
        "CreateKeyPair",                 # creating SSH key (persistence)
        "ImportKeyPair",                 # importing external SSH key
        "CreateSecurityGroup",           # creating new security group
        "DeleteFlowLogs"                 # deleting network logs (covering tracks)
    ]

    def detect_ec2_suspicious_activity(self, df):
        """
        Detects dangerous EC2 actions indicating instance compromise.
        All matched events are suspicious by definition.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with all suspicious EC2 events found
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        return df[
            df["eventName"].isin(self.EC2_SUSPICIOUS_EVENTS)
        ].reset_index(drop=True)