

import boto3
from datetime import datetime, timezone, timedelta
# ---- CONFIG ----
BUCKET_NAME = "dhanas3bucketobjectcleanup"     # <-- replace with your bucket
AGE_THRESHOLD_DAYS = 30              # final submission value
# For quick testing only, you may temporarily use minutes instead:
# AGE_THRESHOLD = timedelta(minutes=5) --> Uncomment this for testing
AGE_THRESHOLD = timedelta(days=AGE_THRESHOLD_DAYS)
s3_client = boto3.client("s3")
def lambda_handler(event, context):
   now_utc = datetime.now(timezone.utc)
   cutoff = now_utc - AGE_THRESHOLD
   deleted_keys = []
   scanned_count = 0
   paginator = s3_client.get_paginator("list_objects_v2")
   # Never assume a single page of results -- always paginate.
   for page in paginator.paginate(Bucket=BUCKET_NAME):
       for obj in page.get("Contents", []):
           scanned_count += 1
           key = obj["Key"]
           last_modified = obj["LastModified"]  # already timezone-aware (UTC)
           if last_modified < cutoff:
               s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
               deleted_keys.append(key)
               print(f"Deleted stale object: {key} (last modified {last_modified})")
           else:
               print(f"Kept object: {key} (last modified {last_modified})")
   summary = {
       "bucket": BUCKET_NAME,
       "scanned_objects": scanned_count,
       "deleted_count": len(deleted_keys),
       "deleted_keys": deleted_keys,
   }
   print(f"Cleanup summary: {summary}")
   return summary
