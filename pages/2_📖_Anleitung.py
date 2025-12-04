import streamlit as st
import os

st.set_page_config(page_title="Anleitung", layout="wide")

# Path to manual file
MANUAL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'APP_MANUAL.md')

def load_manual():
    if os.path.exists(MANUAL_PATH):
        with open(MANUAL_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    return "Handbuch nicht gefunden."

st.markdown(load_manual())
