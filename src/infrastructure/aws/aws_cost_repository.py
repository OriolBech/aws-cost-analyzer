from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from ...domain.repositories.cost_repository import CostRepository
from ...domain.entities.cost import ServiceCost, DatabaseInstance
from ...domain.value_objects.metrics import DatabaseMetrics
from .aws_client import AWSClient
import json

class AWSCostRepository(CostRepository):
    ENGINE_MAPPING = {
        'postgres': 'PostgreSQL',
        'aurora-postgresql': 'Aurora PostgreSQL',
        'mysql': 'MySQL',
        'mariadb': 'MariaDB',
        'oracle-se2': 'Oracle',
        'sqlserver-se': 'SQL Server'
    }

    def __init__(self, profile_name: str = None):
        self.aws_client = AWSClient(profile_name)

    def get_service_costs(self, start_date: date, end_date: date) -> List[ServiceCost]:
        client = self.aws_client.get_client('ce')
        response = client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.isoformat(),
                'End': end_date.isoformat()
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost'],
            GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        )

        costs = []
        for group in response['ResultsByTime']:
            for service in group['Groups']:
                costs.append(ServiceCost(
                    service_name=service['Keys'][0],
                    cost_amount=Decimal(service['Metrics']['UnblendedCost']['Amount']),
                    date=date.fromisoformat(group['TimePeriod']['Start'])
                ))
        return costs

    def get_database_instances(self, days: int = 30) -> List[DatabaseInstance]:
        instances = []
        
        # Get all regions
        ec2_client = self.aws_client.get_client('ec2')
        regions = [region['RegionName'] 
                  for region in ec2_client.describe_regions()['Regions']]

        print(f"🔍 Discovering RDS instances across {len(regions)} regions...")

        for idx, region in enumerate(regions, 1):
            try:
                print(f"⏳ [{idx}/{len(regions)}] Analyzing region: {region}")
                rds_client = self.aws_client.get_client('rds', region_name=region)
                cloudwatch = self.aws_client.get_client('cloudwatch', region_name=region)
                
                response = rds_client.describe_db_instances()
                
                for db in response['DBInstances']:
                    try:
                        # Get instance metrics with improved error handling
                        metrics = self._get_instance_metrics(
                            cloudwatch,
                            db['DBInstanceIdentifier'],
                            days,
                            'aurora' in db['Engine'].lower()
                        )
                        
                        # Get instance specifications
                        specs = self._get_instance_specs(
                            db['DBInstanceClass'],
                            db['Engine'],
                            region
                        )

                        # Create DatabaseInstance entity with validated data
                        instance = DatabaseInstance(
                            identifier=db['DBInstanceIdentifier'],
                            region=region,
                            engine=f"{db['Engine']} {db.get('EngineVersion', 'N/A')}",
                            instance_type=db['DBInstanceClass'],
                            vcpus=specs.get('vcpus', 0),
                            price_per_hour=self._get_instance_price(
                                db['DBInstanceClass'],
                                db['Engine'],
                                region
                            ),
                            total_memory_gb=specs.get('memory_gb', 0),
                            total_storage_gb=float(db.get('AllocatedStorage', 0)),
                            metrics=DatabaseMetrics(
                                cpu_utilization=metrics.get('CPUUtilization', 0),
                                free_memory_gb=metrics.get('FreeableMemory', 0) / (1024 ** 3),
                                free_storage_gb=metrics.get('FreeStorageSpace', 0) / (1024 ** 3),
                                connections_avg=metrics.get('DatabaseConnections', 0),
                                max_connections=self._calculate_max_connections(
                                    specs.get('memory_gb', 0)
                                )
                            )
                        )
                        instances.append(instance)
                        print(f"✅ Processed {db['DBInstanceIdentifier']}")
                        
                    except Exception as e:
                        print(f"⚠️ Error processing instance {db['DBInstanceIdentifier']}: {e}")
                        
            except Exception as e:
                print(f"⚠️ Error processing region {region}: {e}")
                
        return instances

    def _get_instance_metrics(self, cloudwatch, db_identifier: str, 
                            days: int, is_cluster: bool) -> dict:
        metrics = {}
        dimension_name = 'DBClusterIdentifier' if is_cluster else 'DBInstanceIdentifier'
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        metric_configs = {
            'CPUUtilization': {'unit': 'Percent', 'default': 0},
            'FreeableMemory': {'unit': 'Bytes', 'default': 0},
            'FreeStorageSpace': {'unit': 'Bytes', 'default': 0},
            'DatabaseConnections': {'unit': 'Count', 'default': 0}
        }
        
        for metric_name, config in metric_configs.items():
            try:
                response = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName=metric_name,
                    Dimensions=[{
                        'Name': dimension_name,
                        'Value': db_identifier
                    }],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=3600,  # 1 hour periods
                    Statistics=['Average'],
                    Unit=config['unit']
                )
                
                if response['Datapoints']:
                    # Sort datapoints by timestamp to get most recent first
                    sorted_points = sorted(
                        response['Datapoints'],
                        key=lambda x: x['Timestamp'],
                        reverse=True
                    )
                    
                    # Calculate average of non-zero values
                    valid_points = [
                        dp['Average'] for dp in sorted_points 
                        if dp['Average'] > 0
                    ]
                    
                    if valid_points:
                        metrics[metric_name] = sum(valid_points) / len(valid_points)
                    else:
                        metrics[metric_name] = config['default']
                else:
                    print(f"⚠️ No datapoints found for {metric_name} on {db_identifier}")
                    metrics[metric_name] = config['default']
                    
            except Exception as e:
                print(f"⚠️ Error fetching {metric_name} for {db_identifier}: {e}")
                metrics[metric_name] = config['default']
        
        return metrics

    def _get_instance_specs(self, instance_type: str, engine: str, region: str) -> dict:
        try:
            # Get instance type info from EC2
            ec2_client = self.aws_client.get_client('ec2', region_name='us-east-1')
            response = ec2_client.describe_instance_types(
                InstanceTypes=[instance_type.replace('db.', '')]  # Remove 'db.' prefix for EC2 API
            )
            
            if response['InstanceTypes']:
                instance_info = response['InstanceTypes'][0]
                return {
                    'vcpus': instance_info['VCpuInfo']['DefaultVCpus'],
                    'memory_gb': instance_info['MemoryInfo']['SizeInMiB'] / 1024  # Convert MiB to GiB
                }
                
        except Exception as e:
            print(f"⚠️ Error getting specs from EC2 API: {e}, trying pricing API")
            
            try:
                # Fallback to pricing API
                pricing = self.aws_client.get_client('pricing', region_name='us-east-1')
                
                normalized_engine = next(
                    (v for k, v in self.ENGINE_MAPPING.items() 
                     if k in engine.lower()), engine
                )

                response = pricing.get_products(
                    ServiceCode='AmazonRDS',
                    Filters=[
                        {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                        {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': normalized_engine}
                    ]
                )

                if response['PriceList']:
                    attributes = json.loads(response['PriceList'][0])['product']['attributes']
                    return {
                        'vcpus': int(attributes.get('vcpu', 0)),
                        'memory_gb': float(attributes.get('memory', '0').split()[0])
                    }
                
            except Exception as e:
                print(f"⚠️ Error getting specs from Pricing API: {e}")
                
        # If both APIs fail, return zeros
        return {'vcpus': 0, 'memory_gb': 0}

    def _get_instance_price(self, instance_type: str, engine: str, region: str) -> Decimal:
        try:
            pricing = self.aws_client.get_client('pricing', region_name='us-east-1')
            
            # Normalize engine name for PostgreSQL specifically
            if 'postgres' in engine.lower():
                normalized_engine = 'PostgreSQL'
            else:
                normalized_engine = next(
                    (v for k, v in self.ENGINE_MAPPING.items() 
                     if k in engine.lower()), engine
                )

            # First try with specific filters
            filters = [
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': normalized_engine},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_region_name(region)},
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'}
            ]

            response = pricing.get_products(
                ServiceCode='AmazonRDS',
                Filters=filters
            )

            if not response['PriceList']:
                # Try without deployment option
                filters = [
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': normalized_engine},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': self._get_region_name(region)}
                ]
                response = pricing.get_products(
                    ServiceCode='AmazonRDS',
                    Filters=filters
                )

            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                
                # Debug information
                print(f"Found price item for {instance_type} {normalized_engine} in {region}")
                
                terms = price_item['terms']['OnDemand']
                price_dimensions = next(iter(terms.values()))['priceDimensions']
                price = next(iter(price_dimensions.values()))['pricePerUnit']['USD']
                
                # Convert to Decimal and ensure it's valid
                try:
                    return Decimal(price)
                except Exception as e:
                    print(f"⚠️ Error converting price {price} to Decimal: {e}")
                    return Decimal('0')
                
            else:
                print(f"⚠️ No price found for {instance_type} {normalized_engine} in {region}")
                
        except Exception as e:
            print(f"⚠️ Error getting price from AWS API: {e}")
            
        return Decimal('0')

    def _calculate_max_connections(self, memory_gb: float) -> int:
        # Simple formula for max connections based on memory
        if memory_gb <= 0:
            return 0
        return int(memory_gb * 100)  # Example: 100 connections per GB

    def _get_region_name(self, region_code: str) -> str:
        region_names = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'af-south-1': 'Africa (Cape Town)',
            'ap-east-1': 'Asia Pacific (Hong Kong)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
            'ap-northeast-2': 'Asia Pacific (Seoul)',
            'ap-northeast-3': 'Asia Pacific (Osaka)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ca-central-1': 'Canada (Central)',
            'eu-central-1': 'EU (Frankfurt)',
            'eu-west-1': 'EU (Ireland)',
            'eu-west-2': 'EU (London)',
            'eu-west-3': 'EU (Paris)',
            'eu-north-1': 'EU (Stockholm)',
            'eu-south-1': 'EU (Milan)',
            'me-south-1': 'Middle East (Bahrain)',
            'sa-east-1': 'South America (Sao Paulo)'
        }
        return region_names.get(region_code, region_code) 