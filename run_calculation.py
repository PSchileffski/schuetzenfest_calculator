import json
import sys
import os

# Add the current directory to sys.path so we can import src
sys.path.append(os.getcwd())

from src.calculator import Calculator
from src.models import Scenario

def format_currency(amount):
    return f"{amount:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def main():
    modules_file = 'config/modules.json'
    master_data_file = 'config/master_data.json'
    scenario_file = 'config/scenarios/last_year.json'

    try:
        calc = Calculator(modules_file, master_data_file)
        
        with open(scenario_file, 'r', encoding='utf-8') as f:
            scenario_data = json.load(f)
            scenario = Scenario(**scenario_data)

        result = calc.calculate_scenario(scenario)

        total_revenue = result['total_revenue']
        total_cost = result['total_cost']
        profit = total_revenue - total_cost
        margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

        print(f"\n=== GESAMTKALKULATION: {scenario.name} ===")
        print(f"{'Einnahmen:':<20} {format_currency(total_revenue)}")
        print(f"{'Ausgaben:':<20} {format_currency(total_cost)}")
        print("-" * 40)
        print(f"{'Ergebnis:':<20} {format_currency(profit)}")
        print(f"{'Marge:':<20} {margin:.1f}%")
        print("\n=== DETAILS ===")
        
        print("\n--- Einnahmen ---")
        # Group revenue by category/module
        for item in result['revenue_breakdown']:
             print(f"{item['name']}: {format_currency(item['total'])}")

        print("\n--- Ausgaben ---")
        # Group costs by category/module
        for item in result['breakdown']:
            print(f"{item['module']} ({item['variant']}): {format_currency(item['cost'])}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
