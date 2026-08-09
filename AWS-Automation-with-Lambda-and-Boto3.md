# AWS-Automation-with-Lambda-and-Boto3


## 📂 AWS Automation Assignments with Lambda & Boto3

This repository contains step‑by‑step assignment tasks, each organized in its own folder.  
Inside every **TaskX** folder you’ll find:
- 📘 `README.md` → detailed walkthrough with screenshots  
- 🐍 `.py` → AWS Lambda function code  
- 📜 `.json` → IAM user or bucket policy files  

### 🔎 Assignment Index
1. **Task1 – Automated S3 Bucket Cleanup (Objects Older Than 30 Days)**  
2. **Task2 – Automated EBS Snapshot Creation and Cleanup**  
3. **Task3 – Auto‑Tagging EC2 Instances on Launch**  
6. **Task6 – Audit S3 Buckets for Public Access and Notify**


   --------------------------------------------------------------------------

AWS-Automation-with-Lambda-and-Boto3/
│
├── AWS-Automation-with-Lambda-and-Boto3.md
│
├── Task1/
│   ├── README.md
│   ├── lambda_function.py
│   └── s3-cleanup-inline-policy.json
│
├── Task2/
│   ├── README.md
│   ├── ebs-snapshot-inline-policy.json
│   └── lambda_function.py
│
├── Task3/
│   ├── README.md
│   ├── lambda_function.py
│   └── EC2AutoTagInlinePolicy.json
│
└── Task6/
    ├── README.md
    ├── lambda_function.py
    ├── S3PublicAuditInlinePolicy.json
    └── s3-audit-test-bucket-dhana.json
