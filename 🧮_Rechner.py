import streamlit as st
import os
import json
import pandas as pd
from src.models import Scenario, DayConfig
from src.calculator import Calculator

# Page Config
st.set_page_config(page_title="Schützenfest Kalkulator", layout="wide")

# Paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MODULES_PATH = os.path.join(BASE_PATH, 'config', 'modules.json')
MASTER_DATA_PATH = os.path.join(BASE_PATH, 'config', 'master_data.json')
SCENARIOS_DIR = os.path.join(BASE_PATH, 'config', 'scenarios')

# Mappings for translation
COST_TYPE_MAPPING = {
    "fixed": "Fixkosten",
    "per_visitor": "Pro Besucher",
    "per_hour": "Pro Stunde",
    "variable": "Variabel"
}

REVENUE_TYPE_MAPPING = {
    "fixed": "Pauschal",
    "per_visitor": "Pro Besucher",
    "per_unit_sold": "Pro Verkauf",
    "consumption": "Verzehr",
    "voucher": "Gutschein"
}

# Load Calculator
@st.cache_resource
def get_calculator():
    return Calculator(MODULES_PATH, MASTER_DATA_PATH)

calculator = get_calculator()

# Helper to load scenarios (no cache to always get fresh data)
def load_scenarios():
    scenarios = {}
    if not os.path.exists(SCENARIOS_DIR):
        return scenarios
    for filename in sorted(os.listdir(SCENARIOS_DIR)):
        if filename.endswith('.json'):
            path = os.path.join(SCENARIOS_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    scenarios[data['name']] = Scenario(**data)
                except Exception as e:
                    st.error(f"Error loading {filename}: {e}")
    return scenarios

# --- Sidebar ---
st.sidebar.title("Konfiguration")

# Debug: Show reload button
if st.sidebar.button("🔄 Szenarien neu laden"):
    st.cache_resource.clear()
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

scenarios_map = load_scenarios()
selected_scenario_name = st.sidebar.selectbox("Szenario wählen", list(scenarios_map.keys()))

# Track scenario changes to reset input values
if 'last_scenario' not in st.session_state:
    st.session_state.last_scenario = selected_scenario_name
    st.session_state.scenario_load_counter = 0
elif st.session_state.last_scenario != selected_scenario_name:
    # Clear all input states when scenario changes
    keys_to_clear = [k for k in st.session_state.keys() if k not in ['last_scenario', 'scenario_load_counter']]
    for key in keys_to_clear:
        del st.session_state[key]
    st.session_state.last_scenario = selected_scenario_name
    st.session_state.scenario_load_counter += 1

if selected_scenario_name:
    scenario = scenarios_map[selected_scenario_name]
    
    # --- Global Modules ---
    st.sidebar.subheader("Globale Bausteine")
    global_modules_selection = {}
    
    # Identify global modules
    global_modules_defs = [m for m in calculator.modules if m.scope in ["global", "both"]]
    
    # Current selection (migrate from old selected_variants if needed)
    current_global = scenario.global_modules if scenario.global_modules else getattr(scenario, 'selected_variants', {})

    for module in global_modules_defs:
        # Find current variant index
        current_var_id = current_global.get(module.id)
        variant_options = {}
        variant_details = {}  # Store details for help text
        variant_id_to_name = {}  # Map variant IDs to display names
        
        for v in module.variants:
            # Calculate total cost for this variant
            total_cost = sum(item.amount for item in v.cost_items if item.cost_type == 'fixed')
            
            # Build detailed breakdown for help text
            details = []
            
            # Costs
            if v.cost_items:
                details.append("Kosten:")
                for item in v.cost_items:
                    if item.cost_type == 'fixed':
                        details.append(f"• {item.name}: {item.amount:.0f} €")
                    elif item.cost_type == 'per_visitor':
                        details.append(f"• {item.name}: {item.amount:.2f} € pro Besucher")
                    elif item.cost_type == 'per_hour':
                        details.append(f"• {item.name}: {item.amount:.2f} € pro Stunde")
            
            # Revenues
            if v.revenue_items:
                if details: details.append("") # Spacer
                details.append("Einnahmen:")
                for item in v.revenue_items:
                    if item.revenue_type == 'fixed':
                        details.append(f"• {item.name}: {item.amount:.0f} €")
                    elif item.revenue_type == 'per_visitor':
                        details.append(f"• {item.name}: {item.amount:.2f} € pro Besucher")
                    elif item.revenue_type == 'per_unit_sold':
                        details.append(f"• {item.name}: {item.amount:.2f} € pro Verkauf")
            
            display_name = f"{v.name} ({total_cost:.0f} €)" if total_cost > 0 else v.name
            variant_options[display_name] = v.id
            variant_id_to_name[v.id] = display_name
            variant_details[v.id] = "\n".join(details) if details else "Keine Kosten/Einnahmen"
        
        # Default to first if not found
        default_idx = 0
        if current_var_id:
            ids = list(variant_options.values())
            if current_var_id in ids:
                default_idx = ids.index(current_var_id)
        
        selected_name = st.sidebar.selectbox(
            f"{module.name}", 
            list(variant_options.keys()), 
            index=default_idx,
            key=f"global_{module.id}"
        )
        
        # Get selected variant ID and show its details
        selected_variant_id = variant_options[selected_name]
        help_text = variant_details.get(selected_variant_id, "")
        if help_text and help_text != "Keine Kosten/Einnahmen":
            st.sidebar.caption(f"ℹ️ {help_text}")
        
        global_modules_selection[module.id] = selected_variant_id

    # Update scenario global modules
    scenario = scenario.model_copy(update={"global_modules": global_modules_selection})

    
    st.sidebar.subheader("Tages-Planung")
    
    # Interactive Visitor Counts per Persona AND Day Modules
    updated_days = []
    
    # Identify daily modules
    daily_modules_defs = [m for m in calculator.modules if m.scope in ["daily", "both"]]

    for day in scenario.days:
        with st.sidebar.expander(f"{day.name}", expanded=False):
            # Enable/Disable Day
            day_enabled = st.checkbox("Tag aktiv", value=day.enabled, key=f"enable_{day.name}")
            
            if not day_enabled:
                st.caption("Dieser Tag wird in der Berechnung ignoriert.")
                updated_day = day.model_copy(update={"enabled": False})
                updated_days.append(updated_day)
                continue

            # 1. Modules
            st.markdown("**Bausteine**")
            day_modules_selection = day.selected_modules.copy()
            
            for module in daily_modules_defs:
                # Current variant for this day
                current_var_id = day_modules_selection.get(module.id)
                variant_options = {}
                variant_details = {}  # Store details for help text
                
                for v in module.variants:
                    # Calculate total cost for this variant
                    total_cost = sum(item.amount for item in v.cost_items if item.cost_type == 'fixed')
                    
                    # Build detailed breakdown for help text
                    details = []
                    
                    # Costs
                    if v.cost_items:
                        details.append("Kosten:")
                        for item in v.cost_items:
                            if item.cost_type == 'fixed':
                                details.append(f"• {item.name}: {item.amount:.0f} €")
                            elif item.cost_type == 'per_visitor':
                                details.append(f"• {item.name}: {item.amount:.2f} € pro Besucher")
                            elif item.cost_type == 'per_hour':
                                details.append(f"• {item.name}: {item.amount:.2f} € pro Stunde")
                    
                    # Revenues
                    if v.revenue_items:
                        if details: details.append("") # Spacer
                        details.append("Einnahmen:")
                        for item in v.revenue_items:
                            if item.revenue_type == 'fixed':
                                details.append(f"• {item.name}: {item.amount:.0f} €")
                            elif item.revenue_type == 'per_visitor':
                                details.append(f"• {item.name}: {item.amount:.2f} € pro Besucher")
                            elif item.revenue_type == 'per_unit_sold':
                                details.append(f"• {item.name}: {item.amount:.2f} € pro Verkauf")
                    
                    display_name = f"{v.name} ({total_cost:.0f} €)" if total_cost > 0 else v.name
                    variant_options[display_name] = v.id
                    variant_details[v.id] = "\n".join(details) if details else "Keine Kosten/Einnahmen"
                
                # Default logic: 
                # If not set for day, pick "none"/"no_entry" if exists, else first
                default_idx = 0
                if current_var_id:
                    ids = list(variant_options.values())
                    if current_var_id in ids:
                        default_idx = ids.index(current_var_id)
                else:
                    # Try to find "none" or "no_entry" as default for new modules
                    ids = list(variant_options.values())
                    if "none" in ids:
                        default_idx = ids.index("none")
                    elif "no_entry" in ids:
                        default_idx = ids.index("no_entry")
                    # If module is not in selection yet, set it to default
                    if module.id not in day_modules_selection:
                        day_modules_selection[module.id] = ids[default_idx]

                selected_name = st.selectbox(
                    f"{module.name}", 
                    list(variant_options.keys()), 
                    index=default_idx,
                    key=f"{day.name}_{module.id}"
                )
                
                # Get selected variant ID and show its details
                selected_variant_id = variant_options[selected_name]
                help_text = variant_details.get(selected_variant_id, "")
                if help_text and help_text != "Keine Kosten/Einnahmen":
                    st.caption(f"ℹ️ {help_text}")
                
                day_modules_selection[module.id] = selected_variant_id

            # 2. Visitors
            st.markdown("**Besucher**")
            new_composition = {}
            
            # If old scenario format (visitor_count), migrate roughly
            if not day.visitor_composition and hasattr(day, 'visitor_count'):
                 day.visitor_composition = {"besucher": day.visitor_count}

            for persona in calculator.personas:
                current_val = day.visitor_composition.get(persona.id, 0)
                # Use a unique key that includes load counter to force reload
                widget_key = f"{day.name}_{persona.id}_{st.session_state.scenario_load_counter}"
                
                # Build consumption info
                consumption_info = []
                for prod_id, amount in persona.consumption.items():
                    product = calculator.products_map.get(prod_id)
                    if product and amount > 0:
                        consumption_info.append(f"{amount:.0f}x {product.name}")
                consumption_text = ", ".join(consumption_info) if consumption_info else "keine"
                
                new_val = st.number_input(
                    f"{persona.name}", 
                    min_value=0, 
                    value=current_val,
                    step=10,
                    key=widget_key,
                    help=f"Konsumiert: {consumption_text}"
                )
                new_composition[persona.id] = new_val
            
            updated_day = day.model_copy(update={
                "visitor_composition": new_composition,
                "selected_modules": day_modules_selection,
                "enabled": True
            })
            updated_days.append(updated_day)
    
    # Update scenario with new days (in memory only)
    scenario = scenario.model_copy(update={"days": updated_days})

    # --- Calculation ---
    result = calculator.calculate_scenario(scenario)

    # --- Main Content ---
    st.title(f"Kalkulation: {scenario.name}")
    st.markdown(f"*{scenario.description}*")

    # Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Gesamtkosten", f"{result['total_cost']:,.2f} €")
    col2.metric("Gesamteinnahmen", f"{result['total_revenue']:,.2f} €")
    
    profit_color = "normal"
    if result['profit'] > 0:
        profit_color = "normal" # Streamlit handles green for positive delta usually, but metric color is limited
    
    col3.metric("Gewinn / Verlust", f"{result['profit']:,.2f} €", delta=f"{result['profit']:,.2f} €")
    col4.metric("Ø Kosten/Besucher", f"{result['cost_per_visitor']:.2f} €")

    # --- Tabs for Details ---
    tab0, tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Kosten-Details", "Einnahmen-Details", "Bausteine", "Szenario speichern"])

    with tab0:
        st.subheader("Übersicht")
        
        # Calculate per-day totals
        day_totals = {}
        active_days = [d for d in scenario.days if d.enabled]
        for day in active_days:
            day_costs = sum(x['cost'] for x in result['breakdown'] if x.get('scope') == day.name)
            day_revenue = sum(x['total'] for x in result['revenue_breakdown'] 
                            if f"({day.name})" in x['name'] or x.get('category') == f"Consumption-{day.name}")
            day_totals[day.name] = {
                'costs': day_costs,
                'revenue': day_revenue,
                'profit': day_revenue - day_costs
            }
        
        # Global costs and revenue
        global_costs_total = sum(x['cost'] for x in result['breakdown'] if x.get('scope') == 'Global')
        global_revenue_total = sum(x['total'] for x in result['revenue_breakdown'] if x.get('category') == 'Global')
        
        # Create overview table
        overview_data = []
        
        # Add global row
        overview_data.append({
            "Bereich": "Übergreifend",
            "Kosten": f"{global_costs_total:,.2f} €",
            "Einnahmen": f"{global_revenue_total:,.2f} €",
            "Saldo": f"{global_revenue_total - global_costs_total:,.2f} €"
        })
        
        # Add day rows
        for day in active_days:
            totals = day_totals[day.name]
            overview_data.append({
                "Bereich": day.name,
                "Kosten": f"{totals['costs']:,.2f} €",
                "Einnahmen": f"{totals['revenue']:,.2f} €",
                "Saldo": f"{totals['profit']:,.2f} €"
            })
        
        # Add total row
        overview_data.append({
            "Bereich": "GESAMT",
            "Kosten": f"{result['total_cost']:,.2f} €",
            "Einnahmen": f"{result['total_revenue']:,.2f} €",
            "Saldo": f"{result['profit']:,.2f} €"
        })
        
        df_overview = pd.DataFrame(overview_data)
        
        # Style the dataframe
        st.dataframe(
            df_overview,
            use_container_width=True,
            hide_index=True
        )
        
        # Visualizations
        st.markdown("### Kosten vs. Einnahmen pro Bereich")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("**Kosten und Einnahmen**")
            # Prepare data for chart with negative costs and positive revenue
            chart_rows_1 = []
            chart_rows_1.append({
                "Bereich": "Übergreifend",
                "Kosten": -global_costs_total,
                "Einnahmen": global_revenue_total
            })
            
            for day in active_days:
                totals = day_totals[day.name]
                chart_rows_1.append({
                    "Bereich": day.name,
                    "Kosten": -totals['costs'],
                    "Einnahmen": totals['revenue']
                })
            
            df_chart_1 = pd.DataFrame(chart_rows_1)
            df_chart_1 = df_chart_1.set_index('Bereich')
            st.bar_chart(df_chart_1, color=["#ff4b4b", "#09ab3b"], use_container_width=True)
        
        with col_chart2:
            st.markdown("**Saldo (Gewinn/Verlust)**")
            # Prepare data for profit chart
            chart_rows_2 = []
            chart_rows_2.append({
                "Bereich": "Übergreifend",
                "Saldo": global_revenue_total - global_costs_total
            })
            
            for day in active_days:
                totals = day_totals[day.name]
                chart_rows_2.append({
                    "Bereich": day.name,
                    "Saldo": totals['profit']
                })
            
            df_chart_2 = pd.DataFrame(chart_rows_2)
            df_chart_2 = df_chart_2.set_index('Bereich')
            st.bar_chart(df_chart_2, color="#0068c9", use_container_width=True)

    with tab1:
        st.subheader("Kostenaufstellung")
        
        # Group breakdown by scope
        global_costs = [x for x in result['breakdown'] if x.get('scope') == 'Global']
        day_costs = {day.name: [] for day in scenario.days if day.enabled}
        for item in result['breakdown']:
            scope = item.get('scope')
            if scope != 'Global' and scope in day_costs:
                day_costs[scope].append(item)
        
        # Show global costs first
        if global_costs:
            st.markdown("### Übergreifend")
            detailed_rows = []
            for module in global_costs:
                for item in module['items']:
                    detailed_rows.append({
                        "Baustein": module['module'],
                        "Position": item['name'],
                        "Typ": COST_TYPE_MAPPING.get(item['type'], item['type']),
                        "Betrag": f"{item['total']:.2f} €"
                    })
            st.dataframe(pd.DataFrame(detailed_rows), width='stretch')
            st.markdown(f"**Summe Übergreifend:** {sum(x['cost'] for x in global_costs):,.2f} €")
        
        # Show costs per day
        for day in [d for d in scenario.days if d.enabled]:
            if day_costs[day.name]:
                st.markdown(f"### {day.name}")
                detailed_rows = []
                for module in day_costs[day.name]:
                    # Remove day name from module name if present
                    module_name = module['module'].replace(f" ({day.name})", "")
                    for item in module['items']:
                        detailed_rows.append({
                            "Baustein": module_name,
                            "Position": item['name'],
                            "Typ": COST_TYPE_MAPPING.get(item['type'], item['type']),
                            "Betrag": f"{item['total']:.2f} €"
                        })
                st.dataframe(pd.DataFrame(detailed_rows), width='stretch')
                st.markdown(f"**Summe {day.name}:** {sum(x['cost'] for x in day_costs[day.name]):,.2f} €")

    with tab2:
        st.subheader("Einnahmenaufstellung")
        
        # Group revenue by category
        global_revenue = [x for x in result['revenue_breakdown'] if x.get('category') == 'Global']
        day_revenue = {day.name: [] for day in scenario.days}
        
        for item in result['revenue_breakdown']:
            category = item.get('category', '')
            # Check if it's a day-specific item
            for day in scenario.days:
                if f"({day.name})" in item['name'] or category == f"Consumption-{day.name}":
                    day_revenue[day.name].append(item)
                    break
        
        # Show global revenue
        if global_revenue:
            st.markdown("### Übergreifend")
            # Process global revenue rows for translation
            processed_global_rows = []
            for item in global_revenue:
                processed_global_rows.append({
                    "Bezeichnung": item['name'],
                    "Typ": REVENUE_TYPE_MAPPING.get(item['type'], item['type']),
                    "Betrag": f"{item['total']:.2f} €",
                    "Kategorie": item.get('category', '')
                })
            st.dataframe(pd.DataFrame(processed_global_rows), width='stretch')
            st.markdown(f"**Summe Übergreifend:** {sum(x['total'] for x in global_revenue):,.2f} €")
        
        # Show revenue per day
        for day in [d for d in scenario.days if d.enabled]:
            if day_revenue[day.name]:
                st.markdown(f"### {day.name}")
                # Process rows to remove day name redundancy and format nicely
                processed_rows = []
                for item in day_revenue[day.name]:
                    clean_name = item['name'].replace(f" ({day.name})", "")
                    processed_rows.append({
                        "Bezeichnung": clean_name,
                        "Typ": REVENUE_TYPE_MAPPING.get(item['type'], item['type']),
                        "Betrag": f"{item['total']:.2f} €",
                        "Kategorie": item.get('category', '')
                    })
                st.dataframe(pd.DataFrame(processed_rows), width='stretch')
                st.markdown(f"**Summe {day.name}:** {sum(x['total'] for x in day_revenue[day.name]):,.2f} €")

    with tab3:
        st.subheader("Gewählte Konfiguration")
        
        st.markdown("### Globale Bausteine")
        st.json(scenario.global_modules)
        
        st.markdown("### Tages-Konfiguration")
        for day in [d for d in scenario.days if d.enabled]:
            with st.expander(f"{day.name} - Details"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Bausteine**")
                    st.json(day.selected_modules)
                with col_b:
                    st.markdown("**Besucher**")
                    st.json(day.visitor_composition)

    with tab4:
        st.subheader("Szenario speichern")
        
        st.markdown("""
        Hier können Sie die aktuelle Konfiguration als neues Szenario speichern oder ein bestehendes aktualisieren.
        """)
        
        # Create JSON export of current scenario
        scenario_export = scenario.model_dump(mode='json')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            scenario_name_input = st.text_input(
                "Szenario-Name",
                value=scenario.name,
                help="Name für das Szenario (wird als Dateiname verwendet)"
            )
            
            scenario_desc_input = st.text_area(
                "Beschreibung",
                value=scenario.description,
                help="Kurze Beschreibung des Szenarios"
            )
        
        with col2:
            st.markdown("**Aktionen**")
            
            # Update scenario name and description in export
            scenario_export['name'] = scenario_name_input
            scenario_export['description'] = scenario_desc_input
            
            # Generate filename from scenario name
            safe_filename = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in scenario_name_input)
            safe_filename = safe_filename.replace(' ', '_').lower()
            filename = f"{safe_filename}.json"
            filepath = os.path.join(SCENARIOS_DIR, filename)
            
            file_exists = os.path.exists(filepath)
            
            if file_exists:
                st.warning(f"⚠️ Datei `{filename}` existiert bereits")
                action_label = "Szenario aktualisieren"
            else:
                st.info(f"💾 Wird gespeichert als `{filename}`")
                action_label = "Neues Szenario speichern"
            
            if st.button(action_label, type="primary", use_container_width=True):
                try:
                    # Ensure scenarios directory exists
                    os.makedirs(SCENARIOS_DIR, exist_ok=True)
                    
                    # Save scenario
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(scenario_export, f, indent=2, ensure_ascii=False)
                    
                    st.success(f"✅ Szenario erfolgreich gespeichert: `{filename}`")
                    st.info("💡 Laden Sie die Szenarien neu, um das neue/aktualisierte Szenario in der Sidebar zu sehen.")
                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern: {e}")
        
        # Show JSON preview
        st.markdown("### JSON-Vorschau")
        st.markdown("Diese Konfiguration wird gespeichert:")
        
        # Pretty print JSON
        json_str = json.dumps(scenario_export, indent=2, ensure_ascii=False)
        st.code(json_str, language='json')
        
        # Download button for manual export
        st.download_button(
            label="📥 JSON herunterladen",
            data=json_str,
            file_name=filename,
            mime="application/json",
            help="Laden Sie die JSON-Datei herunter, um sie manuell zu bearbeiten oder zu sichern"
        )

else:
    st.info("Bitte wähle ein Szenario aus der Sidebar.")
