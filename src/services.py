from repository import CostRepository
from settings import COST_PROFILES

class CostService:
    """
    Business logic for processing AWS cost data.
    """

    def __init__(self, repository: CostRepository):
        """
        Dependency Injection: Injects a CostRepository instance.
        """
        self.repository = repository

    def get_costs_last_days(self, days: int, profile: str = "all") -> list:
        """
        Fetch costs for the last N days with an optional profile filter.
        """
        import datetime
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=days)

        # Get all cost data
        costs = self.repository.get_costs(str(start_date), str(end_date))

        # Apply profile filter if it's defined
        profile_services = COST_PROFILES.get(profile, [])
        if profile_services:
            costs = [cost for cost in costs if cost["Service"] in profile_services]

        return costs