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
        self.pricing_client = self.session.client('pricing', region_name='us-east-1')

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

    def get_database_instances(self, total_days=30):
        """
        Fetches RDS instance details from all available regions with pricing and total estimated price.
        """
        instances = []

        ec2 = self.session.client('ec2', region_name="us-east-1")
        regions_response = ec2.describe_regions(AllRegions=False)
        regions = [region['RegionName'] for region in regions_response['Regions']]

        total_hours = total_days * 24

        print(f"🔍 Discovering RDS instances across {len(regions)} regions...")

        for idx, region in enumerate(regions, start=1):
            print(f"⏳ [{idx}/{len(regions)}] Analyzing region: {region}")
            rds_client = self.session.client('rds', region_name=region)

            try:
                response = rds_client.describe_db_instances()
                for db in response["DBInstances"]:
                    instance_type = db["DBInstanceClass"]
                    engine = db["Engine"]

                    price_per_hour = self.get_rds_price(instance_type, engine, region)
                    total_price = (
                        round(price_per_hour * total_hours, 2)
                        if isinstance(price_per_hour, float)
                        else 'N/A'
                    )

                    instances.append({
                        "Region": region,
                        "DBIdentifier": db["DBInstanceIdentifier"],
                        "Engine": engine,
                        "InstanceType": instance_type,
                        "Storage (GB)": db["AllocatedStorage"],
                        "Price/Hour (USD)": price_per_hour,
                        f"Total Cost ({total_days}d)": total_price,  # <-- Aquí está el ajuste
                    })
            except Exception as e:
                print(f"⚠️ Could not fetch from {region}: {e}")

        print("✅ RDS instance discovery completed.")
        return instances
    
    def get_rds_price(self, instance_type, engine, region):
        """
        Retrieves hourly price for a given RDS instance type and engine.
        """
        try:
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': engine},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self.region_full_name(region)},
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'},
            ]

            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=filters,
                MaxResults=1
            )

            if response['PriceList']:
                price_item = response['PriceList'][0]
                import json
                price_item = json.loads(price_item)
                ondemand = price_item['terms']['OnDemand']
                for key in ondemand:
                    for price_dimensions in ondemand[key]['priceDimensions'].values():
                        return float(price_dimensions['pricePerUnit']['USD'])

            return 'N/A'

        except Exception as e:
            print(f"⚠️ Error fetching price for {instance_type} ({engine}) in {region}: {e}")
            return 'N/A'
        
    def region_full_name(self, region_code):
        """
        Converts AWS region code to full name as required by Pricing API.
        """
        region_names = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-west-2': 'EU (London)',
            'eu-west-3': 'EU (Paris)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            # Add other regions as necessary
        }
        return region_names.get(region_code, region_code)
