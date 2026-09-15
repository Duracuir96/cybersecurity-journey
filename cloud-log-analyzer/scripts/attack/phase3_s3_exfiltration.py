# scripts/attack/phase3_s3_exfiltration.py
#
# Phase 3 — S3 exfiltration (mass object download).
# LAB ONLY. Mirrors: phase3_s3_exfiltration.sh
# Exercises: detect_s3_exfiltration()
#
# Creates a small test bucket, uploads dummy files, then downloads them
# in bulk — the read pattern the detector looks for. The bucket itself
# is NOT deleted here — cleaned up by teardown.py.

import io
import boto3

try:
    from config import PROFILE, EXFIL_BUCKET, EXFIL_OBJECT_COUNT, REGION
except ImportError:
    PROFILE = "attacker"
    EXFIL_BUCKET = "voldi-lab-exfil-demo"
    EXFIL_OBJECT_COUNT = 8
    REGION = "us-east-1"


def run_s3_exfiltration(profile_name=PROFILE, bucket=EXFIL_BUCKET,
                        count=EXFIL_OBJECT_COUNT):
    """
    Simulates bulk S3 read access: list buckets, create a bucket with
    dummy objects, then download all of them — mass GetObject pattern.
    """
    session = boto3.Session(profile_name=profile_name)
    s3 = session.client("s3", region_name=REGION)

    print(f"[*] Phase 3 — S3 Exfiltration (bucket: {bucket})")

    print("[*] ListBuckets...")
    existing = s3.list_buckets()
    print(f"[+] Found {len(existing['Buckets'])} buckets")

    print(f"[*] Creating test bucket: {bucket}")
    if REGION == "us-east-1":
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )

    print(f"[*] Uploading {count} dummy objects...")
    for i in range(count):
        s3.put_object(Bucket=bucket, Key=f"file_{i}.txt",
                      Body=io.BytesIO(f"dummy data {i}".encode()))
    print(f"[+] Uploaded {count} objects")

    print("[*] GetBucketAcl...")
    s3.get_bucket_acl(Bucket=bucket)

    print(f"[*] Downloading all {count} objects (GetObject x{count})...")
    for i in range(count):
        s3.get_object(Bucket=bucket, Key=f"file_{i}.txt")
    print(f"[+] Downloaded {count} objects")

    print("[+] Phase 3 complete — check CloudTrail in ~5-15 min")
    print("    Expected: detect_s3_exfiltration -> ALERT")
    print("    Remember: run teardown.py afterwards to remove the bucket.")


if __name__ == "__main__":
    run_s3_exfiltration()