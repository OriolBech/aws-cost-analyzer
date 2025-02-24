import csv
import os
from tabulate import tabulate

class CostFormatter:
    """
    Handles formatting of AWS data for display and CSV.
    """

    @staticmethod
    def format_as_table(data: list, add_total: bool = True) -> str:
        if not data:
            return "No records found."

        total_keys = ["Total Cost", "Total Cost (30d)"]
        total_key = next((key for key in total_keys if key in data[0]), None)

        if add_total and total_key:
            total_cost = sum(
                item.get(total_key, 0) for item in data if isinstance(item.get(total_key, 0), (int, float))
            )
            data.append({list(data[0].keys())[0]: "TOTAL", total_key: round(total_cost, 2)})

        return tabulate(data, headers="keys", tablefmt="grid")

    @staticmethod
    def save_as_csv(data: list, output_file: str):
        if not data:
            print("No data to save.")
            return

        # Usa el orden del primer elemento directamente
        filtered_columns = list(data[0].keys())

        # Identificar columna de totales
        total_keys = ["Total Cost", "Total Cost (30d)"]
        total_key = next((key for key in total_keys if key in filtered_columns), None)

        # Calcular la suma total para la última fila
        total_row = {col: "" for col in filtered_columns}
        if total_key:
            total_sum = sum(
                float(row[total_key]) for row in data if row.get(total_key) not in ["", None, "N/A"]
            )
            total_row[filtered_columns[0]] = "TOTAL"
            total_row[total_key] = round(total_sum, 2)
            data.append(total_row)

        # Crear carpeta si no existe
        dir_path = os.path.dirname(output_file)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        # Escribir CSV respetando el orden del OrderedDict
        with open(output_file, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=filtered_columns)
            writer.writeheader()
            writer.writerows(data)

        print(f"✅ Data successfully written to {output_file}")