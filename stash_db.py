
"""
Database layer for yarn stash.

Handles:
  - Creating the schema on first run
  - CRUD for yarns, knit projects, and spinning projects

All functions accept and return typed dataclass instances (from models.py).

"""


import sqlite3
from pathlib import Path
from typing import Optional

from models import StashYarn, ProjectYarn, KnitProject, SpinProject, SpinningTool, FiberPrep, SpinStyle
from seed_data import DEFAULT_SPINNINGTOOLS, DEFAULT_FIBERPREP, DEFAULT_SPINSTYLE


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS stash_yarn (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    size_notation       TEXT    NOT NULL,
    fiber               TEXT    NOT NULL,
    yards_per_100g      REAL    NOT NULL,
    wraps_per_inch      INTEGER, 
    brand               TEXT,
    yarn_content        TEXT,
    handspun            INTEGER NOT NULL DEFAULT 0,
    hand_dyed           INTEGER NOT NULL DEFAULT 0,
    yarn_notes          TEXT
);

CREATE TABLE IF NOT EXISTS project_yarn (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    starting_weight REAL,
    ending_weight   REAL,
    color_role      TEXT,
    stash_id        INTEGER,
    project_id      INTEGER,
    FOREIGN KEY (stash_id)   REFERENCES stash_yarn(id),
    FOREIGN KEY (project_id) REFERENCES knit_project(id)
);

CREATE TABLE IF NOT EXISTS knit_project (

    id                  INTEGER PRIMARY KEY AUTOINCREMENT,    
    project_name        TEXT NOT NULL,
    pattern_name        TEXT NOT NULL,
    pattern_source      TEXT NOT NULL,
    gauge               TEXT, 
    made_for            TEXT,
    project_notes       TEXT,
    date_started        TEXT,
    date_completed      TEXT
);

CREATE TABLE IF NOT EXISTS spin_project (

    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name        TEXT NOT NULL,
    weight_grams        REAL NOT NULL,
    fiber_content       TEXT,
    plies               INTEGER,
    measured_yards      INTEGER,
    twist               INTEGER,
    date_started        TEXT,
    date_completed      TEXT,
    project_notes       TEXT,
    stash_id        INTEGER,
    tool_id         INTEGER,
    fiber_prep_id   INTEGER,
    spin_style_id   INTEGER,
    FOREIGN KEY (stash_id)       REFERENCES stash_yarn(id),
    FOREIGN KEY (tool_id)        REFERENCES spinning_tool(id),
    FOREIGN KEY (fiber_prep_id)  REFERENCES fiber_prep(id),
    FOREIGN KEY (spin_style_id)  REFERENCES spin_style(id)
);

CREATE TABLE IF NOT EXISTS spinning_tool (
   
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,                   
    tool_type           TEXT NOT NULL,
    notes               TEXT

);


CREATE TABLE IF NOT EXISTS fiber_prep (

    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,                   
    notes               TEXT
);


CREATE TABLE IF NOT EXISTS spin_style (

    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,                   
    notes               TEXT

);

CREATE TABLE IF NOT EXISTS meta (
    key     TEXT PRIMARY KEY,
    value   TEXT
);
"""
# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------------------
# Init: create schema + seed defaults (only on first run)
# ---------------------------------------------------------------------------

def init_db(db_path: str = "fiber_projects.db") -> str:
    """
    Create the database file, apply the schema, and seed defaults if this
    is the first time the app has run. Returns the db_path for convenience.
    """
    conn = _connect(db_path)
    with conn:
        conn.executescript(SCHEMA)

        # Check whether we've seeded before
        already_seeded = conn.execute(
            "SELECT value FROM meta WHERE key = 'seeded'"
        ).fetchone()

        if not already_seeded:
            _seed(conn)
            conn.execute("INSERT INTO meta (key, value) VALUES ('seeded', '1')")

    conn.close()
    return db_path


def _seed(conn: sqlite3.Connection) -> None:
    """Insert all default reference data."""
    for tool in DEFAULT_SPINNINGTOOLS:
        _insert_tool(conn, tool)
    for prep in DEFAULT_FIBERPREP:
        _insert_fiberprep(conn, prep)
    for style in DEFAULT_SPINSTYLE:
        _insert_spinstyle(conn, style)


# ---------------------------------------------------------------------------
# SpinningTools
# ---------------------------------------------------------------------------

def _insert_tool(conn: sqlite3.Connection, tool: SpinningTool) -> int:
    cur = conn.execute(
        "INSERT INTO spinning_tool (name, tool_type, notes) VALUES (?,?,?)",
        (tool.name, tool.tool_type, tool.notes)
    )
    return cur.lastrowid


def add_tool(tool: SpinningTool, db_path: str = "fiber_projects.db") -> SpinningTool:
    """Insert a new tool; returns the tool with its new DB id."""
    conn = _connect(db_path)
    with conn:
        tool.id = _insert_tool(conn, tool)
    conn.close()
    return tool


def update_tool(tool: SpinningTool, db_path: str = "fiber_projects.db") -> None:
    """Update an existing tool by id."""
    if tool.id is None:
        raise ValueError("Cannot update a tool without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE spinning_tool
               SET name=?, tool_type=?, notes=?
               WHERE id=?""",
            (tool.name, tool.tool_type, tool.notes, tool.id)
        )
    conn.close()


def delete_tool(tool_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute("DELETE FROM spinning_tool WHERE id=?", (tool_id,))
    conn.close()


def get_all_tools(db_path: str = "fiber_projects.db") -> list[SpinningTool]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM spinning_tool ORDER BY name").fetchall()
    conn.close()
    return [SpinningTool(
        id=r["id"],
        name=r["name"],
        tool_type=r["tool_type"],
        notes=r["notes"]
    ) for r in rows]


def get_tool_by_id(tool_id: int, db_path: str = "fiber_projects.db") -> Optional[SpinningTool]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM spinning_tool WHERE id=?", (tool_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return SpinningTool(
        id=row["id"], 
        name=row["name"],
        tool_type=row["tool_type"],
        notes=row["notes"])


# ---------------------------------------------------------------------------
# FiberPrep
# ---------------------------------------------------------------------------

def _insert_fiberprep(conn: sqlite3.Connection, fiberprep: FiberPrep) -> int:
    cur = conn.execute(
        """INSERT INTO fiber_prep (name, notes) VALUES (?,?)""",
        (fiberprep.name, fiberprep.notes)
    )
    return cur.lastrowid


def add_fiberprep(fiberprep: FiberPrep, db_path: str = "fiber_projects.db") -> FiberPrep:
    conn = _connect(db_path)
    with conn: fiberprep.id = _insert_fiberprep(conn, fiberprep)
    conn.close()
    return fiberprep


def update_fiberprep(fiberprep: FiberPrep, db_path: str = "fiber_projects.db") -> None:
    if fiberprep.id is None:
        raise ValueError("Cannot update fiber prep style without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE fiber_prep SET name=?, notes=? WHERE id=?""",
            (fiberprep.name, fiberprep.notes, fiberprep.id)
        )
    conn.close()


def delete_fiberprep(fiberprep_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM fiber_prep WHERE id=?", (fiberprep_id,))
    conn.close()

def _row_to_fiberprep(row: sqlite3.Row) -> FiberPrep:
    return FiberPrep(
        id=row["id"],
        name=row["name"],
        notes=row["notes"]
    )
    
def get_all_fiberprep(db_path: str = "fiber_projects.db") -> list[FiberPrep]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM fiber_prep ORDER BY name").fetchall()
    conn.close()
    return [_row_to_fiberprep(r) for r in rows]


def get_fiberprep_by_id(fiberprep_id: int, db_path: str = "fiber_projects.db") -> Optional[FiberPrep]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM fiber_prep WHERE id=?", (fiberprep_id,)).fetchone()
    conn.close()
    return _row_to_fiberprep(row) if row else None



# ---------------------------------------------------------------------------
# Spin Style
# ---------------------------------------------------------------------------

def _insert_spinstyle(conn: sqlite3.Connection, spinstyle: SpinStyle) -> int:
    cur = conn.execute(
        """INSERT INTO spin_style (name, notes) VALUES (?,?)""",
        (spinstyle.name, spinstyle.notes)
    )
    return cur.lastrowid


def add_spinstyle(spinstyle: SpinStyle, db_path: str = "fiber_projects.db") -> SpinStyle:
    conn = _connect(db_path)
    with conn: spinstyle.id = _insert_spinstyle(conn, spinstyle)
    conn.close()
    return spinstyle


def update_spinstyle(spinstyle: SpinStyle, db_path: str = "fiber_projects.db") -> None:
    if spinstyle.id is None:
        raise ValueError("Cannot update a style of spinning without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE spin_style
               SET name=?, notes=?
               WHERE id=?""",
            (spinstyle.name, spinstyle.notes, spinstyle.id)
        )
    conn.close()


def delete_spinstyle(spinstyle_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM spin_style WHERE id=?", (spinstyle_id,))
    conn.close()

def _row_to_spinstyle(row: sqlite3.Row) -> SpinStyle:
    return SpinStyle(
        id=row["id"],
        name=row["name"],
        notes=row["notes"]
    )

def get_all_spinstyles(db_path: str = "fiber_projects.db") -> list[SpinStyle]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM spin_style ORDER BY name").fetchall()
    conn.close()
    return [_row_to_spinstyle(r) for r in rows]


def get_spinstyle_by_id(spinstyle_id: int, db_path: str = "fiber_projects.db") -> Optional[SpinStyle]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM spin_style WHERE id=?", (spinstyle_id,)).fetchone()
    conn.close()
    return _row_to_spinstyle(row) if row else None

    
# ---------------------------------------------------------------------------
# Stash Yarn
#Class name is StashYarn
#Table name is stash_yarn
# ---------------------------------------------------------------------------

def _insert_stashyarn(conn: sqlite3.Connection, stashyarn: StashYarn) -> int:
    cur = conn.execute(
        """INSERT INTO stash_yarn (size_notation, fiber, yards_per_100g, wraps_per_inch, brand, yarn_content, handspun, hand_dyed, yarn_notes) VALUES (?,?,?,?,?,?,?,?,?)""",
        (stashyarn.size_notation, stashyarn.fiber, stashyarn.yards_per_100g, stashyarn.wraps_per_inch, stashyarn.brand, stashyarn.yarn_content, stashyarn.handspun, stashyarn.hand_dyed, stashyarn.yarn_notes )
    )
    return cur.lastrowid

def add_stashyarn(stashyarn: StashYarn, db_path: str = "fiber_projects.db") -> StashYarn:
    conn = _connect(db_path)
    with conn: stashyarn.id = _insert_stashyarn(conn, stashyarn)
    conn.close()
    return stashyarn

def update_stashyarn(stashyarn: StashYarn, db_path: str = "fiber_projects.db") -> None:
    if stashyarn.id is None:
        raise ValueError("Cannot update yarn in the stash without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE stash_yarn
               SET size_notation=?, fiber=?, yards_per_100g=?, wraps_per_inch=?, brand=?, yarn_content=?, handspun=?, hand_dyed=?, yarn_notes=?
               WHERE id=?""",
            (stashyarn.size_notation, stashyarn.fiber, stashyarn.yards_per_100g, stashyarn.wraps_per_inch, stashyarn.brand, stashyarn.yarn_content, stashyarn.handspun, stashyarn.hand_dyed, stashyarn.yarn_notes, stashyarn.id)
        )
    conn.close()

def delete_stashyarn(stashyarn_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM stash_yarn WHERE id=?", (stashyarn_id,))
    conn.close()

def _row_to_stashyarn(row: sqlite3.Row) -> StashYarn:
    return StashYarn(
        id=row["id"],
        size_notation=row["size_notation"], 
        fiber=row["fiber"], 
        yards_per_100g=row["yards_per_100g"], 
        wraps_per_inch=row["wraps_per_inch"], 
        brand=row["brand"], 
        yarn_content=row["yarn_content"], 
        handspun=bool(row["handspun"]), 
        hand_dyed=bool(row["hand_dyed"]), 
        yarn_notes=row["yarn_notes"]
    )

def get_all_stashyarn_by_size(db_path: str = "fiber_projects.db") -> list[StashYarn]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM stash_yarn ORDER BY size_notation").fetchall()
    conn.close()
    return [_row_to_stashyarn(r) for r in rows]

def get_all_stashyarn_by_fiber(db_path: str = "fiber_projects.db") -> list[StashYarn]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM stash_yarn ORDER BY fiber").fetchall()
    conn.close()
    return [_row_to_stashyarn(r) for r in rows]

def get_stashyarn_by_fiber(fiber: str, db_path: str = "fiber_projects.db") -> list[StashYarn]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM stash_yarn WHERE LOWER(fiber)=LOWER(?) ORDER BY brand",
        (fiber,)
    ).fetchall()
    conn.close()
    return [_row_to_stashyarn(r) for r in rows]

def get_stashyarn_by_brand(db_path: str = "fiber_projects.db") -> list[StashYarn]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM stash_yarn ORDER BY brand").fetchall()
    conn.close()
    return [_row_to_stashyarn(r) for r in rows]

def get_stashyarn_by_id(stashyarn_id: int, db_path: str = "fiber_projects.db") -> Optional[StashYarn]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM stash_yarn WHERE id=?", (stashyarn_id,)).fetchone()
    conn.close()
    return _row_to_stashyarn(row) if row else None

def get_stashyarn_handspun(db_path: str = "fiber_projects.db") -> list[StashYarn]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM stash_yarn WHERE handspun=1 ORDER BY fiber"
    ).fetchall()
    conn.close()
    return [_row_to_stashyarn(r) for r in rows]

# ---------------------------------------------------------------------------
# Knit Project
#Class name is KnitProject
#Table name is knit_project
# ---------------------------------------------------------------------------

def _insert_knitproject(conn: sqlite3.Connection, knitproject: KnitProject) -> int:
    cur = conn.execute(
        """INSERT INTO knit_project (project_name, pattern_name, pattern_source, gauge, made_for, project_notes, date_started, date_completed) VALUES (?,?,?,?,?,?,?,?)""",
        (knitproject.project_name, knitproject.pattern_name, knitproject.pattern_source, knitproject.gauge, knitproject.made_for, knitproject.project_notes, knitproject.date_started, knitproject.date_completed)
    )
    return cur.lastrowid

def add_knitproject(knitproject: KnitProject, db_path: str = "fiber_projects.db") -> KnitProject:
    conn = _connect(db_path)
    with conn: knitproject.id = _insert_knitproject(conn, knitproject)
    conn.close()
    return knitproject

def update_knitproject(knitproject: KnitProject, db_path: str = "fiber_projects.db") -> None:
    if knitproject.id is None:
        raise ValueError("Cannot update knitting project without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE knit_project
               SET project_name=?, pattern_name=?, pattern_source=?, gauge=?, made_for=?, project_notes=?, date_started=?, date_completed=?
               WHERE id=?""",
            (knitproject.project_name, knitproject.pattern_name, knitproject.pattern_source, knitproject.gauge, knitproject.made_for, knitproject.project_notes, knitproject.date_started, knitproject.date_completed, knitproject.id)
        )
    conn.close()

def delete_knitproject(knitproject_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM knit_project WHERE id=?", (knitproject_id,))
    conn.close()

def _row_to_knitproject(row: sqlite3.Row) -> KnitProject:
    return KnitProject(
        id=row["id"],
        project_name=row["project_name"], 
        pattern_name=row["pattern_name"], 
        pattern_source=row["pattern_source"], 
        gauge=row["gauge"], 
        made_for=row["made_for"], 
        project_notes=row["project_notes"], 
        date_started=row["date_started"], 
        date_completed=row["date_completed"]
    )
    
def get_all_knitproject(db_path: str = "fiber_projects.db") -> list[KnitProject]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM knit_project ORDER BY project_name").fetchall()
    conn.close()
    return [_row_to_knitproject(r) for r in rows]
    
def get_knitproject_by_date_completed(db_path: str = "fiber_projects.db") -> list[KnitProject]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM knit_project ORDER BY date_completed").fetchall()
    conn.close()
    return [_row_to_knitproject(r) for r in rows]

def get_knitproject_by_id(knitproject_id: int, db_path: str = "fiber_projects.db") -> Optional[KnitProject]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM knit_project WHERE id=?", (knitproject_id,)).fetchone()
    conn.close()
    return _row_to_knitproject(row) if row else None

# ---------------------------------------------------------------------------
# Spin Project
#Class name is SpinProject
#Table name is spin_project
# ---------------------------------------------------------------------------

def _insert_spinproject(conn: sqlite3.Connection, spinproject: SpinProject) -> int:
    cur = conn.execute(
        """INSERT INTO spin_project (project_name, weight_grams, fiber_content, plies, measured_yards, twist, date_started, date_completed, project_notes, tool_id, fiber_prep_id, spin_style_id, stash_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (spinproject.project_name, spinproject.weight_grams, spinproject.fiber_content, spinproject.plies, spinproject.measured_yards, spinproject.twist, spinproject.date_started, spinproject.date_completed, spinproject.project_notes, spinproject.tool_id, spinproject.fiber_prep_id, spinproject.spin_style_id,
 spinproject.stash_id)
    )
    return cur.lastrowid

def add_spinproject(spinproject: SpinProject, db_path: str = "fiber_projects.db") -> SpinProject:
    conn = _connect(db_path)
    with conn: spinproject.id = _insert_spinproject(conn, spinproject)
    conn.close()
    return spinproject

def update_spinproject(spinproject: SpinProject, db_path: str = "fiber_projects.db") -> None:
    if spinproject.id is None:
        raise ValueError("Cannot update spinning project without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE spin_project
               SET project_name=?, weight_grams=?, fiber_content=?, plies=?, measured_yards=?, twist=?, date_started=?, date_completed=?, project_notes=?, tool_id=?, fiber_prep_id=?, spin_style_id=?, stash_id=?
               WHERE id=?""",
            (spinproject.project_name, spinproject.weight_grams, spinproject.fiber_content, spinproject.plies, spinproject.measured_yards, spinproject.twist, spinproject.date_started, spinproject.date_completed, spinproject.project_notes, spinproject.id, spinproject.tool_id, spinproject.fiber_prep_id, spinproject.spin_style_id, spinproject.stash_id)
        )
    conn.close()

def delete_spinproject(spinproject_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM spin_project WHERE id=?", (spinproject_id,))
    conn.close()

def _row_to_spinproject(row: sqlite3.Row) -> SpinProject:
    return SpinProject(
        id=row["id"],
        project_name=row["project_name"], 
        weight_grams=row["weight_grams"], 
        fiber_content=row["fiber_content"], 
        plies=row["plies"], 
        measured_yards=row["measured_yards"],
        twist=row["twist"],
        date_started=row["date_started"], 
        date_completed=row["date_completed"],
        project_notes=row["project_notes"],
        tool_id=row["tool_id"],
        fiber_prep_id=row["fiber_prep_id"],
        spin_style_id=row["spin_style_id"],
        stash_id=row["stash_id"]
    )
    
def get_all_spinproject(db_path: str = "fiber_projects.db") -> list[SpinProject]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM spin_project ORDER BY project_name").fetchall()
    conn.close()
    return [_row_to_spinproject(r) for r in rows]
    
def get_spinproject_by_id(spinproject_id: int, db_path: str = "fiber_projects.db") -> Optional[SpinProject]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM spin_project WHERE id=?", (spinproject_id,)).fetchone()
    conn.close()
    return _row_to_spinproject(row) if row else None

def complete_spinproject(
    spinproject_id: int,
    db_path: str = "fiber_projects.db",
    measured_yards: Optional[float] = None,
    date_completed: Optional[str] = None,
    # StashYarn fields for the finished yarn
    size_notation: str = "",
    fiber: str = "",
    yards_per_100g: float = 0.0,
    brand: Optional[str] = None,
    yarn_notes: Optional[str] = None,
) -> tuple[SpinProject, StashYarn]:
    """
    Complete a spin project by:
    1. Creating a new StashYarn entry from the finished yarn details
    2. Updating the SpinProject with the stash_id and completion info
    Returns both the updated SpinProject and the new StashYarn.
    """
    import datetime

    # Step 1 — create the StashYarn entry
    new_yarn = StashYarn(
        size_notation  = size_notation,
        fiber          = fiber,
        yards_per_100g = yards_per_100g,
        brand          = brand,
        handspun       = True,
        yarn_notes     = yarn_notes,
    )
    new_yarn = add_stashyarn(new_yarn, db_path)

    # Step 2 — update the SpinProject with completion info and stash_id
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE spin_project
               SET stash_id=?, measured_yards=?, date_completed=?
               WHERE id=?""",
            (
                new_yarn.id,
                measured_yards,
                date_completed or datetime.date.today().isoformat(),
                spinproject_id,
            )
        )
    conn.close()

    return get_spinproject_by_id(spinproject_id, db_path), new_yarn

# ---------------------------------------------------------------------------
# Project Yarn
#Class name is ProjectYarn
#Table name is project_yarn
# ---------------------------------------------------------------------------


def _insert_projectyarn(conn: sqlite3.Connection, projectyarn: ProjectYarn) -> int:
    cur = conn.execute(
        """INSERT INTO project_yarn (starting_weight, ending_weight, color_role, stash_id, project_id) VALUES (?,?,?,?,?)""",
        (projectyarn.starting_weight, projectyarn.ending_weight, projectyarn.color_role, projectyarn.stash_id, projectyarn.project_id)
    )
    return cur.lastrowid

def add_projectyarn(projectyarn: ProjectYarn, db_path: str = "fiber_projects.db") -> ProjectYarn:
    conn = _connect(db_path)
    with conn: projectyarn.id = _insert_projectyarn(conn, projectyarn)
    conn.close()
    return projectyarn

def update_projectyarn(projectyarn: ProjectYarn, db_path: str = "fiber_projects.db") -> None:
    if projectyarn.id is None:
        raise ValueError("Cannot update project yarn without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE project_yarn
               SET starting_weight=?, ending_weight=?, color_role=?, stash_id=?, project_id=?
               WHERE id=?""",
            (projectyarn.starting_weight, projectyarn.ending_weight, projectyarn.color_role, projectyarn.stash_id, projectyarn.project_id, projectyarn.id)
        )
    conn.close()

def delete_projectyarn(projectyarn_id: int, db_path: str = "fiber_projects.db") -> None:
    conn = _connect(db_path)
    with conn: conn.execute("DELETE FROM project_yarn WHERE id=?", (projectyarn_id,))
    conn.close()

def _row_to_projectyarn(row: sqlite3.Row) -> ProjectYarn:
    return ProjectYarn(
        id=row["id"],
        starting_weight=row["starting_weight"], 
        ending_weight=row["ending_weight"], 
        color_role=row["color_role"], 
        stash_id=row["stash_id"], 
        project_id=row["project_id"]
    )
    
def get_all_projectyarn(db_path: str = "fiber_projects.db") -> list[ProjectYarn]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM project_yarn ORDER BY id").fetchall()
    conn.close()
    return [_row_to_projectyarn(r) for r in rows]
    
def get_projectyarn_by_id(projectyarn_id: int, db_path: str = "fiber_projects.db") -> Optional[ProjectYarn]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM project_yarn WHERE id=?", (projectyarn_id,)).fetchone()
    conn.close()
    return _row_to_projectyarn(row) if row else None

def get_projectyarn_by_project(project_id: int, db_path: str = "fiber_projects.db") -> list[ProjectYarn]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM project_yarn WHERE project_id=?", (project_id,)
    ).fetchall()
    conn.close()
    return [_row_to_projectyarn(r) for r in rows]