import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="Einstellungen", layout="wide")

MODULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'modules.json')

# Mappings for translation
SCOPE_MAPPING = {
    "global": "Global (Einmalig)",
    "daily": "Täglich (pro Tag wählbar)"
}
SCOPE_MAPPING_REVERSE = {v: k for k, v in SCOPE_MAPPING.items()}

COST_TYPE_MAPPING = {
    "fixed": "Pauschal / Fixkosten",
    "per_visitor": "Pro Besucher",
    "per_hour": "Pro Stunde"
}
COST_TYPE_MAPPING_REVERSE = {v: k for k, v in COST_TYPE_MAPPING.items()}

REVENUE_TYPE_MAPPING = {
    "fixed": "Pauschal / Fixeinnahme",
    "per_visitor": "Pro Besucher",
    "per_unit_sold": "Pro verkaufter Einheit"
}
REVENUE_TYPE_MAPPING_REVERSE = {v: k for k, v in REVENUE_TYPE_MAPPING.items()}

def load_modules():
    with open(MODULES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_modules(modules):
    with open(MODULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)

st.title("⚙️ Einstellungen")

if 'modules_data' not in st.session_state:
    st.session_state.modules_data = load_modules()

modules = st.session_state.modules_data

# 1. Select Module
module_ids = [m['id'] for m in modules]
def get_module_name(mid):
    m = next((m for m in modules if m['id'] == mid), None)
    return m['name'] if m else mid

selected_module_id = st.selectbox("Modul auswählen", module_ids, format_func=get_module_name)
selected_module = next(m for m in modules if m['id'] == selected_module_id)

st.divider()

# 2. Edit Module Details
col1, col2 = st.columns(2)
with col1:
    new_module_name = st.text_input("Modul Bezeichnung", selected_module['name'])
    selected_module['name'] = new_module_name
with col2:
    # Scope selection with translation
    current_scope_display = SCOPE_MAPPING.get(selected_module['scope'], selected_module['scope'])
    selected_scope_display = st.selectbox(
        "Geltungsbereich (Scope)", 
        options=list(SCOPE_MAPPING.values()), 
        index=list(SCOPE_MAPPING.values()).index(current_scope_display) if current_scope_display in SCOPE_MAPPING.values() else 0
    )
    selected_module['scope'] = SCOPE_MAPPING_REVERSE.get(selected_scope_display, "global")

# 3. Variants Management
st.subheader(f"Varianten für '{selected_module['name']}'")

variant_ids = [v['id'] for v in selected_module['variants']]
def get_variant_name(vid):
    v = next((v for v in selected_module['variants'] if v['id'] == vid), None)
    return v['name'] if v else vid

selected_variant_id = st.selectbox("Variante bearbeiten", variant_ids, format_func=get_variant_name)

# Add New Variant Section
with st.expander("➕ Neue Variante hinzufügen"):
    col_new_1, col_new_2 = st.columns(2)
    with col_new_1:
        new_variant_name = st.text_input("Name der neuen Variante")
    with col_new_2:
        new_variant_id = st.text_input("ID der neuen Variante (z.B. 'premium_package')", help="Muss eindeutig sein, keine Leerzeichen")
    
    if st.button("Variante hinzufügen"):
        if new_variant_name and new_variant_id:
            # Check if ID exists
            if any(v['id'] == new_variant_id for v in selected_module['variants']):
                st.error("Diese ID existiert bereits!")
            else:
                new_variant = {
                    "id": new_variant_id,
                    "name": new_variant_name,
                    "cost_items": [],
                    "revenue_items": []
                }
                selected_module['variants'].append(new_variant)
                st.success(f"Variante '{new_variant_name}' hinzugefügt!")
                st.rerun()
        else:
            st.warning("Bitte Name und ID angeben.")

if selected_variant_id:
    # Find variant
    variant = next(v for v in selected_module['variants'] if v['id'] == selected_variant_id)
    
    # Variant Details
    variant['name'] = st.text_input("Variante Bezeichnung", variant['name'])
    variant['id'] = st.text_input("Variante ID", variant['id'], disabled=True, help="IDs sollten nicht geändert werden")
    
    # Cost Items Editor
    st.write("Kosten-Positionen:")
    
    # Convert to DataFrame for editing
    cost_items_df = pd.DataFrame(variant.get('cost_items', []))
    
    if cost_items_df.empty:
        cost_items_df = pd.DataFrame(columns=["name", "amount", "cost_type", "description"])
    else:
        # Translate cost_type for display
        cost_items_df['cost_type'] = cost_items_df['cost_type'].map(lambda x: COST_TYPE_MAPPING.get(x, x))
    
    # Configure column config
    column_config = {
        "name": st.column_config.TextColumn("Bezeichnung", required=True),
        "amount": st.column_config.NumberColumn("Betrag (€)", min_value=0.0, format="%.2f €"),
        "cost_type": st.column_config.SelectboxColumn(
            "Kosten-Art", 
            options=list(COST_TYPE_MAPPING.values()), 
            required=True
        ),
        "description": st.column_config.TextColumn("Beschreibung")
    }
    
    edited_df = st.data_editor(
        cost_items_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key=f"editor_{selected_module['id']}_{variant['id']}"
    )
    
    # Update variant with edited data
    # Convert back to list of dicts, removing empty rows if any
    # First translate cost_type back to technical keys
    if not edited_df.empty:
        edited_df['cost_type'] = edited_df['cost_type'].map(lambda x: COST_TYPE_MAPPING_REVERSE.get(x, x))
        # Replace NaN with None to ensure valid JSON and Pydantic compatibility
        edited_df = edited_df.where(pd.notnull(edited_df), None)

    new_cost_items = edited_df.to_dict('records')
    # Clean up (remove NaN/None)
    cleaned_items = []
    for item in new_cost_items:
        if item['name']: # Only keep if name is set
            cleaned_items.append(item)
            
    variant['cost_items'] = cleaned_items

    # Revenue Items Editor
    st.write("Einnahmen-Positionen:")
    
    # Convert to DataFrame for editing
    revenue_items_df = pd.DataFrame(variant.get('revenue_items', []))
    
    if revenue_items_df.empty:
        revenue_items_df = pd.DataFrame(columns=["name", "amount", "revenue_type", "description"])
    else:
        # Translate revenue_type for display
        revenue_items_df['revenue_type'] = revenue_items_df['revenue_type'].map(lambda x: REVENUE_TYPE_MAPPING.get(x, x))
    
    # Configure column config
    revenue_column_config = {
        "name": st.column_config.TextColumn("Bezeichnung", required=True),
        "amount": st.column_config.NumberColumn("Betrag (€)", min_value=0.0, format="%.2f €"),
        "revenue_type": st.column_config.SelectboxColumn(
            "Einnahmen-Art", 
            options=list(REVENUE_TYPE_MAPPING.values()), 
            required=True
        ),
        "description": st.column_config.TextColumn("Beschreibung")
    }
    
    edited_revenue_df = st.data_editor(
        revenue_items_df,
        column_config=revenue_column_config,
        num_rows="dynamic",
        use_container_width=True,
        key=f"revenue_editor_{selected_module['id']}_{variant['id']}"
    )
    
    # Update variant with edited data
    if not edited_revenue_df.empty:
        edited_revenue_df['revenue_type'] = edited_revenue_df['revenue_type'].map(lambda x: REVENUE_TYPE_MAPPING_REVERSE.get(x, x))
        # Replace NaN with None to ensure valid JSON and Pydantic compatibility
        edited_revenue_df = edited_revenue_df.where(pd.notnull(edited_revenue_df), None)

    new_revenue_items = edited_revenue_df.to_dict('records')
    cleaned_revenue_items = []
    for item in new_revenue_items:
        if item['name']:
            cleaned_revenue_items.append(item)
            
    variant['revenue_items'] = cleaned_revenue_items

st.divider()

if st.button("💾 Änderungen speichern", type="primary"):
    save_modules(modules)
    st.success("Module wurden erfolgreich gespeichert!")
    # Reload to ensure consistency
    st.session_state.modules_data = load_modules()

# Download Button for Persistence
st.markdown("### Export für GitHub")
st.markdown("Da Änderungen in der Cloud-Umgebung flüchtig sind, laden Sie die Konfiguration herunter und speichern Sie sie in Ihrem Git-Repository unter `config/modules.json`.")

json_str = json.dumps(modules, indent=2, ensure_ascii=False)
st.download_button(
    label="📥 modules.json herunterladen",
    data=json_str,
    file_name="modules.json",
    mime="application/json"
)
