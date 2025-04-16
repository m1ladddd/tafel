
import streamlit as st
import json
import os

# Zoek in dezelfde map als dit script
REMAP_DIR = os.path.join(os.path.dirname(__file__), "configuration", "gui_line_remap")


st.title("Smart Grid GUI Remap Tool")

# Debug output: laat zien waar hij kijkt
st.write("Zoekt naar remap-bestanden in:", REMAP_DIR)

# Zoek naar remap-bestanden in de rootmap
remap_files = [f for f in os.listdir(REMAP_DIR) if f.startswith("gui_remap_table") and f.endswith(".json")]

if not remap_files:
    st.warning("Geen 'gui_remap_table*.json' bestanden gevonden in deze map.")
    st.stop()

# Bestandskeuze dropdown
selected_file = st.selectbox("Selecteer een GUI remap bestand", remap_files)

# Laad gekozen bestand
with open(os.path.join(REMAP_DIR, selected_file), "r") as f:
    raw = json.load(f)

# Haal de echte data eruit
if isinstance(raw, list) and isinstance(raw[0], dict):
    data = raw[0]
else:
    st.error("JSON-structuur niet herkend.")
    st.stop()


# Toon en toggle mappings
updated_data = []
st.markdown("### Lijnen in dit bestand")
for key in data:
    mapping = data[key]
    origin = mapping["origin_line"]
    destinations = mapping["destination_lines"]
    label = f"Lijn {origin} → {', '.join(destinations)}"
    
    is_visible = st.checkbox(label, value=True)
    
    if is_visible:
        updated_data.append(mapping)


# Downloadknop voor aangepaste JSON
if st.button("🎯 Genereer & Download aangepaste remap configuratie"):
    st.download_button(
        label="⬇️ Download aangepaste JSON",
        data=json.dumps(updated_data, indent=4),
        file_name=f"{selected_file.replace('.json', '')}_custom.json",
        mime="application/json"
    )
