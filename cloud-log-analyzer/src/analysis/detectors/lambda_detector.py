# src/analysis/detectors/lambda_detector.py

import pandas as pd


class LambdaDetector:
    """
    Detects Lambda-related attacks and serverless abuse.
    Covers: function code modification, permission escalation,
            unauthorized function creation.
    """

    # Lambda events indicating function tampering or abuse
    LAMBDA_SUSPICIOUS_EVENTS = [
        "UpdateFunctionCode",          # modifying function code — backdoor injection
        "UpdateFunctionConfiguration", # modifying function settings
        "CreateFunction",              # creating new function
        "AddPermission",               # adding execution permissions
        "AddLayerVersionPermission",   # adding layer permissions
        "PublishLayerVersion",         # publishing malicious layer
        "InvokeFunction"               # invoking function (combined with above = abuse)
    ]

    def detect_lambda_abuse(self, df):
        """
        Detects suspicious Lambda activity indicating serverless abuse.
        UpdateFunctionCode is the most critical — code injection vector.

        Input  : clean DataFrame from DataValidator
        Output : DataFrame with all suspicious Lambda events found
        """
        if df.empty:
            return pd.DataFrame(columns=df.columns)

        return df[
            df["eventName"].isin(self.LAMBDA_SUSPICIOUS_EVENTS)
        ].reset_index(drop=True)