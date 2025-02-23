from abc import ABC, abstractmethod
import boto3
from collections import defaultdict

class CostRepository(ABC):
    """
    Abstract base class (interface) for fetching AWS cost data.
    """

    @abstractmethod
    def get_costs(self, start_date: str, end_date: str) -> list:
        """Fetch AWS costs for a given date range."""
        pass


class AWSCostRepository(CostRepository):
    """
    Concrete implementation of CostRepository that fetches AWS costs
    using the Cost Explorer API.
    """

    def __init__(self, profile_name: str = None):
        """
        Initialize AWS Cost Explorer client with an optional AWS profile.
        """
        self.session = boto3.Session(profile_name=profile_name)
        self.client = self.session.client('ce', region_name="us-east-1")

    def get_costs(self, start_date: str, end_date: str) -> list:
        """
        Fetch AWS cost data for a specified date range and aggregate totals per service.
        """
        response = self.client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        # Dictionary to store aggregated costs per service
        aggregated_costs = defaultdict(float)

        # Iterate over daily records and sum costs per service
        for group in response['ResultsByTime']:
            for service in group['Groups']:
                service_name = service['Keys'][0]
                cost = float(service['Metrics']['UnblendedCost']['Amount'])
                aggregated_costs[service_name] += cost

        # Convert to list of dictionaries
        results = [
            {"Service": service, "Total Cost": round(cost, 2)}
            for service, cost in aggregated_costs.items()
        ]
        
        return results

    def get_database_instances(self):
        """
        Fetches RDS instance details from all available regions with progress logging.
        """
        instances = []

        # Set default region for EC2 to discover regions
        ec2 = self.session.client('ec2', region_name="us-east-1")

        regions_response = ec2.describe_regions(AllRegions=False)
        regions = [region['RegionName'] for region in regions_response['Regions']]

        print(f"🔍 Discovering RDS instances across {len(regions)} regions...")

        # Iterate through each region
        for idx, region in enumerate(regions, start=1):
            print(f"⏳ [{idx}/{len(regions)}] Analyzing region: {region}")
            rds_client = self.session.client('rds', region_name=region)

            try:
                response = rds_client.describe_db_instances()
                for db in response["DBInstances"]:
                    instances.append({
                        "Region": region,
                        "DBIdentifier": db["DBInstanceIdentifier"],
                        "Engine": db["Engine"],
                        "InstanceType": db["DBInstanceClass"],
                        "Storage (GB)": db["AllocatedStorage"],
                    })
            except Exception as e:
                print(f"⚠️ Could not fetch from {region}: {e}")

        print("✅ RDS instance discovery completed.")
        return instances
