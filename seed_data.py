"""
Default reference data seeded into the database on first run.

Looms           : all looms currently owned
Yarns           : common weaving yarns with accurate WPI and yards/pound
Structures      : basic structures with standard sett multipliers
SpinningTool    : spinning tools currently owned and used regularly
FiberPrep       : Fiber preparations commonly used
SpinStyle       : spinning styles commonly used

Sources for yarn specs:
  - Ashford/Brassard published yardage tables
  - Handweaver's Pattern Directory (Ann Dixon)
  - Interweave "Yarn Substitution Guide"
"""

from models import Loom, Yarn, WeaveStructure, SpinningTool, FiberPrep, SpinStyle


# ---------------------------------------------------------------------------
# DEFAULT LOOMS
# ---------------------------------------------------------------------------
#    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
#    name                TEXT    NOT NULL UNIQUE,
#    max_weaving_width   REAL    NOT NULL,
#    loom_waste          REAL    NOT NULL

DEFAULT_LOOMS: list[Loom] = [
    Loom("Schacht Standard", max_weaving_width=30, loom_waste=30),
    Loom("Rigid Heddle", max_weaving_width=24, loom_waste=18),
]


# ---------------------------------------------------------------------------
# DEFAULT YARNS
# Organized by fiber, then weight (coarsest → finest)
# WPI values are mid-range; individual skeins vary slightly.
# ---------------------------------------------------------------------------

DEFAULT_YARNS: list[Yarn] = [

    # --- Cotton ---
    Yarn("3/2",  "cotton", wraps_per_inch=18, yards_per_pound=1260,
         brand="Valley Yarns", yarn_line="3/2 Perle Cotton"),
    Yarn("5/2",  "cotton", wraps_per_inch=24, yards_per_pound=2100,
         brand="Valley Yarns", yarn_line="5/2 Perle Cotton"),
    Yarn("8/2",  "cotton", wraps_per_inch=32, yards_per_pound=3360,
         brand="Maurice Brassard", yarn_line="8/2 Unmercerized Cotton"),
    Yarn("8/2",  "cotton", wraps_per_inch=32, yards_per_pound=3600,
         brand="Valley Yarns", yarn_line="8/2 Mercerized Cotton"),
    Yarn("10/2", "cotton", wraps_per_inch=40, yards_per_pound=4200,
         brand="Maurice Brassard", yarn_line="10/2 Cotton"),
    Yarn("20/2", "cotton", wraps_per_inch=60, yards_per_pound=8400,
         brand="Maurice Brassard", yarn_line="20/2 Cotton"),

    # --- Wool ---
    Yarn("2/8",  "wool",   wraps_per_inch=32, yards_per_pound=1600,
         brand="Jaggerspun", yarn_line="Heather 2/8"),
    Yarn("2/16", "wool",   wraps_per_inch=48, yards_per_pound=3200,
         brand="Jaggerspun", yarn_line="Zephyr Wool-Silk"),
    Yarn("5/2",  "wool",   wraps_per_inch=22, yards_per_pound=1750),
    Yarn("8/2",  "wool",   wraps_per_inch=32, yards_per_pound=3200),

    # --- Linen ---
    Yarn("10/1", "linen",  wraps_per_inch=40, yards_per_pound=3000,
         brand="Bockens", yarn_line="10/1 Linen"),
    Yarn("16/1", "linen",  wraps_per_inch=55, yards_per_pound=4800,
         brand="Bockens", yarn_line="16/1 Linen"),

    # --- Tencel / Lyocell ---
    Yarn("8/2",  "tencel", wraps_per_inch=32, yards_per_pound=3360,
         brand="Yarn Barn", yarn_line="8/2 Tencel"),
    Yarn("10/2", "tencel", wraps_per_inch=40, yards_per_pound=4200),

    # --- Silk ---
    Yarn("20/2", "silk",   wraps_per_inch=60, yards_per_pound=8400,
         brand="Treenway Silks", yarn_line="20/2 Bombyx Silk"),

    # --- Generic / unlabeled (useful placeholders) ---
    Yarn("worsted", "wool",  wraps_per_inch=18, yards_per_pound=900),
    Yarn("DK",      "wool",  wraps_per_inch=22, yards_per_pound=1100),
    Yarn("sport",   "wool",  wraps_per_inch=26, yards_per_pound=1400),
    Yarn("fingering","wool", wraps_per_inch=36, yards_per_pound=1800),
]


# ---------------------------------------------------------------------------
# DEFAULT WEAVE STRUCTURES
# sett_multiplier: fraction of WPI used as recommended EPI
# Rule of thumb:
#   plain weave  = WPI / 2    (multiplier 0.50)
#   2/2 twill    = WPI × 0.60
#   3/1 twill    = WPI × 0.60
#   basket weave = WPI / 3    (multiplier 0.33)
#   rep weave    = WPI × 0.75 (warp-faced, so more ends)
#   huck lace    = WPI × 0.45 (more open)
#   waffle weave = WPI × 0.60
# ---------------------------------------------------------------------------

DEFAULT_STRUCTURES: list[WeaveStructure] = [
    WeaveStructure(
        name="Plain weave",
        sett_multiplier=0.50,
        min_shafts=2,
        notes="Most versatile; sett = half of WPI"
    ),
    WeaveStructure(
        name="Basket weave",
        sett_multiplier=0.33,
        min_shafts=2,
        notes="Very open; typically 2×2 or 4×4 interlacement"
    ),
    WeaveStructure(
        name="2/2 twill",
        sett_multiplier=0.60,
        min_shafts=4,
        notes="Classic diagonal; balanced over/under"
    ),
    WeaveStructure(
        name="3/1 twill",
        sett_multiplier=0.60,
        min_shafts=4,
        notes="Weft-dominant diagonal; denim-style"
    ),
    WeaveStructure(
        name="1/3 twill",
        sett_multiplier=0.60,
        min_shafts=4,
        notes="Warp-dominant diagonal"
    ),
    WeaveStructure(
        name="Huck lace",
        sett_multiplier=0.45,
        min_shafts=4,
        notes="Open lace structure; sett slightly looser than plain"
    ),
    WeaveStructure(
        name="Waffle weave",
        sett_multiplier=0.60,
        min_shafts=4,
        notes="Textured 3D weave; good for towels and washcloths"
    ),
    WeaveStructure(
        name="Rep weave",
        sett_multiplier=0.75,
        min_shafts=4,
        notes="Warp-faced; pack ends in tightly"
    ),
    WeaveStructure(
        name="Overshot",
        sett_multiplier=0.50,
        min_shafts=4,
        notes="Pattern weft floats on plain-weave ground; sett like plain weave"
    ),
    WeaveStructure(
        name="Honeycomb",
        sett_multiplier=0.50,
        min_shafts=4,
        notes="Cell-like texture; same sett as plain weave"
    ),
    WeaveStructure(
        name="Rigid heddle plain weave",
        sett_multiplier=0.50,
        min_shafts=1,
        notes="For rigid heddle looms; sett determined by heddle size"
    ),
]



#    spinning tools list
#   
#    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
#    name                TEXT NOT NULL,                   
#    tool_type           TEXT NOT NULL,
#    notes               TEXT


DEFAULT_SPINNINGTOOLS: list[SpinningTool] = [
    SpinningTool("Narwhal Turkish", "Spindle", "went to space on TSC's Spaceship"),
    SpinningTool("EEW 6", "Electric Wheel", "8oz bobbin"),
    SpinningTool("EEW Nano", "Electric Wheel", "2oz bobbin"),
    SpinningTool("Schacht Ladybug", "Castle Wheel"),
    SpinningTool("Lendrum","Castle Wheel", "cranky wheel bearing"),
]    

# fiber prep list
#
#   id                  INTEGER PRIMARY KEY AUTOINCREMENT,
#   name                TEXT NOT NULL,                   
#   notes               TEXT

DEFAULT_FIBERPREP: list[FiberPrep] = [
    FiberPrep("rolag"),
    FiberPrep("combed top"),
    FiberPrep("batt"),    
]

# spinning style list
#
#   id                  INTEGER PRIMARY KEY AUTOINCREMENT,
#   name                TEXT NOT NULL,                   
#   notes               TEXT

DEFAULT_SPINSTYLE: list[SpinStyle] = [
    SpinStyle("short draw"),    
    SpinStyle("long draw"),
    SpinStyle("corespun"),
    SpinStyle("art yarn"),
]
