from typing import List, Any
from tabulate import tabulate
from dataclasses import asdict
from decimal import Decimal

class TableFormatter:
    @staticmethod
    def format_table(data: List[Any], add_total: bool = True) -> str:
        if not data:
            return "No data available"

        # Convert domain entities to dictionaries
        dict_data = []
        for item in data:
            if hasattr(item, '__dataclass_fields__'):  # Check if it's a dataclass
                dict_data.append(asdict(item))
            elif isinstance(item, dict):
                dict_data.append(item)
            else:
                dict_data.append(vars(item))

        if add_total and 'cost_amount' in dict_data[0]:
            total_cost = sum(
                float(item['cost_amount'])
                for item in dict_data
                if isinstance(item.get('cost_amount'), (int, float, str, Decimal))
            )
            dict_data.append({
                'service_name': 'TOTAL',
                'cost_amount': round(total_cost, 2),
                'date': ''
            })

        return tabulate(dict_data, headers='keys', tablefmt='grid') 