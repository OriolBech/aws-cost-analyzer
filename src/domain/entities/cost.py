from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass
class ServiceCost:
    service_name: str
    cost_amount: Decimal
    date: date

@dataclass
class DatabaseInstance:
    identifier: str
    region: str
    engine: str
    instance_type: str
    vcpus: int
    price_per_hour: Decimal
    total_memory_gb: float
    total_storage_gb: float
    metrics: 'DatabaseMetrics' 