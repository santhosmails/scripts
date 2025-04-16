import boto3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()

def get_regions(ec2_client):
    """Fetches all available regions."""
    try:
        regions_response = ec2_client.describe_regions()
        return [region['RegionName'] for region in regions_response['Regions']]
    except Exception as e:
        logger.error(f"Error fetching regions: {e}")
        return []

def fetch_ec2_data(ec2):
    """Fetches snapshots, volumes, and running instances for a given EC2 client."""
    try:
        snapshots = ec2.describe_snapshots(OwnerIds=['self'])['Snapshots']
        volumes = ec2.describe_volumes()['Volumes']
        instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])['Reservations']
        return snapshots, volumes, instances
    except Exception as e:
        logger.error(f"Error fetching EC2 data: {e}")
        return [], [], []

def process_snapshots(snapshot_response, volume_ids):
    """Processes snapshots to identify stale ones."""
    for snapshot in snapshot_response:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        if not volume_id:
            logger.info(f"Snapshot {snapshot_id} is not associated with any volume and can be deleted.")
        elif volume_id not in volume_ids:
            logger.info(f"Snapshot {snapshot_id} is associated with a non-existent volume {volume_id} and can be deleted.")

def lambda_handler(event=None, context=None):
    """Main handler function."""
    logger.info("Starting the process to check for stale EBS snapshots...")

    ec2_client = boto3.client('ec2')
    regions = get_regions(ec2_client)

    if not regions:
        logger.error("No regions found. Exiting.")
        return

    for region in regions:
        logger.info(f"Checking region: {region}")
        ec2 = boto3.client('ec2', region_name=region)

        snapshots, volumes, instances = fetch_ec2_data(ec2)

        # Gather active instance IDs
        active_instance_ids = {
            instance['InstanceId']
            for reservation in instances
            for instance in reservation['Instances']
        }

        # Gather volume IDs
        volume_ids = {volume['VolumeId'] for volume in volumes}

        # Process snapshots
        process_snapshots(snapshots, volume_ids)

    logger.info("Process completed.")

# Entry point for the script
if __name__ == "__main__":
    lambda_handler()
