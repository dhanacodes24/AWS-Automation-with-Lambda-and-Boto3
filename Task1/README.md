<div align="center">

### AWS DEVOPS ASSIGNMENT

# 🧹 Automated S3 Bucket Cleanup

<img src="https://img.shields.io/badge/Task-01-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Service-S3%20%7C%20Lambda%20%7C%20IAM-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Runtime-Python%203.12%20(boto3)-blue?style=flat-square"/>
<img src="https://img.shields.io/badge/Status-Completed%20%E2%9C%94-success?style=flat-square"/>

### 🎯 Automatically delete stale S3 objects older than a retention threshold — zero manual cleanup.

</div>

---

## 📘 Overview

> This assignment automates deletion of **stale objects** in an S3 bucket using a Lambda function. The function paginates through all objects, compares each object's `LastModified` timestamp to the current UTC time, and deletes anything older than the retention window (30 days in production).

| 🔑 Key | Detail |
|---|---|
| **Objective** | Delete S3 objects older than 30 days |
| **Trigger** | Manual test event (can be scheduled via EventBridge) |
| **Core AWS Services** | S3, Lambda, IAM |
| **Language / SDK** | Python 3.12 + boto3 |
| **Author** | *Moana* |

---

## 🗂️ Table of Contents

1. [🏗️ Architecture Diagram](#️-architecture-diagram)
2. [✅ Prerequisites](#-prerequisites)
3. [🪣 Step 1 — S3 Bucket Setup](#-step-1--s3-bucket-setup)
4. [🔐 Step 2 — IAM Role & Policy](#-step-2--iam-role--policy)
5. [🧠 Step 3 — Lambda Function Setup](#-step-3--lambda-function-setup)
6. [🐍 Step 4 — Lambda Code (Boto3)](#-step-4--lambda-code-boto3)
7. [🧪 Step 5 — Testing & Verification](#-step-5--testing--verification)
8. [💬 Discussion — Lambda vs. S3 Lifecycle Rules](#-discussion--lambda-vs-s3-lifecycle-rules)
9. [🏁 Summary](#-summary)

---

## 🏗️ Architecture Diagram

```mermaid
flowchart LR
    A["⏰ Manual Trigger<br/>(or EventBridge Schedule)"] -->|invoke| B["🧠 Lambda Function<br/>s3-bucket-cleanup<br/>(Python 3.12 + boto3)"]
    B --> C["1️⃣ List Objects<br/>paginator.paginate()"]
    C --> D["2️⃣ Compare LastModified<br/>vs. now(UTC) - threshold"]
    D --> E["3️⃣ Delete Object<br/>if older than threshold"]
    E --> F["🖨️ Print deleted object keys"]

    style A fill:#0969DA,color:#fff
    style B fill:#0B3D91,color:#fff
    style F fill:#2DA44E,color:#fff
```

> 💡 **Flow in one line:** `List (paginated) ➜ Compare Age ➜ Delete ➜ Log`

---

## ✅ Prerequisites

- [x] AWS account with Console + CLI access
- [x] An S3 bucket created (or ready to create) with a handful of test objects uploaded
- [x] IAM permissions to create Roles and Lambda functions
- [x] Willingness to temporarily lower the age threshold (e.g. minutes) for testing, then reset to 30 days

---

## 🪣 Step 1 — S3 Bucket Setup

$\Large{\textcolor{#87CEEB}{\textbf{ '**STEP 1   Create the S3 Bucket and Upload Test Files**'  }}}$ 


------------------------------------------------------------------
Selected General Purpose > Added Bucket Name
------------------------------------------------------------------

<img width="1222" height="521" alt="image" src="https://github.com/user-attachments/assets/7a9a0d36-e6ff-4267-b401-fdbe9aaf0fbc" />

------------------------------------------------------------------
Checked Block Public Access settings for this bucket
-------------------------------------------------------------------

<img width="1224" height="569" alt="image" src="https://github.com/user-attachments/assets/7a8c0edb-f6c3-4c07-8baf-a0411708b61d" />

------------------------------------------------------------------
Uploaded few sample files
--------------------------------------------------------------------

<img width="1223" height="545" alt="image" src="https://github.com/user-attachments/assets/c6e81c9e-d5e4-4c5d-8613-31e5edf5471b" />

--------------------------------------------------------------------
| Setting | Value |
|---|---|
| **Bucket name** | `dhanas3bucketobjectcleanup` |
| **Region** | e.g. `us-east-1` |
| **Test objects** | Upload 3–5 sample files (`.csv` / `.png`) |



---

## 🔐 Step 2 — IAM Role & Policy

**STEP 2   Create the IAM Role with a Least-Privilege Inline Policy**

**Role name:** `lambda-s3-cleanup-role`

| Action | Purpose |
|---|---|
| `s3:ListBucket` | List/paginate objects in the target bucket |
| `s3:DeleteObject` | Delete objects that exceed the age threshold |

<details>
<summary>📄 <b>Click to expand — Inline IAM Policy JSON</b></summary>

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucketObjects",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::dhanas3bucketobjectcleanup"
    },
    {
      "Sid": "DeleteStaleObjects",
      "Effect": "Allow",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::dhanas3bucketobjectcleanup/*"
    },
    {
      "Sid": "AllowCloudWatchLogging",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}

```
</details>

📸 **Steps and Screenshot:**

-----------------------------------
Selected AWS services and Lambda
-----------------------------------
<img width="1225" height="597" alt="image" src="https://github.com/user-attachments/assets/7c4f0c65-cc2e-4902-8114-99357f2b6731" />

-----------------------------------
Created Role
-----------------------------------

<img width="1226" height="620" alt="image" src="https://github.com/user-attachments/assets/355283af-b421-4edb-b8a1-4c65d2dea9b2" />

-----------------------------------
Created inline Policy
-----------------------------------

<img width="1223" height="618" alt="image" src="https://github.com/user-attachments/assets/effe63f8-6ca0-4217-8776-deebcf575eb5" />

-----------------------------------
Verified policy attached to role
----------------------------------

<img width="1223" height="596" alt="image" src="https://github.com/user-attachments/assets/05bd79d4-8533-4b93-bc07-150afd2b03ea" />

---------------------------------



> ⚠️ **Least privilege:** Both statements are scoped to the specific bucket ARN — never use `"Resource": "*"` for delete permissions in production.

---

## 🧠 Step 3 — Lambda Function Setup

**STEP 3   Create the Lambda Function**

| Setting | Value |
|---|---|
| **Function name** | `s3-stale-object-cleanup` |
| **Runtime** | Python 3.12 |
| **Execution role** | `lambda-s3-cleanup-role` | 
| **Timeout** | 1 min |
| **Env var** `BUCKET_NAME` | `dhanas3bucketobjectcleanup` |
| **Env var** `MAX_AGE_DAYS` | `30` *(temporarily lower for testing)* |

📸 **Steps and Screenshot:**
------------------------------------------
Selected Author from scratch , named s3-stale-object-cleanup
------------------------------------------
<img width="1222" height="621" alt="image" src="https://github.com/user-attachments/assets/8b2269d1-95a3-469b-b4ce-bab4a52ef98e" />

------------------------------------------
Expand Change default execution role → select Use an existing role → pick lambda-s3-cleanup-role from the dropdown ..
-----------------------------------------
<img width="1224" height="624" alt="image" src="https://github.com/user-attachments/assets/67e4c9b2-ae48-4bbb-9a56-31bedf98e46d" />

------------------------------------------
Created Lambda Function
------------------------------------------
<img width="1220" height="429" alt="image" src="https://github.com/user-attachments/assets/1f89cda2-7f53-40d1-b9cb-f8f3a15115cb" />

-----------------------------------------

---

## 🐍 Step 4 — Lambda Code (Boto3)

<details>
<summary>📄 <b>Click to expand — lambda_function.py</b></summary>

```python
import boto3
from datetime import datetime, timezone, timedelta
# ---- CONFIG ----
BUCKET_NAME = "dhanas3bucketobjectcleanup"     # <-- replace with your bucket
AGE_THRESHOLD_DAYS = 30              # final submission value
# For quick testing only, you may temporarily use minutes instead:
# AGE_THRESHOLD = timedelta(minutes=5)
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

```
</details>


📸 **Screenshot and steps**
-------------------------------------
Added lambda function code and deployed 
-----------------------------------------
<img width="1224" height="607" alt="image" src="https://github.com/user-attachments/assets/aa1e7bd7-2ad5-4719-878d-7b5285727037" />

-----------------------------------------
-------------------------------------
<img width="1205" height="486" alt="image" src="https://github.com/user-attachments/assets/ca7b9255-8f30-493c-8a3f-c519e2f1637d" />

--------------------------------------

---

## 🧪 Step 5 — Testing & Verification


📸 **Testing steps and Screenshot:**

🧪 **Test → For testing purpose changed Threshold to 5 mins from 30 days  for testing purpose and Ran Lambda manually**


----------------------------------------------------
1)   Ran Lambda Function with threshold 5 mins 

---------------------------------------------------

<img width="1439" height="617" alt="image" src="https://github.com/user-attachments/assets/cb92fc98-2adf-49ee-b7d5-a6147eea54eb" />

---------------------------------------------------

2) In output we can see files are being deleted

<img width="1419" height="602" alt="image" src="https://github.com/user-attachments/assets/3d2fbe48-bcfa-4ce1-bb25-3b57ee6be0e7" />

--------------------------------------------------

3) In S3 bucket We can see files got  deleted .

 **BEFORE**

<img width="1436" height="597" alt="image" src="https://github.com/user-attachments/assets/06a23854-2ce2-4c75-ae36-5e889b8607d2" />

**AFTER**

<img width="1148" height="574" alt="image" src="https://github.com/user-attachments/assets/eb6befe7-ca0c-4b3f-a682-53b06c6ef58d" />


---------------------------------------------

4) We can verify the same in CloudWatch logs

   <img width="1322" height="612" alt="image" src="https://github.com/user-attachments/assets/2e8108e4-57c2-491f-b935-269b7aa396e7" />

-----------------------------------------

| ✅ Check |  Outcome was as Expected |
|---|---|
| Lambda execution status | `Succeeded`, no errors |
| Deleted object count (test run) | Matches objects older than the lowered test threshold |
| Remaining objects | Only newer files present in the bucket |
| Final code | `MAX_AGE_DAYS` reset to `30` before submission |


---

## 💬 Discussion — Lambda vs. S3 Lifecycle Rules

> In production, **S3 Lifecycle Rules** handle age-based deletion natively with **zero code** — they're cheaper, more reliable, and require no maintenance. **Lambda is the better choice** when cleanup needs **conditional logic** Lifecycle Rules can't express: deleting based on **object naming patterns**, **content inspection**, **cross-service actions** (e.g. notify via SNS, log to DynamoDB before deleting), or **business-rule exceptions** that go beyond a simple age threshold.

---


---

## 🏁 Summary

<div align="center">

<img src="https://img.shields.io/badge/Result-Automated%20S3%20Retention%20Cleanup-2DA44E?style=for-the-badge"/>

**List (paginated) ➜ Compare Age ➜ Delete ➜ Log** — a lightweight, serverless housekeeping pattern for object storage.

</div>

---

<div align="center">

<img src="https://img.shields.io/badge/AWS-S3-orange?style=flat-square&logo=amazons3"/>
<img src="https://img.shields.io/badge/AWS-Lambda-orange?style=flat-square&logo=awslambda"/>
<img src="https://img.shields.io/badge/AWS-IAM-orange?style=flat-square&logo=amazoniam"/>
<img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white"/>

</div>
