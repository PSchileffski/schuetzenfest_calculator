import json
import os
import sys
from src.models import Scenario
from src.calculator import Calculator

def load_scenario(filepath: str) -> Scenario:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Scenario(**data)

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    modules_path = os.path.join(base_path, 'config', 'modules.json')
    scenarios_dir = os.path.join(base_path, 'config', 'scenarios')

    if not os.path.exists(modules_path):
        print(f"Error: Modules file not found at {modules_path}")
        return

    calculator = Calculator(modules_path)
    results = []

    print(f"{'Szenario':<30} | {'Gesamtkosten':<15} | {'Ø pro Besucher':<15}")
    print("-" * 65)

    for filename in os.listdir(scenarios_dir):
        if filename.endswith('.json'):
            scenario_path = os.path.join(scenarios_dir, filename)
            try:
                scenario = load_scenario(scenario_path)
                result = calculator.calculate_scenario(scenario)
                results.append(result)
                
                print(f"{result['scenario_name']:<30} | {result['total_cost']:>10.2f} € | {result['cost_per_visitor']:>10.2f} €")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    print("\n--- Detail-Analyse für das erste Szenario ---")
    if results:
        first = results[0]
        print(f"Szenario: {first['scenario_name']}")
        for module in first['breakdown']:
            print(f"\n  Baustein: {module['module']} ({module['variant']}) - {module['cost']:.2f} €")
            for item in module['items']:
                print(f"    - {item['name']}: {item['total']:.2f} € ({item['type']})")

if __name__ == "__main__":
    main()
