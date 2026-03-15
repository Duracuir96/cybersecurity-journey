# main.py
from data_collection.aws_connector import AWSConnector

connector = AWSConnector()

# ── Mode fichier local (développement) ──────────────────
events = connector.fetch_logs(
    source="file",
    file_path="..\data\sample_cloudtrail.json"
)

if events:
    print("Premier événement :", events[0])
    print("Noms des événements :", [e["eventName"] for e in events])

# ── Mode AWS réel (décommenter quand prêt) ───────────────
# connector.connect()
# logs = connector.fetch_logs(
#     source="aws",
#     max_events=10
# )
# if logs:
#     print(f"{len(logs)} logs reçus")
#     print(logs[0])