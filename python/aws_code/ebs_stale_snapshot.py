import boto3
import json
from datetime import datetime

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()

def lambda_handler():
    ec2_client = boto3.client('ec2')
    regions_response = ec2_client.describe_regions()
    regions = [region['RegionName'] for region in regions_response['Regions']]

    for region in regions:
        print(f"Checking region: {region}")
        ec2 = boto3.client('ec2', region_name=region)

        snapshot_response = ec2.describe_snapshots(OwnerIds=['self'])
        instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        volume_response = ec2.describe_volumes()

        active_instance_ids = set()
        for reservation in instances_response['Reservations']:
            for instance in reservation['Instances']:
                active_instance_ids.add(instance['InstanceId'])

        volume_ids = set()
        for volume in volume_response['Volumes']:
            volume_ids.add(volume['VolumeId'])

        for snapshot in snapshot_response['Snapshots']:
            snapshot_id = snapshot['SnapshotId']
            volume_id = snapshot['VolumeId']

            if not volume_id:
                print(f"{snapshot_id} is not associated with any volume and it can be deleted")

            if volume_id not in volume_ids:
                print(f"{snapshot_id} volume does not exist and it can be deleted")

lambda_handler()
