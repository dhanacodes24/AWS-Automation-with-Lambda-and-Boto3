import boto3
from datetime import datetime, timezone, timedelta
# ---- CONFIG ----
VOLUME_ID = "vol-01f8bdd100ec6d30d"   # <-- replace with your EBS volume ID
RETENTION_DAYS = 30                       # final submission value
# For quick testing only, you may temporarily use a smaller window:
# RETENTION_DAYS = 0
TAG_KEY = "CreatedBy"
TAG_VALUE = "Lambda-Backup"
ec2_client = boto3.client("ec2")
def lambda_handler(event, context):
   now_utc = datetime.now(timezone.utc)
   cutoff = now_utc - timedelta(days=RETENTION_DAYS)
   # 1. Create a new snapshot of the target volume
   snapshot = ec2_client.create_snapshot(
       VolumeId=VOLUME_ID,
       Description=f"Automated backup of {VOLUME_ID} via Lambda",
       TagSpecifications=[
           {
               "ResourceType": "snapshot",
               "Tags": [
                   {"Key": TAG_KEY, "Value": TAG_VALUE},
                   {"Key": "SourceVolume", "Value": VOLUME_ID},
               ],
           }
       ],
   )
   created_id = snapshot["SnapshotId"]
   print(f"Created snapshot: {created_id} for volume {VOLUME_ID}")
   # 2. List snapshots owned by this account carrying our tag
   response = ec2_client.describe_snapshots(
       OwnerIds=["self"],
       Filters=[{"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]}],
   )
   deleted_ids = []
   for snap in response.get("Snapshots", []):
       snap_id = snap["SnapshotId"]
       start_time = snap["StartTime"]  # timezone-aware (UTC)
       # Never delete the snapshot we just created in this same run
       if snap_id == created_id:
           continue
       if start_time < cutoff:
           ec2_client.delete_snapshot(SnapshotId=snap_id)
           deleted_ids.append(snap_id)
           print(f"Deleted stale snapshot: {snap_id} (created {start_time})")
       else:
           print(f"Kept snapshot: {snap_id} (created {start_time})")
   summary = {
       "volume_id": VOLUME_ID,
       "created_snapshot": created_id,
       "deleted_count": len(deleted_ids),
       "deleted_snapshots": deleted_ids,
   }
   print(f"Snapshot lifecycle summary: {summary}")
   return summary




