"""
app.py — Craft Projects App, landing page

This is the entry point for the multipage app.
Run with: streamlit run app.py

Pages live in the pages/ folder:
    1_Library.py     — fiber project library (knit + spin)
    2_Weaving.py      — warp calculator projects
    3_Data_Entry.py   — forms for adding new projects
"""

import streamlit as st

st.set_page_config(
    page_title = "Craft Projects",
    page_icon  = "🧵",
    layout     = "wide",
)

st.title("🧵 Craft Projects")
st.write(
    "Welcome! Use the page navigation in the sidebar to browse your "
    "fiber project library, weaving projects, or add new entries."
)

st.markdown("---")
st.markdown("**Pages**")
st.markdown("- 🧶 **Library** — browse knit and spin projects")
st.markdown("- 🪢 **Weaving** — browse warp calculator projects")
st.markdown("- ➕ **Data Entry** — add new projects, yarns, and reference data")
