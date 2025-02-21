import csv
import os
from tabulate import tabulate

class CostFormatter:
    """
    Handles formatting of AWS cost data for display.
    """

    @staticmethod
    def format_as_table(data: list) -> str:
        """
        Converts cost data into a formatted table with aggregated totals.
        """
        if not data:
            return "No cost records found for the selected date range."

        # Calculate the total cost
        total_cost = sum(item['Total Cost'] for item in data)

        # Append total cost row to the table
        data.append({'Service': 'TOTAL', 'Total Cost': round(total_cost, 2)})

        return tabulate(data, headers="keys", tablefmt="grid")

    @staticmethod
    def save_as_csv(data: list, output_file: str):
        """
        Saves the aggregated cost data to a CSV file.
        """
        if not data:
            print("No cost data to save.")
            return

        # Calculate total cost
        total_cost = sum(item['Total Cost'] for item in data)

        # Append total cost row
        data.append({"Service": "TOTAL", "Total Cost": round(total_cost, 2)})

        # Ensure directory exists before writing
        dir_path = os.path.dirname(output_file)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # Write aggregated data to CSV
        with open(output_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["Service", "Total Cost"])
            writer.writeheader()
            writer.writerows(data)