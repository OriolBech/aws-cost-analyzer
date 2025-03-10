from abc import ABC, abstractmethod
from datetime import date
from typing import List
from ..entities.cost import ServiceCost, DatabaseInstance

class CostRepository(ABC):
    @abstractmethod
    def get_service_costs(self, start_date: date, end_date: date) -> List[ServiceCost]:
        """Get costs for all services in the date range"""
        pass

    @abstractmethod
    def get_database_instances(self, days: int = 30) -> List[DatabaseInstance]:
        """Get all database instances with their metrics"""
        pass 