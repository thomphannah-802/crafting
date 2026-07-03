"""
projects.py — save, retrieve, and update weaving projects

A project has two stages:
  1. PLANNED   — created from a WarpPlan, all calculated fields filled in
  2. COMPLETED — updated after weaving with actual measurements and notes

Actual yardage is derived from actual_weight_grams using the warp yarn's
yards_per_pound (stored at save time). For multi-weft projects this is an
estimate.

Disposition options: "gift", "for_sale", "personal_keep", "sample"
"""

import sqlite3
import datetime
import json
from dataclasses import dataclass, field
from typing import Optional

from calculator import WarpPlan


PROJECTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (

    -- identity
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name            TEXT    NOT NULL,
    date_planned            TEXT    NOT NULL,

    -- planned inputs (echoed from WarpPlan)
    loom_name               TEXT    NOT NULL,
    yarn_name               TEXT    NOT NULL,
    yarn_yards_per_pound    INTEGER NOT NULL,
    structure_name          TEXT    NOT NULL,
    sett                    INTEGER NOT NULL,
    ppi                     INTEGER NOT NULL,
    take_up_pct             REAL    NOT NULL,
    gap_allowance           REAL    NOT NULL,

    -- planned warp outputs
    total_ends              INTEGER NOT NULL,
    warp_length_inches      REAL    NOT NULL,
    warp_length_yards       REAL    NOT NULL,
    planned_warp_yards      REAL    NOT NULL,
    planned_warp_weight_oz  REAL    NOT NULL,

    -- planned weft outputs
    planned_weft_yards      REAL    NOT NULL,
    planned_weft_weight_oz  REAL    NOT NULL,

    -- planned combined
    planned_total_yards     REAL    NOT NULL,
    planned_total_weight_oz REAL    NOT NULL,

    -- piece and weft detail stored as JSON
    piece_details_json      TEXT    NOT NULL,
    weft_summary_json       TEXT    NOT NULL,

    -- completion fields (all nullable until finished)
    date_completed          TEXT,
    actual_weight_grams     REAL,
    actual_yards_used       REAL,   -- derived from weight at completion time
    actual_length_inches    REAL,
    actual_width_inches     REAL,
    disposition             TEXT,
    completion_notes        TEXT,
    photo                   BLOB
);
"""

VALID_DISPOSITIONS = {"gift", "for_sale", "personal_keep", "sample"}


# ---------------------------------------------------------------------------
# Project dataclass
# ---------------------------------------------------------------------------

@dataclass
class Project:
    # --- identity ---
    project_name:               str
    date_planned:               str

    # --- planned inputs ---
    loom_name:                  str
    yarn_name:                  str
    yarn_yards_per_pound:       int
    structure_name:             str
    sett:                       int
    ppi:                        int
    take_up_pct:                float
    gap_allowance:              float

    # --- planned warp ---
    total_ends:                 int
    warp_length_inches:         float
    warp_length_yards:          float
    planned_warp_yards:         float
    planned_warp_weight_oz:     float

    # --- planned weft ---
    planned_weft_yards:         float
    planned_weft_weight_oz:     float

    # --- planned combined ---
    planned_total_yards:        float
    planned_total_weight_oz:    float

    # --- JSON detail fields ---
    piece_details_json:         str
    weft_summary_json:          str

    # --- completion (all optional) ---
    date_completed:             Optional[str]   = None
    actual_weight_grams:        Optional[float] = None
    actual_yards_used:          Optional[float] = None   # derived on complete
    actual_length_inches:       Optional[float] = None
    actual_width_inches:        Optional[float] = None
    disposition:                Optional[str]   = None
    completion_notes:           Optional[str]   = None
    photo:                      Optional[bytes] = None

    id:                         Optional[int]   = None

    def __post_init__(self):
        if self.disposition and self.disposition not in VALID_DISPOSITIONS:
            raise ValueError(
                f"Invalid disposition '{self.disposition}'. "
                f"Must be one of: {', '.join(VALID_DISPOSITIONS)}"
            )

    @property
    def is_complete(self) -> bool:
        return self.date_completed is not None

    @property
    def status(self) -> str:
        return "Completed" if self.is_complete else "Planned"

    @property
    def weft_summary(self) -> list[dict]:
        return json.loads(self.weft_summary_json)

    def summary(self) -> str:
        lines = [
            "",
            "=" * 62,
            f"  {self.project_name.upper()}  [{self.status}]",
            "=" * 62,
            f"  Planned     : {self.date_planned}",
            f"  Loom        : {self.loom_name}",
            f"  Yarn        : {self.yarn_name}",
            f"  Structure   : {self.structure_name}",
            f"  Sett        : {self.sett} EPI   PPI: {self.ppi}",
            "-" * 62,
            "  PLANNED — WARP",
            f"  Ends        : {self.total_ends}",
            f"  Warp length : {self.warp_length_inches:.1f}\" ({self.warp_length_yards:.2f} yd/end)",
            f"  Warp yards  : {self.planned_warp_yards:.1f} yards ({self.planned_warp_weight_oz:.1f} oz)",
            "-" * 62,
            "  PLANNED — WEFT",
        ]
        for w in self.weft_summary:
            lines.append(
                f"  {w['yarn_name']:<35} "
                f"{w['total_yards']:>7.1f} yards total  "
                f"({w['yards_per_piece']:.1f} yd/piece)"
            )
        lines += [
            f"  Total weft  : {self.planned_weft_yards:.1f} yards ({self.planned_weft_weight_oz:.1f} oz)",
            "-" * 62,
            "  PLANNED — COMBINED",
            f"  Total yards : {self.planned_total_yards:.1f}",
            f"  Total weight: {self.planned_total_weight_oz:.1f} oz  "
            f"({self.planned_total_weight_oz/16:.2f} lbs)",
        ]
        if self.is_complete:
            lines += [
                "-" * 62,
                "  ACTUAL",
                f"  Completed   : {self.date_completed}",
            ]
            if self.actual_weight_grams is not None:
                lines.append(f"  Weight      : {self.actual_weight_grams:.1f} g")
            if self.actual_yards_used is not None:
                diff = self.actual_yards_used - self.planned_total_yards
                sign = "+" if diff >= 0 else ""
                lines.append(
                    f"  Yards used  : {self.actual_yards_used:.1f}  "
                    f"({sign}{diff:.1f} vs planned)"
                )
            if self.actual_length_inches and self.actual_width_inches:
                lines.append(
                    f"  Dimensions  : {self.actual_width_inches}\" x {self.actual_length_inches}\""
                )
            if self.disposition:
                lines.append(f"  Disposition : {self.disposition.replace('_', ' ').title()}")
            if self.completion_notes:
                lines.append(f"  Notes       : {self.completion_notes}")
            if self.photo:
                lines.append(f"  Photo       : stored")
        lines.append("=" * 62)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Build a Project from a WarpPlan
# ---------------------------------------------------------------------------

def project_from_plan(plan: WarpPlan, project_name: str) -> "Project":
    """
    Create a Project from a calculated WarpPlan.
    Captures yards_per_pound at this moment so completion math is stable
    even if the yarn reference entry is later edited.
    """
    return Project(
        project_name            = project_name,
        date_planned            = datetime.date.today().isoformat(),
        loom_name               = plan.loom_name,
        yarn_name               = plan.yarn_name,
        yarn_yards_per_pound    = plan.yarn_yards_per_pound,
        structure_name          = plan.structure_name,
        sett                    = plan.sett,
        ppi                     = plan.ppi,
        take_up_pct             = plan.take_up_pct,
        gap_allowance           = plan.gap_allowance,
        total_ends              = plan.total_ends,
        warp_length_inches      = plan.warp_length_inches,
        warp_length_yards       = plan.warp_length_yards,
        planned_warp_yards      = plan.warp_yards,
        planned_warp_weight_oz  = plan.warp_weight_oz,
        planned_weft_yards      = plan.total_weft_yards,
        planned_weft_weight_oz  = plan.total_weft_weight_oz,
        planned_total_yards     = plan.total_yards,
        planned_total_weight_oz = plan.total_weight_oz,
        piece_details_json      = json.dumps(plan.piece_details),
        weft_summary_json       = json.dumps(plan.weft_summary),
    )


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_projects_table(db_path: str = "warp_calc.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.executescript(PROJECTS_SCHEMA)
    conn.close()


def save_project(project: Project, db_path: str = "warp_calc.db") -> Project:
    conn = _connect(db_path)
    with conn:
        cur = conn.execute(
            """INSERT INTO projects (
                project_name, date_planned,
                loom_name, yarn_name, yarn_yards_per_pound,
                structure_name, sett, ppi, take_up_pct, gap_allowance,
                total_ends, warp_length_inches, warp_length_yards,
                planned_warp_yards, planned_warp_weight_oz,
                planned_weft_yards, planned_weft_weight_oz,
                planned_total_yards, planned_total_weight_oz,
                piece_details_json, weft_summary_json
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                project.project_name, project.date_planned,
                project.loom_name, project.yarn_name, project.yarn_yards_per_pound,
                project.structure_name, project.sett, project.ppi,
                project.take_up_pct, project.gap_allowance,
                project.total_ends, project.warp_length_inches,
                project.warp_length_yards, project.planned_warp_yards,
                project.planned_warp_weight_oz, project.planned_weft_yards,
                project.planned_weft_weight_oz, project.planned_total_yards,
                project.planned_total_weight_oz,
                project.piece_details_json, project.weft_summary_json,
            )
        )
        project.id = cur.lastrowid
    conn.close()
    return project


def complete_project(
    project_id:             int,
    db_path:                str = "warp_calc.db",
    actual_weight_grams:    Optional[float] = None,
    actual_length_inches:   Optional[float] = None,
    actual_width_inches:    Optional[float] = None,
    disposition:            Optional[str]   = None,
    completion_notes:       Optional[str]   = None,
    photo:                  Optional[bytes] = None,
    date_completed:         Optional[str]   = None,
) -> "Project":
    """
    Update a planned project with completion data.
    actual_yards_used is derived automatically from actual_weight_grams
    using the yarn's yards_per_pound stored at save time.
    """
    if disposition and disposition not in VALID_DISPOSITIONS:
        raise ValueError(
            f"Invalid disposition '{disposition}'. "
            f"Must be one of: {', '.join(VALID_DISPOSITIONS)}"
        )

    date_completed = date_completed or datetime.date.today().isoformat()

    # derive actual yardage from weight if weight was provided
    actual_yards_used = None
    if actual_weight_grams is not None:
        project = get_project_by_id(project_id, db_path)
        if project:
            weight_lbs = actual_weight_grams / 453.592
            actual_yards_used = round(weight_lbs * project.yarn_yards_per_pound, 1)

    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE projects SET
                date_completed       = COALESCE(?, date_completed),
                actual_weight_grams  = COALESCE(?, actual_weight_grams),
                actual_yards_used    = COALESCE(?, actual_yards_used),
                actual_length_inches = COALESCE(?, actual_length_inches),
                actual_width_inches  = COALESCE(?, actual_width_inches),
                disposition          = COALESCE(?, disposition),
                completion_notes     = COALESCE(?, completion_notes),
                photo                = COALESCE(?, photo)
               WHERE id = ?""",
            (
                date_completed, actual_weight_grams, actual_yards_used,
                actual_length_inches, actual_width_inches,
                disposition, completion_notes, photo,
                project_id,
            )
        )
    conn.close()
    return get_project_by_id(project_id, db_path)


def get_project_by_id(project_id: int, db_path: str = "warp_calc.db") -> Optional[Project]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    return _row_to_project(row) if row else None


def get_all_projects(db_path: str = "warp_calc.db") -> list[Project]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM projects ORDER BY date_planned DESC"
    ).fetchall()
    conn.close()
    return [_row_to_project(r) for r in rows]


def get_planned_projects(db_path: str = "warp_calc.db") -> list[Project]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM projects WHERE date_completed IS NULL ORDER BY date_planned DESC"
    ).fetchall()
    conn.close()
    return [_row_to_project(r) for r in rows]


def get_completed_projects(db_path: str = "warp_calc.db") -> list[Project]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM projects WHERE date_completed IS NOT NULL ORDER BY date_completed DESC"
    ).fetchall()
    conn.close()
    return [_row_to_project(r) for r in rows]


def delete_project(project_id: int, db_path: str = "warp_calc.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
    conn.close()


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        id                      = row["id"],
        project_name            = row["project_name"],
        date_planned            = row["date_planned"],
        loom_name               = row["loom_name"],
        yarn_name               = row["yarn_name"],
        yarn_yards_per_pound    = row["yarn_yards_per_pound"],
        structure_name          = row["structure_name"],
        sett                    = row["sett"],
        ppi                     = row["ppi"],
        take_up_pct             = row["take_up_pct"],
        gap_allowance           = row["gap_allowance"],
        total_ends              = row["total_ends"],
        warp_length_inches      = row["warp_length_inches"],
        warp_length_yards       = row["warp_length_yards"],
        planned_warp_yards      = row["planned_warp_yards"],
        planned_warp_weight_oz  = row["planned_warp_weight_oz"],
        planned_weft_yards      = row["planned_weft_yards"],
        planned_weft_weight_oz  = row["planned_weft_weight_oz"],
        planned_total_yards     = row["planned_total_yards"],
        planned_total_weight_oz = row["planned_total_weight_oz"],
        piece_details_json      = row["piece_details_json"],
        weft_summary_json       = row["weft_summary_json"],
        date_completed          = row["date_completed"],
        actual_weight_grams     = row["actual_weight_grams"],
        actual_yards_used       = row["actual_yards_used"],
        actual_length_inches    = row["actual_length_inches"],
        actual_width_inches     = row["actual_width_inches"],
        disposition             = row["disposition"],
        completion_notes        = row["completion_notes"],
        photo                   = row["photo"],
    )
