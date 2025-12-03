import streamlit as st
import json
import os
import pandas as pd

st.set_page_config(page_title="Modul-Editor", layout="wide")

MODULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'modules.json')

def load_modules():
    with open(MODULES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_modules(modules):
    with open(MODULES_PATH, 'w', encoding='utf-8') as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)

st.title("🛠️ Modul-Editor")

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
    new_module_name = st.text_input("Modul Name", selected_module['name'])
    selected_module['name'] = new_module_name
with col2:
    new_module_scope = st.selectbox("Scope", ["global", "daily"], index=0 if selected_module['scope'] == "global" else 1)
    selected_module['scope'] = new_module_scope

# 3. Variants Management
st.subheader(f"Varianten für '{selected_module['name']}'")

variant_ids = [v['id'] for v in selected_module['variants']]
def get_variant_name(vid):
    v = next((v for v in selected_module['variants'] if v['id'] == vid), None)
    return v['name'] if v else vid

selected_variant_id = st.selectbox("Variante bearbeiten", variant_ids, format_func=get_variant_name)

if selected_variant_id:
    # Find variant
    variant = next(v for v in selected_module['variants'] if v['id'] == selected_variant_id)
    
    # Variant Details
    variant['name'] = st.text_input("Variante Name", variant['name'])
    variant['id'] = st.text_input("Variante ID", variant['id'], disabled=True, help="IDs sollten nicht geändert werden")
    
    # Cost Items Editor
    st.write("Kosten-Positionen:")
    
    # Convert to DataFrame for editing
    cost_items_df = pd.DataFrame(variant.get('cost_items', []))
    
    if cost_items_df.empty:
        cost_items_df = pd.DataFrame(columns=["name", "amount", "cost_type", "description"])
    
    # Configure column config
    column_config = {
        "name": st.column_config.TextColumn("Bezeichnung", required=True),
        "amount": st.column_config.NumberColumn("Betrag (€)", min_value=0.0, format="%.2f €"),
        "cost_type": st.column_config.SelectboxColumn("Typ", options=["fixed", "per_visitor", "per_hour"], required=True),
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
    new_cost_items = edited_df.to_dict('records')
    # Clean up (remove NaN/None)
    cleaned_items = []
    for item in new_cost_items:
        if item['name']: # Only keep if name is set
            cleaned_items.append(item)
            
    variant['cost_items'] = cleaned_items

st.divider()

if st.button("💾 Änderungen speichern", type="primary"):
    save_modules(modules)
    st.success("Module wurden erfolgreich gespeichert!")
    # Reload to ensure consistency
    st.session_state.modules_data = load_modules()
