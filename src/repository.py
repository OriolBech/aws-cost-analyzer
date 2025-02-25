from abc import ABC, abstractmethod
import boto3
import json
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta

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
                    storage_gb = db["AllocatedStorage"]
                    is_cluster = 'aurora' in engine.lower()
                    price_per_hour = self.get_rds_price(instance_type, engine, region)
                    total_price = (
                        round(price_per_hour * total_hours, 2)
                        if isinstance(price_per_hour, float)
                        else 'N/A'
                    )

                    utilization = self.get_rds_utilization(
                        db["DBInstanceIdentifier"], 
                        region, 
                        days=total_days,
                        is_cluster=is_cluster
                    )

                    specs = self.get_instance_specs(instance_type, engine, region)

                    instances.append(OrderedDict([
                        ("DBIdentifier", db["DBInstanceIdentifier"]),
                        ("Region", region),
                        ("Engine", f"{engine} {db['EngineVersion']}"),
                        ("InstanceType", instance_type),
                        ("vCPUs", specs["vcpus"]),
                        ("Price/Hour (USD)", price_per_hour),
                        (f"Cost ({total_days}d)", total_price),
                        ("Total Memory (GB)", specs["memory_gb"]),
                        ("Free Memory Avg (MB)", utilization["FreeableMemory"]),
                        ("Total Storage (GB)", storage_gb),
                        ("Free Storage Avg (GB)", utilization["FreeStorageSpace"]),
                        ("CPU Avg (%)", utilization["CPUUtilization"]),
                        ("Max Connections", self.get_max_connections(specs["memory_gb"])),
                        ("Connections Avg", utilization["DatabaseConnections"]),
                        ("Sizing Evaluation", self.evaluate_instance_sizing(
                            utilization["CPUUtilization"],
                            utilization["FreeableMemory"],
                            specs["memory_gb"],
                            utilization["FreeStorageSpace"],
                            storage_gb
                        )),
                    ]))

            except Exception as e:
                print(f"⚠️ Could not fetch from {region}: {e}")

        print("✅ RDS instance discovery completed.")
        return instances
    
    def evaluate_instance_sizing(self, cpu_avg, memory_avg_gb, total_memory_gb, storage_avg_gb, total_storage_gb):
        evaluations = []

        # CPU Evaluation
        if not isinstance(cpu_avg, (int, float)):
            cpu_eval = "CPU: Insufficient Data"
        elif cpu_avg > 80:
            cpu_eval = "CPU: High Usage"
        elif cpu_avg < 20:
            cpu_eval = "CPU: Low Usage"
        else:
            cpu_eval = "CPU: Optimal"
        evaluations.append(cpu_eval)

        # Memory Evaluation
        try:
            if not all(isinstance(x, (int, float)) for x in [memory_avg_gb, total_memory_gb]):
                mem_eval = "Memory: Insufficient Data"
            else:
                memory_percent_free = (memory_avg_gb / total_memory_gb) * 100
                if memory_percent_free < 5:
                    mem_eval = f"Memory: Critically Low ({memory_percent_free:.1f}% free)"
                elif memory_percent_free < 15:
                    mem_eval = f"Memory: Low ({memory_percent_free:.1f}% free)"
                else:
                    mem_eval = f"Memory: Optimal ({memory_percent_free:.1f}% free)"
        except Exception:
            mem_eval = "Memory: Calculation Error"
        evaluations.append(mem_eval)

        # Storage Evaluation
        try:
            if not all(isinstance(x, (int, float)) for x in [storage_avg_gb, total_storage_gb]):
                storage_eval = "Storage: Insufficient Data"
            else:
                storage_percent_free = (storage_avg_gb / total_storage_gb) * 100
                if storage_percent_free < 10:
                    storage_eval = f"Storage: Critically Low ({storage_percent_free:.1f}% free)"
                elif storage_percent_free < 25:
                    storage_eval = f"Storage: Low ({storage_percent_free:.1f}% free)"
                else:
                    storage_eval = f"Storage: Optimal ({storage_percent_free:.1f}% free)"
        except Exception:
            storage_eval = "Storage: Calculation Error"
        evaluations.append(storage_eval)

        return " | ".join(evaluations)
    
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
                        price_str = price_dimensions['pricePerUnit']['USD']
                        price_float = round(float(price_str.replace(',', '.')), 4)
                    return price_float

            return 'N/A'

        except Exception as e:
            print(f"⚠️ Error fetching price for {instance_type} ({engine}) in {region}: {e}")
            return 'N/A'
        
    def get_max_connections(self, memory_gb):
        """
        Calculate max connections based on memory, with proper type checking
        """
        try:
            if isinstance(memory_gb, (int, float)):
                memory_bytes = memory_gb * 1024**3
                connections = memory_bytes / 25165760  # 24MB per connection
                return min(int(connections), 12000)
            return 'N/A'
        except Exception:
            return 'N/A'
        
    def get_rds_utilization(self, db_identifier, region, days=7, is_cluster=False):
        cloudwatch = self.session.client('cloudwatch', region_name=region)
        dimension_name = 'DBClusterIdentifier' if is_cluster else 'DBInstanceIdentifier'

        metrics = {
            'CPUUtilization': 'N/A',
            'DatabaseConnections': 'N/A',
            'FreeableMemory': 'N/A',
            'FreeStorageSpace': 'N/A'
        }

        try:
            for metric_name in metrics.keys():
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[{'Name': dimension_name, 'Value': db_identifier}],
                    StartTime=datetime.utcnow() - timedelta(days=days),
                    EndTime=datetime.utcnow(),
                    Period=86400,  # daily metrics
                    Statistics=['Average']
                )

                datapoints = response.get('Datapoints', [])
                if not datapoints:
                    continue

                values = [dp['Average'] for dp in datapoints if isinstance(dp.get('Average'), (int, float))]
                if not values:
                    continue

                avg_value = sum(values) / len(values)

                if metric_name in ['FreeStorageSpace', 'FreeableMemory']:
                    # Convert bytes to GB
                    metrics[metric_name] = round(avg_value / (1024 ** 3), 2)
                else:
                    metrics[metric_name] = round(avg_value, 2)

        except Exception as e:
            print(f"⚠️ Error fetching metrics for {db_identifier} in {region}: {e}")

        return metrics

    def get_instance_specs(self, instance_type, engine, region):
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
                price_item = json.loads(response['PriceList'][0])

                # Validar estructura completa antes de acceder
                attributes = price_item.get('product', {}).get('attributes', {})
                
                memory_str = attributes.get('memory', '0 GiB')
                vcpu_str = attributes.get('vcpu', '0')

                # Conversión segura a números
                memory_gb = memory_str.split(' ')[0].replace(',', '').strip()
                vcpus = vcpu_str.strip()

                memory_gb = float(memory_gb) if memory_gb.replace('.', '', 1).isdigit() else 'N/A'
                vcpus = int(vcpus) if vcpus.isdigit() else 'N/A'

                return {
                    "memory_gb": memory_gb,
                    "vcpus": vcpus
                }

            # Caso en que no devuelve información
            return {"memory_gb": "N/A", "vcpus": "N/A"}

        except Exception as e:
            print(f"⚠️ Error fetching specs for {instance_type} ({engine}) in {region}: {e}")
            return {"memory_gb": "N/A", "vcpus": "N/A"}
        
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
