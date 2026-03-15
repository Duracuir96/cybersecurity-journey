import boto3 
import os 
import sys
from dotenv import load_dotenv 

load_dotenv()

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_REGION:
    print("ERROR: Missing AWS environment variables.")
    print("Make sure your .env file contains:")
    print("AWS_ACCESS_KEY_ID=your_key_here")
    print("AWS_SECRET_ACCESS_KEY=your_secret_here")
    print("AWS_SECRET_ACCESS_KEY=your_secret_here")
    sys.exit(1)

cloudtrail = boto3.client('cloudtrail', region_name= 'us-east-1')
response = cloudtrail.describe_trails()
cloudtrail = boto3.client('cloudtrail',aws_access_key_id = AWS_ACCESS_KEY_ID, aws_secret_access_key = AWS_SECRET_ACCESS_KEY ,  region_name = "us-east-1")
response = cloudtrail.lookup_events(
            MaxResults =10
        )
print(response)