# src/analysis/heuristic_engine.py

import pandas as pd 

class HeuristicEngine:
    # IAM event names considered dangerous

    IAM_DANGEROUS_EVENTS =[
        "CreateUser",
        "DeleteUser",
        "AttachUserPolicy",
        "DetachUserPolicy",
        "CreateAccessKey",
        "DeleteAccessKey",
        "PutUserPolicy",
        "DeleteUserPolicy"   
    ]

    def detect_failed_logins(self, df, threshold = 3):
        """
        Detects suspicious IPs that attempted ConsoleLogin
        more than threshold times

        Input: clean DataFrame from DataValidator 
        Output: DataFrame with suspicious IPs and their login count 

        """
        if df.empty:
            return pd.DataFrame(columns =["sourceIPAddress", "login_count"])
        
        # step 1 - keep only ConsoleLogin events 

        logins = df[df["eventName"] == "ConsoleLogin"]

        if logins.empty:
            return pd.DataFrame(columns = ["sourceIPAddress", "login_count"])
        
        # step 2 - count how many times each IP attempted login

        counts = (
            logins
            .groupby("sourceIPAddress")
            .size()
            .reset_index(name = "login_count")
        )

        # step 3 - keep only IPs above the threshold 

        suspicious = counts[counts["login_count"] >= threshold]

        # step 4 - sort from most attempts to least 

        suspicious = suspicious.sort_values("login_count", ascending =False)
        return suspicious.reset_index(drop = True)

    def detect_iam_changes(self,df):
        """
        detects dangerous IAM modifications events.
        Any event in IAM_DANGEROUS_EVENTS is suspicious by definition

        Input : clean DataFrame from DataValidator 
        Output : DataFrame with all dangerous IAM events found 

        """
        if df.empty:
            return pd.DataFrame(columns = df.columns)
        
        # Filter rows where eventName is a known dangerous IAM action

        iam_events = df[df["eventName"].isin(self.IAM_DANGEROUS_EVENTS)]

        return iam_events.reset_index(drop=True)

    def count_api_calls_by_ip(self, df , threshold= 10):
        """
        Counts total API calls per IP address
        Returns IPs that exceed the threshold - potential scanners or attackers 

        Input: clean DataFrame from DataValidator
        Output: DataFrame with IP addresses and their total call count 

        """
        if df.empty:
            return pd.DataFrame(columns= ["sourceIPAddress", "call_count"])
        
        # step 1 - count all events per IP

        counts = (
            df
            .groupby("sourceIPAddress")
            .size()
            .reset_index(name="call_count")
        )

        # step 2 -- keep only IPs above the threshold

        suspicious = counts[counts["call_count"] >= threshold]

        # step 3 - sort from most calls to least 

        suspicious = suspicious.sort_values("call_count", ascending = False)

        return suspicious.reset_index(drop = True)