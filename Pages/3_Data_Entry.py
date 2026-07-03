"""
pages/3_Data_Entry.py — Data Entry Page

Two workflows — Knit/Crochet Project and Spinning Project — each shows
every form you'd want when starting or finishing that kind of project,
stacked on one page. No extra dropdown-hopping required.

Reuses all existing functions from stash_db.py — no new database logic
lives here, only the Streamlit form layer.
"""

import streamlit as st
import datetime
import sys, os
sys.path.insert(0, os.getcwd())

from models import StashYarn, KnitProject, SpinProject, ProjectYarn, SpinningTool, FiberPrep, SpinStyle
from stash_db import (
    init_db,
    add_tool, get_all_tools,
    add_fiberprep, get_all_fiberprep,
    add_spinstyle, get_all_spinstyles,
    add_stashyarn, get_stashyarn_by_brand, get_stashyarn_by_id,
    add_knitproject, get_all_knitproject, update_knitproject,
    add_spinproject, get_all_spinproject, complete_spinproject,
    add_projectyarn, get_projectyarn_by_project, update_projectyarn,
)

st.set_page_config(
    page_title = "Fiber Projects — Data Entry",
    page_icon  = "➕",
    layout     = "wide",
)

DB = init_db("fiber_projects.db")

st.title("➕ Data Entry")

# session_state keeps track of "the project I'm currently working on"
# across forms on this page, so attaching yarn knows which project to use
# without you having to look up and re-select it.
if "active_knit_project_id" not in st.session_state:
    st.session_state.active_knit_project_id = None
if "active_spin_project_id" not in st.session_state:
    st.session_state.active_spin_project_id = None

# ---------------------------------------------------------------------------
# Top-level choice
# ---------------------------------------------------------------------------

workflow = st.radio(
    "What are you working on?",
    ["— Select —", "Knit / Crochet Project", "Spinning Project", "Reference Data"],
    horizontal=True,
)

st.markdown("---")

# ===========================================================================
# KNIT / CROCHET WORKFLOW
# ===========================================================================

if workflow == "Knit / Crochet Project":

    # -----------------------------------------------------------------
    # Section 1 — pick an existing project to work on, or start a new one
    # -----------------------------------------------------------------

    st.markdown("## 1 · Project")

    existing_knit = get_all_knitproject(DB)
    in_progress_knit = [p for p in existing_knit if not p.date_completed]

    project_pick_options = ["— Start a new project —"] + [
        f"{p.project_name} (ID {p.id})" for p in in_progress_knit
    ]
    picked = st.selectbox("Continue an existing project, or start new", project_pick_options)

    if picked == "— Start a new project —":
        with st.form("knit_project_form"):
            project_name   = st.text_input("Project name*")
            pattern_name   = st.text_input("Pattern name* (use 'Self-drafted' if no pattern)")
            pattern_source = st.text_input("Pattern source* (e.g. Ravelry, designer name, book title)")
            gauge          = st.text_input("Gauge (optional)")
            made_for       = st.text_input("Made for (optional)")
            date_started   = st.date_input("Date started", value=datetime.date.today())
            project_notes  = st.text_area("Notes (optional)")

            submitted = st.form_submit_button("Save project")

            if submitted:
                if not project_name or not pattern_name or not pattern_source:
                    st.error("Project name, pattern name, and pattern source are required.")
                else:
                    new_project = add_knitproject(
                        KnitProject(
                            project_name   = project_name,
                            pattern_name   = pattern_name,
                            pattern_source = pattern_source,
                            gauge          = gauge or None,
                            made_for       = made_for or None,
                            date_started   = date_started.isoformat(),
                            project_notes  = project_notes or None,
                        ),
                        DB,
                    )
                    st.session_state.active_knit_project_id = new_project.id
                    st.success(f"✅ Saved! Project ID {new_project.id}: {new_project.project_name}")
    else:
        # extract the ID from the "(ID X)" suffix in the selected label
        matched_project = next(p for p in in_progress_knit if f"(ID {p.id})" in picked)
        st.session_state.active_knit_project_id = matched_project.id
        st.info(f"Working on: **{matched_project.project_name}**")

    active_project_id = st.session_state.active_knit_project_id

    # -----------------------------------------------------------------
    # Section 2 — add a new stash yarn (optional, if it's not in stash yet)
    # -----------------------------------------------------------------

    st.markdown("## 2 · Add a stash yarn (skip if you already have one)")

    with st.form("knit_stashyarn_form"):
        size_notation  = st.text_input("Size notation (e.g. fingering, dk, worsted)")
        fiber          = st.text_input("Fiber (e.g. merino, cotton, alpaca)")
        yards_per_100g = st.number_input("Yards per 100g", min_value=0.0, step=1.0)
        wraps_per_inch = st.number_input("Wraps per inch (optional)", min_value=0, step=1, value=0)
        brand          = st.text_input("Brand (optional)")
        yarn_content   = st.text_input("Yarn content (optional)")
        handspun       = st.checkbox("Handspun")
        hand_dyed      = st.checkbox("Hand-dyed")
        yarn_notes     = st.text_area("Notes (optional)", key="knit_yarn_notes")

        submitted = st.form_submit_button("Save yarn to stash")

        if submitted:
            if not size_notation or not fiber or yards_per_100g <= 0:
                st.error("Size notation, fiber, and yards per 100g are required.")
            else:
                new_yarn = add_stashyarn(
                    StashYarn(
                        size_notation  = size_notation,
                        fiber          = fiber,
                        yards_per_100g = yards_per_100g,
                        wraps_per_inch = wraps_per_inch or None,
                        brand          = brand or None,
                        yarn_content   = yarn_content or None,
                        handspun       = handspun,
                        hand_dyed      = hand_dyed,
                        yarn_notes     = yarn_notes or None,
                    ),
                    DB,
                )
                st.success(f"✅ Saved! Yarn ID {new_yarn.id}: {new_yarn.size_notation} {new_yarn.fiber}")

    # -----------------------------------------------------------------
    # Section 3 — attach one or more yarns to the active project
    # -----------------------------------------------------------------

    st.markdown("## 3 · Attach yarn(s) to this project")

    if not active_project_id:
        st.info("Start or select a project above first.")
    else:
        stash_yarns = get_stashyarn_by_brand(DB)
        if not stash_yarns:
            st.warning("No stash yarns yet — add one in Section 2 above.")
        else:
            yarn_options = {
                f"{y.brand or '—'} {y.size_notation} {y.fiber} (ID {y.id})": y.id
                for y in stash_yarns
            }

            num_yarns = st.number_input(
                "How many yarns to attach right now?", min_value=1, max_value=6, value=1, step=1
            )

            with st.form("knit_attach_yarn_form"):
                yarn_rows = []
                for i in range(int(num_yarns)):
                    st.markdown(f"**Yarn {i + 1}**")
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        yarn_choice = st.selectbox(
                            "Stash yarn", yarn_options.keys(), key=f"yarn_choice_{i}"
                        )
                    with col2:
                        color_role = st.text_input(
                            "Color role (MC, CC1...)", key=f"color_role_{i}"
                        )
                    with col3:
                        starting_weight = st.number_input(
                            "Starting wt (g)", min_value=0.0, step=1.0, key=f"starting_weight_{i}"
                        )
                    yarn_rows.append((yarn_choice, color_role, starting_weight))

                submitted = st.form_submit_button("Attach yarn(s) to project")

                if submitted:
                    count = 0
                    for yarn_choice, color_role, starting_weight in yarn_rows:
                        new_py = add_projectyarn(
                            ProjectYarn(
                                project_id      = active_project_id,
                                stash_id        = yarn_options[yarn_choice],
                                color_role      = color_role or None,
                                starting_weight = starting_weight if starting_weight > 0 else None,
                            ),
                            DB,
                        )
                        count += 1
                    st.success(f"✅ Attached {count} yarn(s) to the project.")

    # -----------------------------------------------------------------
    # Section 4 — complete the project (final weights + completion date)
    # -----------------------------------------------------------------

    st.markdown("## 4 · Complete this project")

    if not active_project_id:
        st.info("Start or select a project above first.")
    else:
        project_yarns = get_projectyarn_by_project(active_project_id, DB)

        if not project_yarns:
            st.info("No yarn attached yet — finish Section 3 before completing.")
        else:
            with st.form("knit_complete_form"):
                date_completed = st.date_input("Date completed", value=datetime.date.today())
                project_notes  = st.text_area("Final notes (optional)", key="knit_complete_notes")

                st.markdown("**Final weight for each yarn used**")
                ending_weight_inputs = {}
                for py in project_yarns:
                    yarn = get_stashyarn_by_id(py.stash_id, DB)
                    yarn_label = f"{yarn.brand or '—'} {yarn.size_notation} {yarn.fiber}" if yarn else "Unknown yarn"
                    role_label = f" ({py.color_role})" if py.color_role else ""

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"{yarn_label}{role_label}  —  started at "
                                 f"{py.starting_weight if py.starting_weight is not None else '—'}g")
                    with col2:
                        ending_weight_inputs[py.id] = st.number_input(
                            "Final wt (g)", min_value=0.0, step=1.0, key=f"ending_weight_{py.id}"
                        )

                submitted = st.form_submit_button("Mark project complete")

                if submitted:
                    project = next(p for p in existing_knit if p.id == active_project_id)
                    project.date_completed = date_completed.isoformat()
                    project.project_notes  = project_notes or project.project_notes
                    update_knitproject(project, DB)

                    total_yards_used = 0.0
                    for py in project_yarns:
                        ending_weight = ending_weight_inputs[py.id]
                        if ending_weight > 0:
                            py.ending_weight = ending_weight
                            update_projectyarn(py, DB)
                            yarn = get_stashyarn_by_id(py.stash_id, DB)
                            if yarn and py.grams_used:
                                total_yards_used += (py.grams_used / 100) * yarn.yards_per_100g

                    st.success(
                        f"✅ {project.project_name} marked complete! "
                        f"Approx. {total_yards_used:.1f} yards used."
                    )
                    st.session_state.active_knit_project_id = None

# ===========================================================================
# SPINNING WORKFLOW
# ===========================================================================

elif workflow == "Spinning Project":

    st.markdown("## 1 · Project")

    existing_spin = get_all_spinproject(DB)
    in_progress_spin = [p for p in existing_spin if not p.date_completed]

    tools  = get_all_tools(DB)
    preps  = get_all_fiberprep(DB)
    styles = get_all_spinstyles(DB)

    project_pick_options = ["— Start a new project —"] + [
        f"{p.project_name} (ID {p.id})" for p in in_progress_spin
    ]
    picked = st.selectbox("Continue an existing project, or start new", project_pick_options)

    if picked == "— Start a new project —":
        if not tools or not preps or not styles:
            st.warning("Add at least one tool, fiber prep, and spin style under "
                        "'Reference Data' before creating a spin project.")
        else:
            tool_options  = {t.name: t.id for t in tools}
            prep_options  = {p.name: p.id for p in preps}
            style_options = {s.name: s.id for s in styles}

            with st.form("spin_project_form"):
                project_name  = st.text_input("Project name*")
                weight_grams  = st.number_input("Starting fiber weight (grams)*", min_value=0.0, step=1.0)
                fiber_content = st.text_input("Fiber content (optional)")
                plies         = st.number_input("Plies (optional)", min_value=0, step=1, value=0)
                twist         = st.number_input("Twist in degrees (optional)", min_value=0, step=1, value=0)
                date_started  = st.date_input("Date started", value=datetime.date.today())
                project_notes = st.text_area("Notes (optional)")

                tool_choice  = st.selectbox("Tool used*", tool_options.keys())
                prep_choice  = st.selectbox("Fiber prep*", prep_options.keys())
                style_choice = st.selectbox("Spin style*", style_options.keys())

                submitted = st.form_submit_button("Save project")

                if submitted:
                    if not project_name or weight_grams <= 0:
                        st.error("Project name and starting weight are required.")
                    else:
                        new_project = add_spinproject(
                            SpinProject(
                                project_name  = project_name,
                                weight_grams  = weight_grams,
                                fiber_content = fiber_content or None,
                                plies         = plies or None,
                                twist         = twist or None,
                                date_started  = date_started.isoformat(),
                                project_notes = project_notes or None,
                                tool_id       = tool_options[tool_choice],
                                fiber_prep_id = prep_options[prep_choice],
                                spin_style_id = style_options[style_choice],
                            ),
                            DB,
                        )
                        st.session_state.active_spin_project_id = new_project.id
                        st.success(f"✅ Saved! Spin project ID {new_project.id}: {new_project.project_name}")
    else:
        matched_project = next(p for p in in_progress_spin if f"(ID {p.id})" in picked)
        st.session_state.active_spin_project_id = matched_project.id
        st.info(f"Working on: **{matched_project.project_name}**")

    active_spin_id = st.session_state.active_spin_project_id

    st.markdown("## 2 · Complete this spin project")
    st.caption("Completing automatically creates a new stash yarn entry from the details below.")

    if not active_spin_id:
        st.info("Start or select a spin project above first.")
    else:
        project = next(p for p in existing_spin if p.id == active_spin_id)

        with st.form("spin_complete_form"):
            measured_yards = st.number_input("Measured yards", min_value=0.0, step=1.0)
            date_completed = st.date_input("Date completed", value=datetime.date.today(), key="spin_date_completed")

            st.markdown("**Finished yarn details (creates a stash yarn entry)**")
            size_notation = st.text_input("Size notation* (e.g. fingering, dk)")
            fiber         = st.text_input("Fiber* (e.g. merino, blue-faced leicester)")

            if measured_yards > 0 and project.weight_grams > 0:
                suggested_ypg = round((measured_yards / project.weight_grams) * 100, 1)
                st.caption(f"Suggested yards/100g based on weight and yardage: {suggested_ypg}")
            else:
                suggested_ypg = 0.0

            yards_per_100g = st.number_input(
                "Yards per 100g*", min_value=0.0, step=1.0, value=suggested_ypg
            )
            yarn_notes = st.text_area("Yarn notes (optional)", key="spin_yarn_notes")

            submitted = st.form_submit_button("Complete project & create stash yarn")

            if submitted:
                if not size_notation or not fiber or yards_per_100g <= 0:
                    st.error("Size notation, fiber, and yards per 100g are required.")
                else:
                    spin_project, new_yarn = complete_spinproject(
                        spinproject_id = project.id,
                        db_path        = DB,
                        measured_yards = measured_yards or None,
                        date_completed = date_completed.isoformat(),
                        size_notation  = size_notation,
                        fiber          = fiber,
                        yards_per_100g = yards_per_100g,
                        yarn_notes     = yarn_notes or None,
                    )
                    st.success(
                        f"✅ Project completed! New stash yarn created: "
                        f"ID {new_yarn.id} — {new_yarn.size_notation} {new_yarn.fiber} "
                        f"({new_yarn.yards_per_100g} yd/100g)"
                    )
                    st.session_state.active_spin_project_id = None

# ===========================================================================
# REFERENCE DATA
# ===========================================================================

elif workflow == "Reference Data":
    st.markdown("## Reference data")

    ref_type = st.radio("Type", ["Spinning tool", "Fiber prep", "Spin style"], horizontal=True)

    if ref_type == "Spinning tool":
        with st.form("add_tool_form"):
            name      = st.text_input("Tool name*")
            tool_type = st.text_input("Tool type* (e.g. wheel, spindle, electric wheel)")
            notes     = st.text_input("Notes (optional)")
            submitted = st.form_submit_button("Save tool")
            if submitted:
                if not name or not tool_type:
                    st.error("Name and tool type are required.")
                else:
                    new_tool = add_tool(SpinningTool(name=name, tool_type=tool_type, notes=notes or None), DB)
                    st.success(f"✅ Saved! Tool ID {new_tool.id}: {new_tool.name}")

    elif ref_type == "Fiber prep":
        with st.form("add_prep_form"):
            name      = st.text_input("Prep name* (e.g. combed top, batt, rolag)")
            notes     = st.text_input("Notes (optional)")
            submitted = st.form_submit_button("Save fiber prep")
            if submitted:
                if not name:
                    st.error("Name is required.")
                else:
                    new_prep = add_fiberprep(FiberPrep(name=name, notes=notes or None), DB)
                    st.success(f"✅ Saved! Fiber prep ID {new_prep.id}: {new_prep.name}")

    elif ref_type == "Spin style":
        with st.form("add_style_form"):
            name      = st.text_input("Style name* (e.g. long draw, short forward draw)")
            notes     = st.text_input("Notes (optional)")
            submitted = st.form_submit_button("Save spin style")
            if submitted:
                if not name:
                    st.error("Name is required.")
                else:
                    new_style = add_spinstyle(SpinStyle(name=name, notes=notes or None), DB)
                    st.success(f"✅ Saved! Spin style ID {new_style.id}: {new_style.name}")
