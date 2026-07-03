"""
Database layer for the warp calculator.

Handles:
  - Creating the schema on first run
  - Seeding default reference data
  - CRUD for looms, yarns, and weave structures

All functions accept and return typed dataclass instances (from models.py).
The DB file is created at the path you pass to init_db() — defaults to
'warp_calc.db' in the current directory.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from models import Loom, Yarn, WeaveStructure
from seed_data import DEFAULT_LOOMS, DEFAULT_YARNS, DEFAULT_STRUCTURES


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS looms (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    max_weaving_width   REAL    NOT NULL,
    loom_waste          REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS yarns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    size_notation   TEXT    NOT NULL,
    fiber           TEXT    NOT NULL,
    wraps_per_inch  INTEGER NOT NULL,
    yards_per_pound INTEGER NOT NULL,
    brand           TEXT,
    yarn_line       TEXT,
    yarn_notes      TEXT
);

CREATE TABLE IF NOT EXISTS weave_structures (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT    NOT NULL UNIQUE,
    sett_multiplier     REAL    NOT NULL,
    min_shafts          INTEGER NOT NULL,
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

def init_db(db_path: str = "warp_calc.db") -> str:
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
    for loom in DEFAULT_LOOMS:
        _insert_loom(conn, loom)
    for yarn in DEFAULT_YARNS:
        _insert_yarn(conn, yarn)
    for structure in DEFAULT_STRUCTURES:
        _insert_structure(conn, structure)


# ---------------------------------------------------------------------------
# Looms
# ---------------------------------------------------------------------------

def _insert_loom(conn: sqlite3.Connection, loom: Loom) -> int:
    cur = conn.execute(
        "INSERT INTO looms (name, max_weaving_width, loom_waste) VALUES (?,?,?)",
        (loom.name, loom.max_weaving_width, loom.loom_waste)
    )
    return cur.lastrowid


def add_loom(loom: Loom, db_path: str = "warp_calc.db") -> Loom:
    """Insert a new loom; returns the loom with its new DB id."""
    conn = _connect(db_path)
    with conn:
        loom.id = _insert_loom(conn, loom)
    conn.close()
    return loom


def update_loom(loom: Loom, db_path: str = "warp_calc.db") -> None:
    """Update an existing loom by id."""
    if loom.id is None:
        raise ValueError("Cannot update a loom without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE looms
               SET name=?, max_weaving_width=?, loom_waste=?
               WHERE id=?""",
            (loom.name, loom.max_weaving_width, loom.loom_waste, loom.id)
        )
    conn.close()


def delete_loom(loom_id: int, db_path: str = "warp_calc.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute("DELETE FROM looms WHERE id=?", (loom_id,))
    conn.close()


def get_all_looms(db_path: str = "warp_calc.db") -> list[Loom]:
    conn = _connect(db_path)
    rows = conn.execute("SELECT * FROM looms ORDER BY name").fetchall()
    conn.close()
    return [Loom(
        id=r["id"],
        name=r["name"],
        max_weaving_width=r["max_weaving_width"],
        loom_waste=r["loom_waste"]
    ) for r in rows]


def get_loom_by_id(loom_id: int, db_path: str = "warp_calc.db") -> Optional[Loom]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM looms WHERE id=?", (loom_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    return Loom(id=row["id"], name=row["name"],
                max_weaving_width=row["max_weaving_width"],
                loom_waste=row["loom_waste"])


# ---------------------------------------------------------------------------
# Yarns
# ---------------------------------------------------------------------------

def _insert_yarn(conn: sqlite3.Connection, yarn: Yarn) -> int:
    cur = conn.execute(
        """INSERT INTO yarns
           (size_notation, fiber, wraps_per_inch, yards_per_pound, brand, yarn_line, yarn_notes)
           VALUES (?,?,?,?,?,?,?)""",
        (yarn.size_notation, yarn.fiber, yarn.wraps_per_inch,
         yarn.yards_per_pound, yarn.brand, yarn.yarn_line, yarn.yarn_notes)
    )
    return cur.lastrowid


def add_yarn(yarn: Yarn, db_path: str = "warp_calc.db") -> Yarn:
    conn = _connect(db_path)
    with conn:
        yarn.id = _insert_yarn(conn, yarn)
    conn.close()
    return yarn


def update_yarn(yarn: Yarn, db_path: str = "warp_calc.db") -> None:
    if yarn.id is None:
        raise ValueError("Cannot update a yarn without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE yarns
               SET size_notation=?, fiber=?, wraps_per_inch=?,
                   yards_per_pound=?, brand=?, yarn_line=?, yarn_notes=?
               WHERE id=?""",
            (yarn.size_notation, yarn.fiber, yarn.wraps_per_inch,
             yarn.yards_per_pound, yarn.brand, yarn.yarn_line, yarn.yarn_notes, yarn.id)
        )
    conn.close()


def delete_yarn(yarn_id: int, db_path: str = "warp_calc.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute("DELETE FROM yarns WHERE id=?", (yarn_id,))
    conn.close()


def get_all_yarns(db_path: str = "warp_calc.db") -> list[Yarn]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM yarns ORDER BY fiber, size_notation, brand"
    ).fetchall()
    conn.close()
    return [_row_to_yarn(r) for r in rows]


def get_yarns_by_fiber(fiber: str, db_path: str = "warp_calc.db") -> list[Yarn]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM yarns WHERE LOWER(fiber)=LOWER(?) ORDER BY size_notation",
        (fiber,)
    ).fetchall()
    conn.close()
    return [_row_to_yarn(r) for r in rows]


def get_yarn_by_id(yarn_id: int, db_path: str = "warp_calc.db") -> Optional[Yarn]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM yarns WHERE id=?", (yarn_id,)).fetchone()
    conn.close()
    return _row_to_yarn(row) if row else None


def _row_to_yarn(row: sqlite3.Row) -> Yarn:
    return Yarn(
        id=row["id"],
        size_notation=row["size_notation"],
        fiber=row["fiber"],
        wraps_per_inch=row["wraps_per_inch"],
        yards_per_pound=row["yards_per_pound"],
        brand=row["brand"],
        yarn_line=row["yarn_line"],
        yarn_notes=row["yarn_notes"]
    )


# ---------------------------------------------------------------------------
# Weave structures
# ---------------------------------------------------------------------------

def _insert_structure(conn: sqlite3.Connection, s: WeaveStructure) -> int:
    cur = conn.execute(
        """INSERT INTO weave_structures
           (name, sett_multiplier, min_shafts, notes)
           VALUES (?,?,?,?)""",
        (s.name, s.sett_multiplier, s.min_shafts, s.notes)
    )
    return cur.lastrowid


def add_structure(s: WeaveStructure, db_path: str = "warp_calc.db") -> WeaveStructure:
    conn = _connect(db_path)
    with conn:
        s.id = _insert_structure(conn, s)
    conn.close()
    return s


def update_structure(s: WeaveStructure, db_path: str = "warp_calc.db") -> None:
    if s.id is None:
        raise ValueError("Cannot update a structure without an id.")
    conn = _connect(db_path)
    with conn:
        conn.execute(
            """UPDATE weave_structures
               SET name=?, sett_multiplier=?, min_shafts=?, notes=?
               WHERE id=?""",
            (s.name, s.sett_multiplier, s.min_shafts, s.notes, s.id)
        )
    conn.close()


def delete_structure(structure_id: int, db_path: str = "warp_calc.db") -> None:
    conn = _connect(db_path)
    with conn:
        conn.execute("DELETE FROM weave_structures WHERE id=?", (structure_id,))
    conn.close()


def get_all_structures(db_path: str = "warp_calc.db") -> list[WeaveStructure]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT * FROM weave_structures ORDER BY min_shafts, name"
    ).fetchall()
    conn.close()
    return [_row_to_structure(r) for r in rows]


def get_structure_by_id(structure_id: int, db_path: str = "warp_calc.db") -> Optional[WeaveStructure]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM weave_structures WHERE id=?", (structure_id,)).fetchone()
    conn.close()
    return _row_to_structure(row) if row else None


def get_structure_by_id(sid: int, db_path: str = "warp_calc.db") -> Optional[WeaveStructure]:
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM weave_structures WHERE id=?", (sid,)).fetchone()
    conn.close()
    return _row_to_structure(row) if row else None


def _row_to_structure(row: sqlite3.Row) -> WeaveStructure:
    return WeaveStructure(
        id=row["id"],
        name=row["name"],
        sett_multiplier=row["sett_multiplier"],
        min_shafts=row["min_shafts"],
        notes=row["notes"]
    )
