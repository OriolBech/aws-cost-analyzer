from dataclasses import dataclass
from decimal import Decimal

@dataclass
class DatabaseMetrics:
    cpu_utilization: float
    free_memory_gb: float
    free_storage_gb: float
    connections_avg: float
    max_connections: int

    def evaluate_cpu(self) -> str:
        if self.cpu_utilization > 80:
            return "CPU: High Usage"
        elif self.cpu_utilization < 20:
            return "CPU: Low Usage"
        return "CPU: Optimal"

    def evaluate_memory(self, total_memory_gb: float) -> str:
        if not total_memory_gb:
            return "Memory: Insufficient Data"
        
        memory_percent_free = (self.free_memory_gb / total_memory_gb) * 100
        if memory_percent_free < 5:
            return f"Memory: Critically Low ({memory_percent_free:.1f}% free)"
        elif memory_percent_free < 15:
            return f"Memory: Low ({memory_percent_free:.1f}% free)"
        return f"Memory: Optimal ({memory_percent_free:.1f}% free)" 