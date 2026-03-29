import pandas as pd 

class DataValidator:
    # Columns that DataFrame MUST HAvE
    REQUIRED_COLUMNS = [
        "eventTime",
        "eventName",
        "eventSource",
        "sourceIPAddress",
        "userName"
    ]

    def validate_schema(self, df):
        """
        checks that all required columns exist.
        Input : Raw Dataframe
        Output : True if valid, false otherwise
        """
        missing = []

        for col in self.REQUIRED_COLUMNS:
                if col not in df.columns:
                     missing.append(col)

        if missing:
             print(f"[ERROR] Missing columns: {missing}")
             return False 
        print("[INFO schema valid]")
        return True
    
    def clean_data(self, df):
         """
         cleans the DataFrame 
         Input : Raw DataFrame
         Output : clean Dataframe 
         """
         initial_count = len(df)
         
         # Remove rows without date 
         
         df = df.dropna(subset= ["eventTime"])

         # Remove rows without eventName

         df = df[df["eventName"]!= ""]

         # Reset index after deletion
         df = df.reset_index(drop = True)

         final_count = len(df)
         removed = initial_count - final_count
         print(f"[INFO]{removed} rows removed - {final_count} rows remaining")

         return df