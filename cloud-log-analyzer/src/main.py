# main.py
from data_collection.aws_connector import AWSConnector
from data_processing.log_parser import LogParser
from datetime import datetime, timedelta
from data_processing.data_validator import DataValidator
from analysis.heuristic_engine import HeuristicEngine

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

     # layer 4 - analyze 

engine = HeuristicEngine()

print("\n── Failed Login Attempts ────────────────")
failed_logins = engine.detect_failed_logins(df, threshold=3)
print(failed_logins if not failed_logins.empty else "No suspicious logins detected")

print("\n── Dangerous IAM Changes ────────────────")
iam_changes = engine.detect_iam_changes(df)
print(iam_changes if not iam_changes.empty else "No IAM changes detected")

print("\n── High Volume API Callers -──────────────")
api_calls = engine.count_api_calls_by_ip(df, threshold=10)
print(api_calls if not api_calls.empty else "No high volume IPs detected")