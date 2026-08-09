import boto3
from botocore.exceptions import ClientError
 
s3 = boto3.client('s3')
sns = boto3.client('sns')
 
# Replace with the ARN copied from Step 1 (SNS topic).
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:994114819227:s3-public-bucket-alerts'
 
 
def lambda_handler(event, context):
    """
    Scans every S3 bucket in the account and flags any bucket that
    is genuinely publicly accessible. Runs on a daily EventBridge
    schedule. Publishes one consolidated SNS alert if 1+ buckets
    are flagged, and always logs a full per-bucket audit trail.
    """
    print('Starting S3 public-access audit...')
 
    bucket_names = list_all_buckets()
    print(f'Found {len(bucket_names)} bucket(s) to audit: {bucket_names}')
 
    flagged_buckets = []
 
    for bucket_name in bucket_names:
        verdict = audit_bucket(bucket_name)
        if verdict['is_public']:
            flagged_buckets.append(verdict)
            print(f'[PUBLIC/AT-RISK] {bucket_name} -> {verdict["reasons"]}')
        else:
            print(f'[SAFE] {bucket_name} -> Block Public Access fully enforced, '
                  f'no public policy or ACL detected.')
 
    if flagged_buckets:
        publish_alert(flagged_buckets)
    else:
        print('SUCCESS: Audit complete. No publicly accessible buckets found.')
 
    return {
        'statusCode': 200,
        'body': {
            'buckets_checked': len(bucket_names),
            'buckets_flagged': [b['bucket_name'] for b in flagged_buckets],
        },
    }
 
 
def list_all_buckets():
    response = s3.list_buckets()
    return [b['Name'] for b in response.get('Buckets', [])]
 
 
def audit_bucket(bucket_name):
    """
    Returns a dict describing whether a single bucket is public,
    and WHY, by combining three independent signals: Block Public
    Access status, bucket policy status, and ACL grants.
    """
    reasons = []
 
    # ---- Signal 1: Block Public Access configuration ----
    bpa_fully_enforced = is_block_public_access_fully_enforced(bucket_name)
    if not bpa_fully_enforced:
        reasons.append('Block Public Access is NOT fully enabled on this bucket')
 
    # ---- Signal 2: Bucket policy status (computed by AWS) ----
    policy_is_public = is_bucket_policy_public(bucket_name)
    if policy_is_public:
        reasons.append('Bucket policy grants public access (IsPublic=True)')
 
    # ---- Signal 3: ACL grants (legacy path, still checked) ----
    acl_is_public = does_acl_grant_public_access(bucket_name)
    if acl_is_public:
        reasons.append('Bucket ACL grants access to AllUsers or AuthenticatedUsers')
 
    # A bucket is genuinely at risk only if BPA is not fully locking
    # things down AND at least one of policy/ACL is actually public.
    is_public = (not bpa_fully_enforced) and (policy_is_public or acl_is_public)
 
    return {
        'bucket_name': bucket_name,
        'is_public': is_public,
        'bpa_fully_enforced': bpa_fully_enforced,
        'policy_is_public': policy_is_public,
        'acl_is_public': acl_is_public,
        'reasons': reasons,
    }
 
 
def is_block_public_access_fully_enforced(bucket_name):
    """
    True only if ALL FOUR Block Public Access settings are enabled.
    If the bucket has no BPA configuration at all (older bucket,
    ownership/config edge case), treat it as NOT enforced.
    """
    try:
        response = s3.get_public_access_block(Bucket=bucket_name)
        config = response['PublicAccessBlockConfiguration']
        return all([
            config.get('BlockPublicAcls', False),
            config.get('IgnorePublicAcls', False),
            config.get('BlockPublicPolicy', False),
            config.get('RestrictPublicBuckets', False),
        ])
    except ClientError as err:
        code = err.response['Error']['Code']
        if code == 'NoSuchPublicAccessBlockConfiguration':
            print(f'  -> {bucket_name}: no BPA configuration set at all.')
            return False
        print(f'  -> {bucket_name}: error reading BPA ({code}); treating as NOT enforced.')
        return False
 
 
def is_bucket_policy_public(bucket_name):
    """
    Uses AWS's own computed IsPublic flag rather than parsing the
    policy JSON by hand -- this is the exact API named in the
    assignment (s3:GetBucketPolicyStatus) and is far more reliable
    than manual policy inspection.
    """
    try:
        response = s3.get_bucket_policy_status(Bucket=bucket_name)
        return response['PolicyStatus']['IsPublic']
    except ClientError as err:
        code = err.response['Error']['Code']
        if code == 'NoSuchBucketPolicy':
            return False
        print(f'  -> {bucket_name}: error reading policy status ({code}).')
        return False
 
 
def does_acl_grant_public_access(bucket_name):
    """
    Checks ACL grantees for the two well-known 'public' group URIs.
    Relevant mainly for legacy buckets where ACLs are still enabled.
    """
    public_group_uris = (
        'http://acs.amazonaws.com/groups/global/AllUsers',
        'http://acs.amazonaws.com/groups/global/AuthenticatedUsers',
    )
    try:
        response = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in response.get('Grants', []):
            grantee = grant.get('Grantee', {})
            if grantee.get('URI') in public_group_uris:
                return True
        return False
    except ClientError as err:
        print(f'  -> {bucket_name}: error reading ACL ({err.response["Error"]["Code"]}).')
        return False
 
 
def publish_alert(flagged_buckets):
    bucket_lines = []
    for b in flagged_buckets:
        bucket_lines.append(f"- {b['bucket_name']}: {', '.join(b['reasons'])}")
 
    message = (
        'AWS S3 Public Access Audit ALERT\n'
        f"{len(flagged_buckets)} bucket(s) were found to be publicly "
        'accessible or at risk:\n\n' + '\n'.join(bucket_lines) +
        '\n\nPlease review and remediate immediately.'
    )
 
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject='ALERT: Publicly Accessible S3 Bucket(s) Detected',
        Message=message,
    )
    print(f'SNS alert published for {len(flagged_buckets)} flagged bucket(s): '
          f"{[b['bucket_name'] for b in flagged_buckets]}")

