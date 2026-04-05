import pandas as pd 

class LogParser:
    def parse_json(self, raw_logs):
        """
        input : list[dict] brut (vient de AWSConnector)
        output : list[dict] avec seulemnt les champs utiles 
        """
        parsed = []

        for event in raw_logs:
            # Detect the format - AWs has the key "EventName"
            is_aws_format = "EventName" in event
            if is_aws_format:
                parsed.append({
                "eventTime":       event.get("EventTime", None),
                "eventName":       event.get("EventName", ""),
                "eventSource":     event.get("EventSource", ""),
                "sourceIPAddress": event.get("SourceIPAddress", "unknown"),
                "userName":        event.get("Username", "unknown")
                })

            else:

                # userIdentity nested 
                user_identity = event.get("userIdentity",{})
                user_name = user_identity.get("userName","unknown")

                # keep just only 5 variables 

                parsed.append({
                    "eventTime":  event.get("eventTime", ""),
                    "eventName": event.get("eventName", ""),
                    "eventSource": event.get("eventSource", ""),
                    "sourceIPAddress": event.get("sourceIPAddress", "unknown"),
                    "userName":        user_name

            })
        return parsed 

    def to_dataframe(self, parsed_logs):
        """
        input : lict[dict] propre (from parse_json)
        output: structured Dataframe Pandas 
        """
        df = pd.DataFrame(parsed_logs)
         # Guard — if DataFrame is empty, return it with correct columns
        if df.empty:
            return pd.DataFrame(columns= [
                "eventTime", "eventName", "eventSource",
                "sourceIPAddress", "userName"
            ])

        df["eventTime"] = pd.to_datetime(df["eventTime"])

        return df 