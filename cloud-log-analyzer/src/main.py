# main.py
from data_collection.aws_connector import AWSConnector
from data_processing.log_parser import LogParser
from datetime import datetime, timedelta
from data_processing.data_validator import DataValidator
connector = AWSConnector()

        # Layer 1 - collect

# ── Mode fichier local (développement) ──────────────────
# raw_logs = connector.fetch_logs(
#     source="file",
#     file_path="..\data\sample_cloudtrail.json"
# )

# if raw_logs:
#     print("Premier événement :", raw_logs[0])
#     print("Noms des événements :", [e["eventName"] for e in raw_logs])

# ── Mode AWS réel (décommenter quand prêt) ───────────────
connector.connect()
end_time = datetime.utcnow()
start_time = end_time -timedelta(hours=24)
logs = connector.fetch_logs(
    source="aws",
    max_events=10,
    start_time = start_time,
    end_time = end_time,
)
if logs:
    print(f"{len(logs)} logs reçus")
    print(logs[0])

        # Layer 2 - parser

parser = LogParser()
parsed_logs = parser.parse_json(logs)
df = parser.to_dataframe(parsed_logs)

print(df.shape)
print(df.dtypes)
print(df.head())


        # Layer 3 - validate

validator = DataValidator()
is_valid = validator.validate_schema(df)

if is_valid:
    df = validator.clean_data(df)
    print(df.head())
else:
    print("[STOP] invalid DataFrame -check the parser")