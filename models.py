"""
Data models for the warp calculator reference layer.
All reference data (looms, yarns, weave structures) lives here as dataclasses.
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
    fiber         : fiber type, e.g. "cotton", "wool", "linen", "tencel"
    wraps_per_inch: how many wraps fit in one inch (used for size estimation)
    yards_per_100g: total yardage per 100g (used for yardage/weight calc)
    yarn_weight_grams: yarn weight in grams
    brand         : (optional) brand name, e.g. "Republica Unicornia" "Yarnaceous" etc
    id            : database id automatically assigned?
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


# Bridge class to connect KnitProject and StashYarn. 

@dataclass
class ProjectYarn:
    """
    starting_weight: weight in grams of yarn at start of project
    ending_weight: Weight in grams of yarn at end of project
    grams_used: calculated field difference between ending and starting weight
    stash_id: id of StashYarn entry
    project_id: id of KnitProject entry
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

    project_name  : self-named project title
    pattern_name  : name from ravelry or other source
    pattern_source: ravelry, book, etc
    gauge         : (optional) stitches x rows
    made_for      : gift, self, etc
    project_notes : (optional) notes
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
    name: str                   
    tool_type: str               # "wheel" or "spindle"
    notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class FiberPrep:
    name: str                    # "combed top", "batt", "rolag"
    notes: Optional[str] = None
    id: Optional[int] = None

@dataclass
class SpinStyle:
    name: str                    # "long draw", "short forward draw"
    notes: Optional[str] = None
    id: Optional[int] = None
    