import json
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

class AWSConnector:

    def __init__(self, region="us-east-1"):
        self.region = region
        self.client = None

    def connect(self):
        """Initialise la connexion AWS avec credentials .env"""
        try:
            self.client = boto3.client(
                "cloudtrail",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=self.region
            )
            print("[INFO] Connexion AWS établie")
        except NoCredentialsError:
            print("[ERROR] Credentials introuvables")
            self.client = None

    def fetch_logs(self, source="file", file_path=None,
                   start_time=None, end_time=None, max_events=50):
        """
        Entrée  : source + paramètres
        Sortie  : list[dict] — toujours uniforme
        """
        if source == "file":
            return self._load_from_file(file_path)
        elif source == "aws":
            return self._load_from_aws(start_time, end_time, max_events)
        else:
            print(f"[ERROR] Source inconnue : {source}")
            return []

    def _load_from_file(self, file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            events = data.get("Records", [])
            print(f"[INFO] {len(events)} événements chargés depuis {file_path}")
            return events
        except FileNotFoundError:
            print(f"[ERROR] Fichier introuvable : {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON invalide : {e}")
            return []

    def _load_from_aws(self, start_time, end_time, max_events):
        if not self.client:
            print("[ERROR] Appelle connect() d'abord")
            return []
        try:
            response = self.client.lookup_events(
                StartTime=start_time,
                EndTime=end_time,
                MaxResults=max_events
            )
            events = response.get("Events", [])
            print(f"[INFO] {len(events)} événements récupérés depuis AWS")
            return events
        except ClientError as e:
            print(f"[ERROR] AWS : {e}")
            return []