"""
pages/2_Weaving.py — Weaving Projects Page

Project library browser for warp calculator projects.
This is a starting stub — fill in once weaving projects exist to browse.
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.getcwd())

st.set_page_config(
    page_title = "Fiber Projects — Weaving",
    page_icon  = "🪢",
    layout     = "wide",
)

st.title("🪢 Weaving Projects")

try:
    from database import init_db as init_weaving_db
    from projects import get_all_projects

    WEAVING_DB = init_weaving_db("warp_calc.db")
    weaving_projects = get_all_projects(WEAVING_DB)

    if not weaving_projects:
        st.info("No weaving projects saved yet. Add some in the notebook to see them here.")
    else:
        table_rows = [
            {
                "Project Name"  : p.project_name,
                "Date Planned"  : p.date_planned,
                "Status"        : "✅ Completed" if p.is_complete else "📋 Planned",
            }
            for p in weaving_projects
        ]
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        name_options = ["— Select a project —"] + [p.project_name for p in weaving_projects]
        selected = st.selectbox("View project details", name_options)

        if selected != "— Select a project —":
            project = next(p for p in weaving_projects if p.project_name == selected)
            st.markdown(f"### {project.project_name}")
            st.code(project.summary())

except ImportError:
    st.warning(
        "Weaving modules (database.py, projects.py) not found in this folder. "
        "Make sure warp_calc.py files are in the same directory as this app."
    )
