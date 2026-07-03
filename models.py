"""
Data models for the warp calculator reference layer.
Data models for craft project tracker
All reference data lives here as dataclasses for both warp calculator and project tracker
"""

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Loom
# ---------------------------------------------------------------------------

@dataclass
class Loom:
    name: str                        # e.g. "Schacht Baby Wolf 26\""
    max_weaving_width: float         # inches
    loom_waste: float                # inches (front + back combined)
    id: Optional[int] = None         # set by DB on insert

    def __str__(self):
        return (
            f"{self.name}  |  max width: {self.max_weaving_width}\"  "
            f"|  loom waste: {self.loom_waste}\""
        )


# ---------------------------------------------------------------------------
# Yarn
# ---------------------------------------------------------------------------

@dataclass
class Yarn:
    """
    Identifies a yarn by its technical size AND optionally by brand/product.

    size_notation : industry shorthand, e.g. "8/2", "10/2", "5/2", "3/2"
    fiber         : fiber type, e.g. "cotton", "wool", "linen", "tencel"
    wraps_per_inch: how many wraps fit in one inch (used for sett estimation)
    yards_per_pound: total yardage per pound (used for yardage/weight calc)
    brand         : (optional) brand name, e.g. "Valley Yarns", "Maurice Brassard"
    yarn_line     : (optional) product line, e.g. "8/2 Unmercerized Cotton"
    """
    size_notation: str
    fiber: str
    wraps_per_inch: int
    yards_per_pound: int
    brand: Optional[str] = None
    yarn_line: Optional[str] = None
    id: Optional[int] = None
    yarn_notes: Optional[str] = None

    @property
    def display_name(self) -> str:
        base = f"{self.size_notation} {self.fiber.title()}"
        if self.brand and self.yarn_line:
            return f"{base} — {self.brand} {self.yarn_line}"
        if self.brand:
            return f"{base} — {self.brand}"
        return base

    def __str__(self):
        return (
            f"{self.display_name}  |  "
            f"{self.wraps_per_inch} WPI  |  "
            f"{self.yards_per_pound} yd/lb"
        )


# ---------------------------------------------------------------------------
# Weave structure
# ---------------------------------------------------------------------------

@dataclass
class WeaveStructure:
    """
    name            : e.g. "Plain Weave", "2/2 Twill", "Basket Weave"
    sett_multiplier : fraction applied to WPI to get recommended sett
                      Plain weave = 0.5  (half of WPI)
                      Twill       = 0.6  (slightly more open)
                      Basket weave = 0.33 (very open)
    min_shafts      : minimum shafts required
    notes           : optional reminder, e.g. "double the sett for warp-faced"
    """
    name: str
    sett_multiplier: float
    min_shafts: int
    notes: Optional[str] = None
    id: Optional[int] = None

    @property
    def recommended_sett(self, wpi: int = 0) -> str:
        if wpi:
            return f"{round(wpi * self.sett_multiplier)} epi"
        return f"WPI × {self.sett_multiplier}"

    def __str__(self):
        note = f"  [{self.notes}]" if self.notes else ""
        return (
            f"{self.name}  |  sett = WPI × {self.sett_multiplier}  "
            f"|  min {self.min_shafts} shaft(s){note}"
        )

# ---------------------------------------------------------------------------
# Knit/Crochet Yarn structure
# ---------------------------------------------------------------------------

@dataclass
class StashYarn:
    """
    Identifies a yarn by its technical size AND optionally by brand/product.

    size_notation : industry shorthand, "lace", "fingering", "dk", etc
    fiber         : single word fiber type, ("cotton", "wool", "linen", "tencel")
    wraps_per_inch: how many wraps fit in one inch (used for size estimation)
    yards_per_100g: total yardage per 100g (used for yardage/weight calc)
    yarn_weight_grams: yarn weight in grams
    brand         : (optional) brand name, ("Republica Unicornia" "Yarnaceous")
    yarn_content  : if fiber content is anything particularly detailed ("80% bfl, 20% tencel")
    handspun      : boolean is or is not handspun (implication spun by me)
    hand_dyed     : boolean is/is not hand-dyed by me, does not include other indie dyers
    id            : database id automatically assigned
    yarn_notes    : (optional) notes
    """
    size_notation: str
    fiber: str
    yards_per_100g: float
    wraps_per_inch: Optional[int] = None 
    brand: Optional[str] = None
    yarn_content: Optional[str] = None
    handspun: bool = False
    hand_dyed: bool = False
    id: Optional[int] = None
    yarn_notes: Optional[str] = None


# ProjectYarn connects KnitProject and StashYarn when a yarn is assigned to a project 

@dataclass
class ProjectYarn:
    """
    starting_weight   : weight in grams of yarn at start of project
    ending_weight     : Weight in grams of yarn at end of project
    stash_id          : id of StashYarn entry
    project_id        : id of KnitProject entry
    color_role        : "MC" "CC" or other descriptor in colorwork project 
    """

    starting_weight: float
    ending_weight: Optional[float] = None
    id: Optional[int] = None
    stash_id: Optional[int] = None
    project_id: Optional[int] = None
    color_role: Optional[str] = None

    @property
    def grams_used(self) -> Optional[float]:
        if self.ending_weight is not None and self.ending_weight is not None:
            return self.starting_weight - self.ending_weight
        return None


@dataclass
class KnitProject:
    """
    gives information on project

    project_name    : self-named project title
    pattern_name    : name from ravelry or other source
    pattern_source  : ravelry, book, etc
    gauge           : (optional) stitches x rows
    made_for        : gift, self, person etc
    project_notes   : (optional) notes
    date_started    : yyyy-mm-dd
    date_completed  : yyyy-mm-dd
    """
    
    project_name: str
    pattern_name: str
    pattern_source: str
    gauge: Optional[str] = None 
    made_for: Optional[str] = None
    id: Optional[int] = None
    project_notes: Optional[str] = None
    date_started: Optional[str] = None
    date_completed: Optional[str] = None

@dataclass
class SpinProject:
    """
    Information on Spinning Projects
    project_name      : self-named project title
    weight_grams      : weight in grams when complete
    fiber_content     : if known, estimates if self-blended
    plies             : number of plies in yarn
    measured_yards    : measured from niddy-noddy or yardage counter
    twist             : recorded in degrees of twist
    date_started      : yyyy-mm-dd
    date_completed    : yyyy-mm-dd
    project_notes     : Any relevant information
    id                : assigned automatically
    stash_id          : id assigned within stash
    tool_id           : Tool used to create yarn
    fiber_prep_id     : Fiber preparation used to create yarn
    spin_style_id     : Spinning style used to create yarn 
    """

    project_name: str
    weight_grams: float
    fiber_content: Optional[str] = None
    plies: Optional[int] = None
    measured_yards: Optional[int] = None
    twist: Optional[int] = None #recorded in degrees of twist
    date_started: Optional[str] = None
    date_completed: Optional[str] = None
    project_notes: Optional[str] = None
    id: Optional[int]  = None
    stash_id: Optional[int] = None
    tool_id: Optional[int] = None
    fiber_prep_id: Optional[int] = None
    spin_style_id: Optional[int] = None

@dataclass
class SpinningTool:
    """
    Pre-saved spinning tools
    name        : Name of tool (Lendrum, Ladybug, Narwhal Spindle, etc)
    tool_type   : "wheel" "spindle" or even more specific "castle wheel" etc
    notes       : anything relevant about tool
    id          : assigned
    """    
    name: str                   
    tool_type: str               # "wheel" or "spindle"
    notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class FiberPrep:
    """
    Fiber prep describes how the fiber was prepared for spinning
    name     : combed top, batt, rolag, etc
    notes    : anything relevant about prep
    id       : assigned
    """
    name: str                    # "combed top", "batt", "rolag"
    notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class SpinStyle:
    """
    Spin style describes how the yarn was spun, which hand techniques were used
    name     : long draw, short forward draw, corespun, etc
    notes    : anythign relevant about technique
    id       : assigned
    """
    name: str                    # "long draw", "short forward draw"
    notes: Optional[str] = None
    id: Optional[int] = None
    
