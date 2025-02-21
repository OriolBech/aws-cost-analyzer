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
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        self.client = session.client('ce')

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
        Fetches details of RDS instances, including engine type, instance type, and allocated storage.
        """
        instances = []
        try:
            response = self.rds_client.describe_db_instances()

            for db in response["DBInstances"]:
                instances.append({
                    "DBIdentifier": db["DBInstanceIdentifier"],
                    "Engine": db["Engine"],
                    "InstanceType": db["DBInstanceClass"],
                    "Storage (GB)": db["AllocatedStorage"],
                })
        except Exception as e:
            print(f"⚠️ Error fetching RDS instances: {e}")

        return instances

    def get_service_pricing(self, service_name):
        client = boto3.client("pricing", region_name="us-east-1")
        response = client.get_products(
            ServiceCode=service_name,
            Filters=[{"Type": "TERM_MATCH", "Field": "regionCode", "Value": "us-east-1"}]
        )
        return response