from datetime import date, timedelta
from typing import List, Dict
from decimal import Decimal
from collections import defaultdict
from ..domain.repositories.cost_repository import CostRepository
from ..domain.entities.cost import ServiceCost

class CostAnalyzer:
    def __init__(self, repository: CostRepository):
        self.repository = repository

    def analyze_costs(self, days: int, service_filter: List[str] = None) -> List[Dict]:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        costs = self.repository.get_service_costs(start_date, end_date)
        
        # Group costs by service
        service_costs = defaultdict(Decimal)
        total_cost = Decimal('0')
        
        for cost in costs:
            if not service_filter or cost.service_name in service_filter:
                service_costs[cost.service_name] += cost.cost_amount
                total_cost += cost.cost_amount

        # Convert to list of dictionaries
        result = [
            {
                "Service": service_name,
                "Total Cost (USD)": float(total_cost),
                f"Daily Average ({days}d)": round(float(total_cost) / days, 2)
            }
            for service_name, total_cost in service_costs.items()
        ]
        
        # Add total row
        if result:
            result.append({
                "Service": "TOTAL",
                "Total Cost (USD)": float(total_cost),
                f"Daily Average ({days}d)": round(float(total_cost) / days, 2)
            })
        
        return result

    def analyze_databases(self, days: int) -> List[dict]:
        instances = self.repository.get_database_instances(days)
        analyzed_instances = []
        
        for instance in instances:
            evaluation = self._evaluate_instance(instance)
            
            # Extract CPU percentage from metrics
            cpu_percent = instance.metrics.cpu_utilization
            
            # Convert free memory from GB to MB for better readability
            free_memory_mb = instance.metrics.free_memory_gb * 1024
            
            # Calculate storage usage percentage
            storage_used_gb = instance.total_storage_gb - instance.metrics.free_storage_gb
            storage_percent = (storage_used_gb / instance.total_storage_gb * 100) if instance.total_storage_gb > 0 else 0
            
            # Calculate connection percentage
            connection_percent = (instance.metrics.connections_avg / instance.metrics.max_connections * 100) if instance.metrics.max_connections > 0 else 0
            
            analyzed_instances.append({
                "DBIdentifier": instance.identifier,
                "Region": instance.region,
                "Engine": instance.engine,
                "InstanceType": instance.instance_type,
                "vCPUs": instance.vcpus,
                "Total Memory (GB)": round(instance.total_memory_gb, 2),
                "Free Memory Avg (MB)": round(free_memory_mb, 2),
                "Total Storage (GB)": round(instance.total_storage_gb, 2),
                "Storage Used (GB)": round(storage_percent, 2),
                "Price/Hour (USD)": float(instance.price_per_hour),
                f"Total Cost ({days}d)": round(float(instance.price_per_hour) * 24 * days, 2),
                "CPU Avg (%)": round(cpu_percent, 2),
                "Max Connections": instance.metrics.max_connections,
                "Connections Avg (%)": round(instance.metrics.connections_avg, 2),
                "CPU Status": evaluation['evaluation']['cpu'],
                "Memory Status": evaluation['evaluation']['memory'],
                "Storage Status": evaluation['evaluation']['storage']
            })
        
        # Sort by CPU usage (descending) to show most utilized instances first
        return sorted(analyzed_instances, key=lambda x: x['CPU Avg (%)'], reverse=True)

    def _evaluate_instance(self, instance) -> dict:
        return {
            'evaluation': {
                'cpu': instance.metrics.evaluate_cpu(),
                'memory': instance.metrics.evaluate_memory(instance.total_memory_gb),
                'storage': self._evaluate_storage(
                    instance.metrics.free_storage_gb,
                    instance.total_storage_gb
                )
            }
        }

    def _evaluate_storage(self, free_storage_gb: float, total_storage_gb: float) -> str:
        if not all(isinstance(x, (int, float)) for x in [free_storage_gb, total_storage_gb]):
            return "Storage: Insufficient Data"
        
        try:
            storage_percent_free = (free_storage_gb / total_storage_gb) * 100
            if storage_percent_free < 10:
                return f"Storage: Critically Low ({storage_percent_free:.1f}% free)"
            elif storage_percent_free < 25:
                return f"Storage: Low ({storage_percent_free:.1f}% free)"
            return f"Storage: Optimal ({storage_percent_free:.1f}% free)"
        except Exception:
            return "Storage: Calculation Error" 