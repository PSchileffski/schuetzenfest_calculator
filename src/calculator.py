import json
from typing import List, Dict, Any
from .models import Scenario, Module, CostType, RevenueType, Product, Persona

class Calculator:
    def __init__(self, modules_file: str, master_data_file: str):
        self.modules = self._load_modules(modules_file)
        self.modules_map = {m.id: m for m in self.modules}
        
        self.products, self.personas = self._load_master_data(master_data_file)
        self.products_map = {p.id: p for p in self.products}
        self.personas_map = {p.id: p for p in self.personas}

    def _load_modules(self, filepath: str) -> List[Module]:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Module(**m) for m in data]

    def _load_master_data(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        products = [Product(**p) for p in data.get('products', [])]
        personas = [Persona(**p) for p in data.get('personas', [])]
        return products, personas

    def calculate_scenario(self, scenario: Scenario) -> Dict[str, Any]:
        total_cost = 0.0
        breakdown = []
        total_revenue = 0.0
        revenue_breakdown = []

        # Filter enabled days
        active_days = [d for d in scenario.days if d.enabled]

        # Calculate total visitors and hours for defaults
        total_visitors = sum(d.total_visitors for d in active_days)
        total_hours = sum(d.duration_hours for d in active_days)
        
        # Calculate total visitor composition for global modules
        total_visitor_composition = {}
        for day in active_days:
            for pid, count in day.visitor_composition.items():
                total_visitor_composition[pid] = total_visitor_composition.get(pid, 0) + count

        # --- Helper to calculate a module variant cost ---
        def calculate_variant_cost(module, variant, context_visitors, context_hours, context_name, visitor_composition):
            mod_cost = 0.0
            mod_items = []
            
            # Calculate weighted visitors for this module
            weighted_visitors = 0.0
            if visitor_composition:
                for pid, count in visitor_composition.items():
                    persona = self.personas_map.get(pid)
                    rate = 1.0
                    if persona and module.id in persona.module_adoption_rates:
                        rate = persona.module_adoption_rates[module.id]
                    weighted_visitors += count * rate
            else:
                weighted_visitors = context_visitors

            for item in variant.cost_items:
                item_cost = 0.0
                if item.cost_type == CostType.FIXED:
                    item_cost = item.amount
                elif item.cost_type == CostType.PER_VISITOR:
                    item_cost = item.amount * weighted_visitors
                elif item.cost_type == CostType.PER_HOUR:
                    multiplier = context_hours
                    if item.multiplier_key and item.multiplier_key in scenario.global_parameters:
                        multiplier = scenario.global_parameters[item.multiplier_key]
                    item_cost = item.amount * multiplier
                
                mod_cost += item_cost
                mod_items.append({
                    "name": item.name,
                    "type": item.cost_type,
                    "unit_amount": item.amount,
                    "total": item_cost,
                    "description": item.description
                })
            return mod_cost, mod_items

        # --- Helper to calculate a module variant revenue ---
        def calculate_variant_revenue(module, variant, context_visitors, context_hours, context_name, visitor_composition):
            mod_rev = 0.0
            mod_items = []
            
            # Calculate weighted visitors for this module
            weighted_visitors = 0.0
            if visitor_composition:
                for pid, count in visitor_composition.items():
                    persona = self.personas_map.get(pid)
                    rate = 1.0
                    if persona and module.id in persona.module_adoption_rates:
                        rate = persona.module_adoption_rates[module.id]
                    weighted_visitors += count * rate
            else:
                weighted_visitors = context_visitors

            for item in variant.revenue_items:
                item_rev = 0.0
                if item.revenue_type == RevenueType.FIXED:
                    item_rev = item.amount
                elif item.revenue_type == RevenueType.PER_VISITOR:
                    item_rev = item.amount * weighted_visitors
                
                mod_rev += item_rev
                mod_items.append({
                    "name": f"{item.name} ({context_name})",
                    "type": item.revenue_type,
                    "total": item_rev,
                    "category": f"Module: {module.name}"
                })
            return mod_rev, mod_items

        # 1. Calculate Global Modules
        # Only use global_modules (new structure)
        for module_id, variant_id in scenario.global_modules.items():
            module = self.modules_map.get(module_id)
            if not module: continue
            
            # Skip if module is not global scope
            if module.scope == "daily":
                continue
                
            variant = next((v for v in module.variants if v.id == variant_id), None)
            if not variant: continue

            cost, items = calculate_variant_cost(module, variant, total_visitors, total_hours, "Global", total_visitor_composition)
            total_cost += cost
            breakdown.append({
                "module": module.name,
                "variant": variant.name,
                "cost": cost,
                "items": items,
                "scope": "Global"
            })

            # Calculate Revenue from Module
            rev, rev_items = calculate_variant_revenue(module, variant, total_visitors, total_hours, "Global", total_visitor_composition)
            total_revenue += rev
            revenue_breakdown.extend(rev_items)

        # 2. Calculate Day Specific Modules
        for day in active_days:
            for module_id, variant_id in day.selected_modules.items():
                module = self.modules_map.get(module_id)
                if not module: continue
                
                # Skip if module is not daily scope
                if module.scope == "global":
                    continue
                    
                variant = next((v for v in module.variants if v.id == variant_id), None)
                if not variant: continue

                cost, items = calculate_variant_cost(module, variant, day.total_visitors, day.duration_hours, day.name, day.visitor_composition)
                total_cost += cost
                breakdown.append({
                    "module": f"{module.name} ({day.name})",
                    "variant": variant.name,
                    "cost": cost,
                    "items": items,
                    "scope": day.name
                })

                # Calculate Revenue from Module
                rev, rev_items = calculate_variant_revenue(module, variant, day.total_visitors, day.duration_hours, day.name, day.visitor_composition)
                total_revenue += rev
                revenue_breakdown.extend(rev_items)

        # 3. Calculate Revenue & Consumption Costs
        # total_revenue and revenue_breakdown are already initialized
        
        # 2a. Global Revenue Items
        for item in scenario.revenue_items:
            item_revenue = 0.0
            if item.revenue_type == RevenueType.FIXED:
                item_revenue = item.amount
            elif item.revenue_type == RevenueType.PER_VISITOR:
                item_revenue = item.amount * total_visitors
            
            total_revenue += item_revenue
            revenue_breakdown.append({
                "name": item.name,
                "type": item.revenue_type,
                "total": item_revenue,
                "category": "Global"
            })

        # 2b. Day Specific Revenue & Consumption
        for day in active_days:
            # Entry ticket revenue based on entry module selection
            day_visitors = day.total_visitors
            
            # Day specific fixed/per_visitor revenue (e.g. Sponsoring for specific days)
            for item in day.day_specific_revenue:
                r = 0.0
                if item.revenue_type == RevenueType.PER_VISITOR:
                    r = item.amount * day_visitors
                elif item.revenue_type == RevenueType.FIXED:
                    r = item.amount
                
                total_revenue += r
                revenue_breakdown.append({
                    "name": f"{item.name} ({day.name})",
                    "type": item.revenue_type,
                    "total": r,
                    "category": "Tickets/Entry"
                })

            # Consumption Calculation per day
            day_consumption_revenue = 0.0
            day_consumption_cost = 0.0
            
            for persona_id, count in day.visitor_composition.items():
                persona = self.personas_map.get(persona_id)
                if not persona: continue
                
                for prod_id, amount in persona.consumption.items():
                    product = self.products_map.get(prod_id)
                    if not product: continue
                    
                    total_units = amount * count
                    rev = total_units * product.sales_price
                    cost = total_units * product.purchase_price
                    
                    day_consumption_revenue += rev
                    day_consumption_cost += cost

            # Add day consumption to totals and breakdown
            total_revenue += day_consumption_revenue
            total_cost += day_consumption_cost
            
            if day_consumption_revenue > 0:
                revenue_breakdown.append({
                    "name": f"Getränkeverkauf ({day.name})",
                    "type": "consumption",
                    "total": day_consumption_revenue,
                    "category": f"Consumption-{day.name}"
                })
            
            if day_consumption_cost > 0:
                breakdown.append({
                    "module": f"Wareneinsatz Getränke ({day.name})",
                    "variant": "Verbrauchsabhängig",
                    "cost": day_consumption_cost,
                    "items": [{"name": "Einkauf Getränke", "total": day_consumption_cost, "type": "variable"}],
                    "scope": day.name
                })

        profit = total_revenue - total_cost

        return {
            "scenario_name": scenario.name,
            "total_cost": total_cost,
            "total_revenue": total_revenue,
            "profit": profit,
            "total_visitors": total_visitors,
            "cost_per_visitor": total_cost / total_visitors if total_visitors > 0 else 0,
            "revenue_per_visitor": total_revenue / total_visitors if total_visitors > 0 else 0,
            "breakdown": breakdown,
            "revenue_breakdown": revenue_breakdown
        }
