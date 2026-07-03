"""
pages/1_Library.py — Fiber Projects Library Page

Project library browser for knit and spin projects.
This page is part of the multipage app — run with: streamlit run app.py
"""

import streamlit as st
import sys, os
sys.path.insert(0, os.getcwd())

from stash_db import (
    init_db,
    get_stashyarn_by_brand,
    get_stashyarn_by_id,
    get_all_knitproject,
    get_all_spinproject,
    get_projectyarn_by_project,
)

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title  = "Fiber Projects — Library",
    page_icon   = "🧶",
    layout      = "wide",
)

# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------

DB = init_db("fiber_projects.db")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def format_date(date_str):
    """Display date nicely, handle None gracefully."""
    return date_str if date_str else "—"


def status_badge(project):
    """Return a status string based on completion."""
    if project.date_completed:
        return "✅ Completed"
    elif project.date_started:
        return "🪡 In Progress"
    else:
        return "📋 Planned"


def get_yarn_details_for_project(project_id):
    """Fetch all yarns associated with a knit project."""
    project_yarns = get_projectyarn_by_project(project_id, DB)
    details = []
    for py in project_yarns:
        yarn = get_stashyarn_by_id(py.stash_id, DB)
        if yarn:
            grams = py.grams_used
            details.append({
                "role"  : py.color_role or "—",
                "yarn"  : f"{yarn.brand or ''} {yarn.size_notation} {yarn.fiber}".strip(),
                "start_g": py.starting_weight,
                "end_g" : py.ending_weight,
                "used_g": f"{grams:.1f}g" if grams else "—",
            })
    return details


# ---------------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------------

st.sidebar.title("🧶 Fiber Projects")
st.sidebar.markdown("---")

project_type = st.sidebar.radio(
    "Project type",
    ["All", "Knit / Crochet", "Spinning"],
)

status_filter = st.sidebar.selectbox(
    "Status",
    ["All", "Completed", "In Progress", "Planned"],
)

search = st.sidebar.text_input("🔍 Search by name")

st.sidebar.markdown("---")
st.sidebar.caption("Fiber Projects Tracker")


# ---------------------------------------------------------------------------
# Load and filter projects
# ---------------------------------------------------------------------------

knit_projects = []
spin_projects = []

if project_type in ["All", "Knit / Crochet"]:
    knit_projects = get_all_knitproject(DB)

if project_type in ["All", "Spinning"]:
    spin_projects = get_all_spinproject(DB)


def apply_status_filter(projects):
    if status_filter == "Completed":
        return [p for p in projects if p.date_completed]
    elif status_filter == "In Progress":
        return [p for p in projects if p.date_started and not p.date_completed]
    elif status_filter == "Planned":
        return [p for p in projects if not p.date_started]
    return projects


def apply_search_filter(projects, search_term):
    if not search_term:
        return projects
    term = search_term.lower()
    return [p for p in projects if term in p.project_name.lower()]


knit_projects = apply_status_filter(knit_projects)
knit_projects = apply_search_filter(knit_projects, search)
spin_projects = apply_status_filter(spin_projects)
spin_projects = apply_search_filter(spin_projects, search)


# ---------------------------------------------------------------------------
# Yardage totals dashboard
# ---------------------------------------------------------------------------

def get_completed_knit_yardage(projects, db):
    """Sum grams_used converted to yards for all completed knit projects."""
    total_yards = 0.0
    for project in projects:
        if not project.date_completed:
            continue
        project_yarns = get_projectyarn_by_project(project.id, db)
        for py in project_yarns:
            grams = py.grams_used
            if grams is None:
                continue
            yarn = get_stashyarn_by_id(py.stash_id, db)
            if yarn:
                total_yards += (grams / 100) * yarn.yards_per_100g
    return total_yards


def get_completed_spin_yardage(projects):
    """Sum measured_yards for all completed spin projects."""
    return sum(p.measured_yards for p in projects
               if p.date_completed and p.measured_yards)


def filter_by_year_month(projects, year, month):
    """Filter projects by date_completed year/month. 'All' skips that filter."""
    result = []
    for p in projects:
        if not p.date_completed:
            continue
        try:
            p_year, p_month, _ = p.date_completed.split("-")
        except (ValueError, AttributeError):
            continue
        if year != "All" and p_year != year:
            continue
        if month != "All" and p_month != month:
            continue
        result.append(p)
    return result


# gather every completed project's year/month for the dropdown options
all_completed = (
    [p for p in get_all_knitproject(DB) if p.date_completed]
    + [p for p in get_all_spinproject(DB) if p.date_completed]
)
years_available = sorted({p.date_completed.split("-")[0] for p in all_completed}, reverse=True)

st.markdown("### 📊 Yardage Totals")

col_year, col_month = st.columns(2)
with col_year:
    year_choice = st.selectbox("Year", ["All"] + years_available)
with col_month:
    month_labels = {
        "All": "All", "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
    }
    month_choice = st.selectbox(
        "Month", list(month_labels.keys()), format_func=lambda m: month_labels[m]
    )

knit_completed_filtered = filter_by_year_month(get_all_knitproject(DB), year_choice, month_choice)
spin_completed_filtered = filter_by_year_month(get_all_spinproject(DB), year_choice, month_choice)

knit_yards = get_completed_knit_yardage(knit_completed_filtered, DB)
spin_yards = get_completed_spin_yardage(spin_completed_filtered)
combined_yards = knit_yards + spin_yards

metric_col1, metric_col2, metric_col3 = st.columns(3)
with metric_col1:
    st.metric("Combined Total", f"{combined_yards:,.0f} yd")
with metric_col2:
    st.metric("Knit Yardage Used", f"{knit_yards:,.0f} yd")
with metric_col3:
    st.metric("Spun Yardage Produced", f"{spin_yards:,.0f} yd")

st.markdown("---")

# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

st.title("🧶 Fiber Projects Library")

total = len(knit_projects) + len(spin_projects)
st.caption(f"{total} project(s) found")

# ---------------------------------------------------------------------------
# Knit / Crochet projects
# ---------------------------------------------------------------------------

if project_type in ["All", "Knit / Crochet"] and knit_projects:
    st.markdown("## 🪡 Knit / Crochet Projects")

    # build a minimal summary table: name, date, status
    table_rows = [
        {
            "Project Name"  : p.project_name,
            "Date Completed": format_date(p.date_completed),
            "Status"        : status_badge(p),
        }
        for p in knit_projects
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    # dropdown to select a project and view full details below
    knit_name_options = ["— Select a project —"] + [p.project_name for p in knit_projects]
    selected_knit_name = st.selectbox(
        "View project details", knit_name_options, key="knit_select"
    )

    if selected_knit_name != "— Select a project —":
        project = next(p for p in knit_projects if p.project_name == selected_knit_name)
        badge = status_badge(project)

        st.markdown(f"### {badge}  |  {project.project_name}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Pattern**")
            st.write(f"{project.pattern_name}")
            st.write(f"*{project.pattern_source}*")
            if project.made_for:
                st.markdown("**Made for**")
                st.write(project.made_for)

        with col2:
            st.markdown("**Dates**")
            st.write(f"Started:   {format_date(project.date_started)}")
            st.write(f"Completed: {format_date(project.date_completed)}")
            if project.gauge:
                st.markdown("**Gauge**")
                st.write(project.gauge)

        yarn_details = get_yarn_details_for_project(project.id)
        if yarn_details:
            st.markdown("**Yarns used**")
            for y in yarn_details:
                st.write(
                    f"- **{y['role']}** {y['yarn']}  |  "
                    f"Start: {y['start_g']}g  "
                    f"End: {y['end_g']}g  "
                    f"Used: {y['used_g']}"
                )

        if project.project_notes:
            st.markdown("**Notes**")
            st.info(project.project_notes)

    st.markdown("---")

# ---------------------------------------------------------------------------
# Spin projects
# ---------------------------------------------------------------------------

if project_type in ["All", "Spinning"] and spin_projects:
    st.markdown("## 🐑 Spin Projects")

    table_rows = [
        {
            "Project Name"  : p.project_name,
            "Date Completed": format_date(p.date_completed),
            "Status"        : status_badge(p),
        }
        for p in spin_projects
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    spin_name_options = ["— Select a project —"] + [p.project_name for p in spin_projects]
    selected_spin_name = st.selectbox(
        "View project details", spin_name_options, key="spin_select"
    )

    if selected_spin_name != "— Select a project —":
        project = next(p for p in spin_projects if p.project_name == selected_spin_name)
        badge = status_badge(project)

        st.markdown(f"### {badge}  |  {project.project_name}")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Fiber**")
            st.write(f"Content:  {project.fiber_content or '—'}")
            st.write(f"Weight:   {project.weight_grams}g")
            if project.plies:
                st.write(f"Plies:    {project.plies}")

        with col2:
            st.markdown("**Yarn produced**")
            st.write(f"Yards:    {project.measured_yards or '—'}")
            if project.measured_yards and project.weight_grams:
                yd_per_100g = (project.measured_yards / project.weight_grams) * 100
                st.write(f"Yd/100g:  {yd_per_100g:.1f}")
            if project.twist:
                st.write(f"Twist:    {project.twist}°")

        st.markdown("**Dates**")
        col3, col4 = st.columns(2)
        with col3:
            st.write(f"Started:   {format_date(project.date_started)}")
        with col4:
            st.write(f"Completed: {format_date(project.date_completed)}")

        if project.stash_id:
            yarn = get_stashyarn_by_id(project.stash_id, DB)
            if yarn:
                st.markdown("**Finished yarn (stash entry)**")
                st.success(
                    f"ID {yarn.id}  |  "
                    f"{yarn.size_notation} {yarn.fiber}  |  "
                    f"{yarn.yards_per_100g} yd/100g"
                    + (f"  |  {yarn.yarn_notes}" if yarn.yarn_notes else "")
                )

        if project.project_notes:
            st.markdown("**Notes**")
            st.info(project.project_notes)

# ---------------------------------------------------------------------------
# Empty state
# ---------------------------------------------------------------------------

if total == 0:
    st.info("No projects found. Try adjusting your filters, or add projects in the notebook.")
