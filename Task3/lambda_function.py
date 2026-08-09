import boto3
import datetime
 
ec2 = boto3.client('ec2')
 
def lambda_handler(event, context):
    # 1. Extract the instance ID from the EventBridge event
    detail = event.get('detail', {})
    instance_id = detail.get('instance-id')
 
    if not instance_id:
        print('No instance-id found in event, skipping.')
        return {'statusCode': 400, 'body': 'Missing instance-id'}
 
    # 2. Build the tag set
    launch_date = datetime.datetime.utcnow().strftime('%Y-%m-%d')
 
    tags = [
        {'Key': 'LaunchDate', 'Value': launch_date},
        {'Key': 'Environment', 'Value': 'Development'},
        {'Key': 'ManagedBy', 'Value': 'auto-tagging-lambda'}
    ]
 
    # 3. Apply the tags to the instance
    ec2.create_tags(Resources=[instance_id], Tags=tags)
 
    # 4. Print a confirmation message
    print(f'Successfully tagged instance {instance_id} '
          f'with LaunchDate={launch_date}')
 
    return {
        'statusCode': 200,
        'body': f'Tagged {instance_id} successfully'
    }
