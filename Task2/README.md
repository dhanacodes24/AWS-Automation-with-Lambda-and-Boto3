<div align="center">

### AWS DEVOPS ASSIGNMENT

# 💽 Automated EBS Snapshot Backup & Cleanup

<img src="https://img.shields.io/badge/Task-02-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Service-EC2%20%7C%20EBS%20%7C%20Lambda%20%7C%20IAM%20%7C%20EventBridge-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Runtime-Python%203.12%20(boto3)-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Status-Completed%20%E2%9C%94-success?style=flat-square"/>

### 🎯 Automate weekly EBS backups and prune snapshots past their retention period.

</div>

---

## 📘 Overview

> This assignment automates **EBS volume backups**: a Lambda function creates a tagged snapshot of a target volume, then cleans up old snapshots (older than the retention window) that carry the same tag — running on a **weekly EventBridge schedule**.

| 🔑 Key | Detail |
|---|---|
| **Objective** | Create weekly EBS snapshots and delete ones older than 30 days |
| **Trigger** | EventBridge Schedule (weekly) |
| **Core AWS Services** | EC2, EBS, Lambda, IAM, EventBridge |
| **Language / SDK** | Python 3.12 + boto3 |
| **Author** | *Moana* |

---

## 🗂️ Table of Contents

1. [🏗️ Architecture Diagram](#️-architecture-diagram)
2. [✅ Prerequisites](#-prerequisites)
3. [💽 Step 1 — EBS Volume Setup](#-step-1--ebs-volume-setup)
4. [🔐 Step 2 — IAM Role & Policy](#-step-2--iam-role--policy)
5. [🧠 Step 3 — Lambda Function Setup](#-step-3--lambda-function-setup)
6. [🐍 Step 4 — Lambda Code (Boto3)](#-step-4--lambda-code-boto3)
7. [⏰ Step 5 — EventBridge Weekly Schedule](#-step-5--eventbridge-weekly-schedule)
8. [🧪 Step 6 — Testing & Verification](#-step-6--testing--verification)
9. [💬 Discussion — Lambda vs. AWS Data Lifecycle Manager](#-discussion--lambda-vs-aws-data-lifecycle-manager)
10. [🏁 Summary](#-summary)

---

## 🏗️ Architecture Diagram

```mermaid
flowchart LR
    A["⏰ EventBridge Schedule<br/>(weekly)"] -->|invoke| B["🧠 Lambda Function<br/>ebs-snapshot-backup<br/>(Python 3.12 + boto3)"]
    B --> C["1️⃣ CreateSnapshot<br/>+ Tag CreatedBy=Lambda-Backup"]
    B --> D["2️⃣ DescribeSnapshots<br/>filter by tag, owned by self"]
    D --> E["3️⃣ DeleteSnapshot<br/>if older than retention period"]
    C --> F["🖨️ Print created + deleted snapshot IDs"]
    E --> F

    style A fill:#0969DA,color:#fff
    style B fill:#0B3D91,color:#fff
    style F fill:#2DA44E,color:#fff
```

> 💡 **Flow in one line:** `Create + Tag Snapshot ➜ List Tagged Snapshots ➜ Delete Expired Ones ➜ Log`

---

## ✅ Prerequisites

- [x] AWS account with Console + CLI access
- [x] An EBS volume identified or created — note its **Volume ID**
- [x] IAM permissions to create Roles, Lambda functions, and EventBridge Schedules

---

## 💽 Step 1 — EBS Volume Setup

| Setting | Value |
|---|---|
| **Volume ID** | `vol-xxxxxxxxxxxxxxxxx` |
| **Availability Zone** | Match your working region's AZ |
| **Size** | Any (8 GiB default is fine for testing) |

📸 **Steps and Screenshots:**

------------------------------------
**Created new Ec2 Instance**
------------------------------------
<img width="1119" height="554" alt="image" src="https://github.com/user-attachments/assets/9b48d33a-e657-4fda-87e0-ff268e6d76bb" />

------------------------------------
**Noted the EBS volume ID**
------------------------------------
<img width="1120" height="549" alt="image" src="https://github.com/user-attachments/assets/f0030e25-7a45-4edc-bb26-5f3723adfa84" />

------------------------------------


---

## 🔐 Step 2 — IAM Role & Policy

**Role name:** `lambda-ebs-backup-role`

| Action | Purpose |
|---|---|
| `ec2:CreateSnapshot` | Create a new snapshot of the target volume |
| `ec2:DescribeSnapshots` | List existing tagged snapshots to evaluate age |
| `ec2:DeleteSnapshot` | Remove snapshots past the retention window |
| `ec2:CreateTags` | Tag new snapshots for identification (`CreatedBy=Lambda-Backup`) |

<details>
<summary>📄 <b>Click to expand — Inline IAM Policy JSON</b></summary>

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "SnapshotLifecycleActions",
			"Effect": "Allow",
			"Action": [
				"ec2:CreateSnapshot",
				"ec2:DescribeSnapshots",
				"ec2:DeleteSnapshot",
				"ec2:CreateTags"
			],
			"Resource": "*"
		},
		{
			"Sid": "AllowCloudWatchLogging",
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "arn:aws:logs:*:*:*"
		}
	]
}

```
</details>

📸 **Steps and Screenshots:**

------------------------------------
** Created IAM role --> lambda-ebs-snapshot-role **
------------------------------------
<img width="1196" height="597" alt="image" src="https://github.com/user-attachments/assets/f1ce3cc0-3a39-4e5f-a787-c16c38b7f781" />

------------------------------------
** Added inline policy **
------------------------------------
<img width="1195" height="535" alt="image" src="https://github.com/user-attachments/assets/6c000df5-8988-4bf8-a8e6-713250ce95a7" />

-----------------------------------

**Confirmed that policy is attached to the role**
-----------------------------------

<img width="1200" height="555" alt="image" src="https://github.com/user-attachments/assets/1160a1f9-d6c3-4f6e-afb3-65e1c5fbaab4" />

------------------------------------
## 🧠 Step 3 — Lambda Function Setup

| Setting | Value |
|---|---|
| **Function name** | `ebs-snapshot-lifecycle` |
| **Runtime** | Python 3.12 |
| **Execution role** | `lambda-ebs-snapshot-role` |
| **Timeout** | 1 min |
| **Env var** `VOLUME_ID` | `vol-xxxxxxxxxxxxxxxxx` |
| **Env var** `RETENTION_DAYS` | `30` |

📸 **Steps and Screenshots:**

----------------------------------
**Selected Author from scratch and selected custom execution role lambda-ebs-snapshot-role**
----------------------------------
<img width="1198" height="543" alt="image" src="https://github.com/user-attachments/assets/c32d8a09-c5a0-48b1-93c0-8a9e98e9dbc5" />

----------------------------------
**Created Lambda function**
----------------------------------
<img width="1201" height="354" alt="image" src="https://github.com/user-attachments/assets/fa860a48-2893-419a-9547-7a8de1f9b7a1" />

----------------------------------


---

## 🐍 Step 4 — Lambda Code (Boto3)

<details>
<summary>📄 <b>Click to expand — lambda_function.py</b></summary>

```python

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


```
</details>

📸 **Steps and Screenshots:**


----------------------------------
** Added and deployed Lambda function**
----------------------------------
<img width="1193" height="513" alt="image" src="https://github.com/user-attachments/assets/25b9ec29-b3ad-49d7-a205-f2dfe1050e24" />

----------------------------------
**Created test event***

----------------------------------
<img width="1186" height="552" alt="image" src="https://github.com/user-attachments/assets/35c6ed37-87a8-4ee9-b5bc-a0dedb082e41" />

----------------------------------
** Tested manually ***
----------------------------------
<img width="1180" height="604" alt="image" src="https://github.com/user-attachments/assets/88d968d0-50b3-4454-8034-85589cae0b89" />

----------------------------------
** Output and functional Logs**
----------------------------------
<img width="1186" height="408" alt="image" src="https://github.com/user-attachments/assets/24456dae-7b2b-4b86-9381-a975d612107c" />

----------------------------------
***Confirmed new snapshot generated and its generated with our volume id 
----------------------------------
<img width="1191" height="556" alt="image" src="https://github.com/user-attachments/assets/e83a6e48-6818-447d-8886-595b27664497" />

----------------------------------
**Verified CloudWatch logs***
----------------------------------

<img width="1196" height="580" alt="image" src="https://github.com/user-attachments/assets/99aa322a-77a2-4f4a-a6d7-07d5f0979914" />

-------------------------------------
## ⏰ Step 5 — EventBridge Weekly Schedule

| Setting | Chosen Value |
|---|---|
| **Schedule type** | Recurring — `rate(7 days)` or `cron(0 3 ? * MON *)` |
| **Action after completion** | `NONE` (keeps the recurring schedule active) |
| **Execution role** | *Create new role for this schedule* |
| **Target** | `ebs-snapshot-backup` Lambda |

📸 **Steps and Screenshots:**

----------------------------------
** Created weekly EventBridge Schedule
----------------------------------
<img width="1261" height="626" alt="image" src="https://github.com/user-attachments/assets/e967b906-eee0-43bd-94bc-e34ae5a936fb" />

----------------------------------
***Added EventBridge trigger in lambda function**
----------------------------------
<img width="1261" height="607" alt="image" src="https://github.com/user-attachments/assets/5361776e-d094-4815-979d-9be53dc0c401" />

----------------------------------
***Weekly trigger Schedule**
----------------------------------
<img width="1259" height="573" alt="image" src="https://github.com/user-attachments/assets/c82cb961-ea98-431a-976c-776e3aac0eef" />

----------------------------------


---

## 🧪 Step 6 — Testing & Verification


📸 **Steps and Screenshot:**

🧪 **For testing purpose deployed policy policy with 5 minutes threshold**

-------------------------------------
** Changed threshold to 5 minutes ***
-------------------------------------
<img width="1158" height="551" alt="image" src="https://github.com/user-attachments/assets/69aaadcd-8d28-4ffe-a264-9ef21062f728" />

-------------------------------------
** Manually triggered Lambda function and waited below are Before and After results**
-------------------------------------
*BEFORE trigger there was existing snapshot with Snapshot ID
-------------------------------------

<img width="1258" height="402" alt="image" src="https://github.com/user-attachments/assets/c87c3f5b-ff4b-41e7-a317-492c4179873b" />

-------------------------------------

*AFTER trigger old snapshot was deleted and new Snapshot generated 
-------------------------------------
**Lambda Function output**
<img width="1122" height="499" alt="image" src="https://github.com/user-attachments/assets/2bfa1ad5-c910-4adc-ae01-64f17e7b2e71" />

**Old Snapshot deleted and new Snapshot generated**
<img width="1261" height="295" alt="image" src="https://github.com/user-attachments/assets/91f387d7-85ad-417e-abb2-ed475946616b" />

**Functional Logs**
<img width="1250" height="583" alt="image" src="https://github.com/user-attachments/assets/aa256c43-3240-41bf-84eb-ce8b954b36f0" />

**Newly generated  Snapshot**

<img width="1250" height="583" alt="image" src="https://github.com/user-attachments/assets/0d67e371-50a6-418e-b541-fd730e0778d7" />

***CloudWatch Logs**

<img width="1258" height="512" alt="image" src="https://github.com/user-attachments/assets/020d776b-1ae4-4d36-9df8-466c631afdf4" />

-------------------------------------

| ✅ Check | Expected Outcome |
|---|---|
| Lambda execution status | `Succeeded`, no errors |
| New snapshot | Appears in EC2 → Snapshots, tagged `CreatedBy=Lambda-Backup` |
| Old snapshot cleanup | Snapshots older than `RETENTION_DAYS` removed |
| Logs | Print statements show created + deleted snapshot IDs |

---

## 💬 Discussion — Lambda vs. AWS Data Lifecycle Manager

> **AWS Data Lifecycle Manager (DLM)** natively schedules snapshot creation and retention with **zero code** and is the right default choice for standard backup policies. **Lambda is still the better choice** when you need **custom retention logic** beyond simple age-based rules, **cross-account/cross-region snapshot copies**, or **notifications and downstream automation** (e.g. SNS alerts, updating a CMDB, triggering a restore test) tied to the backup lifecycle.

---

---


## 🏁 Summary

<div align="center">

<img src="https://img.shields.io/badge/Result-Automated%20Weekly%20EBS%20Backup%20%2B%20Retention-2DA44E?style=for-the-badge"/>

**Create + Tag ➜ Filter by Tag ➜ Delete Expired ➜ Log** — a self-maintaining backup pipeline running on a weekly clock.

</div>

---

<div align="center">

<img src="https://img.shields.io/badge/AWS-EC2%2FEBS-orange?style=flat-square&logo=amazonec2"/>
<img src="https://img.shields.io/badge/AWS-Lambda-orange?style=flat-square&logo=awslambda"/>
<img src="https://img.shields.io/badge/AWS-EventBridge-orange?style=flat-square&logo=amazoneventbridge"/>
<img src="https://img.shields.io/badge/AWS-IAM-orange?style=flat-square&logo=amazoniam"/>
<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white"/>

</div>

