import csv
import os
from typing import List, Dict, Any
from dataclasses import asdict

class CSVFormatter:
    @staticmethod
    def save_to_file(data: List[Any], filepath: str) -> None:
        if not data:
            return

        # Convert domain entities to dictionaries if needed
        dict_data = []
        for item in data:
            if hasattr(item, '__dataclass_fields__'):  # Check if it's a dataclass
                dict_data.append(asdict(item))
            elif isinstance(item, dict):
                dict_data.append(item)
            else:
                dict_data.append(vars(item))  # Fallback for regular objects

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=dict_data[0].keys())
            writer.writeheader()
            writer.writerows(dict_data) 