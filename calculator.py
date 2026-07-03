# Note only a few warp structures are loaded, will add more as I learn. 
#

"""
calculator.py — warp and weft planning math

Takes a loom, yarn, weave structure, and project dimensions and returns
a full WarpPlan with all derived values filled in.

Key concepts:
  - finished_length   : the length of the piece AFTER washing/finishing
  - hem_allowance     : extra length woven on each end, folds under (inches)
  - fringe            : optional; extra warp length left unwoven (inches per end)
  - gap_allowance     : space left between pieces on a shared warp (default 1")
  - take_up_pct       : combined take-up + shrinkage as a decimal (percentage)
  - loom_waste        : pulled from the loom (front + back beam waste)

Warp length per piece formula:
    woven_length  = (finished_length / (1 - take_up_pct)) + (hem_allowance * 2)
    piece_length  = woven_length + fringe_per_end + gap_allowance

Total warp length:
    warp_length   = (piece_length * num_pieces) + loom_waste

Total ends:
    ends          = round(weaving_width * sett)
    sett          = round(yarn.wraps_per_inch * structure.sett_multiplier)

Total warp yardage:
    total_yards   = (ends * warp_length_inches) / 36

Weft yardage per piece:
    For each weft yarn on a piece:
        weft_yards = ((warp_width_inches / 36) * woven_length_inches * ppi)
                     * (1 + take_up_pct)   <- accounts for draw-in

    For single-weft structures: one yarn at full PPI
    For two-weft structures (overshot): each yarn at PPI / 2

Weight in ounces:
    weight_oz = (total_yards / yarn.yards_per_pound) * 16
"""

from dataclasses import dataclass, field
from typing import Optional
from models import Loom, Yarn, WeaveStructure


# ------------------------------------------------------------------
# Weft yarn definition
# -----------------------------------------------------------------------

@dataclass
class WeftYarn:
    """
    Describes one weft yarn used in a piece.

    yarn            : Yarn object from the reference table
    role            : "tabby", "pattern", or "single"
                      "single"  — only weft (plain weave, twill, etc.)
                      "tabby"   — ground weft in a two-weft structure
                      "pattern" — pattern weft in overshot/turned twill
    ppi_override    : if set, overrides the calculated PPI for this yarn.
                      Useful after sampling.
    """
    yarn: Yarn
    role: str = "single"          # "single" | "tabby" | "pattern"
    ppi_override: Optional[int] = None

    def __post_init__(self):
        valid_roles = {"single", "tabby", "pattern"}
        if self.role not in valid_roles:
            raise ValueError(
                f"Invalid weft role '{self.role}'. "
                f"Must be one of: {', '.join(valid_roles)}"
            )


# ---------------------------------------------------------------------------
# Input: one piece on the warp (one tea towel, one mug rug, etc)
# ---------------------------------------------------------------------

@dataclass
class WarpPiece:
    """
    Describes a single project piece on the warp.

    finished_length : desired finished length in inches (AFTER take-up/shrinkage)
    finished_width  : desired finished width in inches (AFTER take-up/shrinkage)
    hem_allowance   : extra inches woven at each end for a hem (applied x 2)
    fringe          : inches of unwoven warp left as fringe at each end (optional)
    weft_yarns      : list of WeftYarn objects (one for plain weave/twill,
                      two for overshot/turned twill)
    label           : optional name, e.g. "Towel 1", "Scarf"
    """
    finished_length: float
    finished_width: float
    weft_yarns: list[WeftYarn]
    hem_allowance: float = 0.0
    fringe: float = 0.0
    label: str = "Piece"

    def __post_init__(self):
        if self.hem_allowance > 0 and self.fringe > 0:
            raise ValueError(
                f"'{self.label}' has both hem_allowance and fringe set. "
                "Use one or the other, not both."
            )
        if not self.weft_yarns:
            raise ValueError(f"'{self.label}' must have at least one weft yarn.")

        roles = [w.role for w in self.weft_yarns]

        # Single-weft pieces should use role="single"
        if len(self.weft_yarns) == 1 and roles[0] != "single":
            raise ValueError(
                f"'{self.label}' has one weft yarn but role is '{roles[0]}'. "
                "Use role='single' for single-weft structures."
            )

        # Two-weft pieces must have one tabby and one pattern
        if len(self.weft_yarns) == 2:
            if set(roles) != {"tabby", "pattern"}:
                raise ValueError(
                    f"'{self.label}' has two weft yarns but roles are {roles}. "
                    "Two-weft pieces must have one 'tabby' and one 'pattern'."
                )

        if len(self.weft_yarns) > 2:
            raise ValueError(
                f"'{self.label}' has {len(self.weft_yarns)} weft yarns. "
                "Maximum supported is 2 (tabby + pattern)."
            )


# ------------------------------------------------------------------------
# Input: full warp plan parameters
# --------------------------------------------------------------------

@dataclass
class WarpParameters:
    """
    Everything needed to calculate a warp.

    loom            : Loom object (supplies loom_waste)
    yarn            : Yarn object (supplies wraps_per_inch, yards_per_pound)
    structure       : WeaveStructure object (supplies sett_multiplier)
    pieces          : list of WarpPiece objects (one or more)
    take_up_pct     : combined take-up + shrinkage as a decimal (default 15%)
    gap_allowance   : gap between pieces in inches (default 1.0")
    sett_override   : if set, overrides the calculated sett (ends per inch)
    ppi_override    : if set, overrides the calculated PPI for all pieces
                      (individual WeftYarn ppi_override takes precedence)
    """
    loom: Loom
    yarn: Yarn
    structure: WeaveStructure
    pieces: list[WarpPiece]
    take_up_pct: float = 0.15
    gap_allowance: float = 1.0
    sett_override: Optional[int] = None
    ppi_override: Optional[int] = None


# ---------------------------------------------------------------------------
# Output: fully calculated warp plan
# -------------------------------------------------------------------------

@dataclass
class WarpPlan:
    """
    All derived values from a set of WarpParameters.
    All lengths in inches unless noted.
    """
    # --- inputs echoed back for reference ---
    loom_name: str
    yarn_name: str
    yarn_yards_per_pound: int
    structure_name: str
    take_up_pct: float
    gap_allowance: float

    # --- sett ---
    sett: int
    ppi: int
    sett_was_overridden: bool
    ppi_was_overridden: bool

    # --- per-piece breakdown ---
    piece_details: list[dict]

    # --- warp totals ---
    total_ends: int
    warp_length_inches: float
    warp_length_yards: float

    # --- warp yardage and weight ---
    warp_yards: float
    warp_weight_oz: float

    # --- weft totals ---
    weft_summary: list[dict]      # one entry per unique yarn used as weft
    total_weft_yards: float
    total_weft_weight_oz: float

    # --- combined ---
    total_yards: float            # warp + all weft
    total_weight_oz: float
    total_weight_lbs: float

    # --- warnings ---
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "",
            "=" * 62,
            "  WARP PLAN SUMMARY",
            "=" * 62,
            f"  Loom       : {self.loom_name}",
            f"  Warp yarn  : {self.yarn_name}",
            f"  Structure  : {self.structure_name}",
            f"  Sett       : {self.sett} EPI"
            + (" (overridden)" if self.sett_was_overridden else " (calculated)"),
            f"  PPI        : {self.ppi}"
            + (" (overridden)" if self.ppi_was_overridden else " (= EPI, balanced)"),
            f"  Take-up    : {self.take_up_pct * 100:.0f}%",
            "-" * 62,
            "  PIECES",
        ]
        for p in self.piece_details:
            lines.append(f"  {p['label']}")
            lines.append(f"    Finished size  : {p['finished_width']}\" x {p['finished_length']}\"")
            if p['hem_allowance'] > 0:
                lines.append(f"    Hem allowance  : {p['hem_allowance']}\" each end ({p['hem_allowance']*2}\" total)")
            if p['fringe'] > 0:
                lines.append(f"    Fringe         : {p['fringe']}\" each end")
            lines.append(f"    Warp length    : {p['piece_warp_length']:.2f}\" (incl. gap)")
            for weft in p['weft_breakdown']:
                lines.append(
                    f"    Weft ({weft['role']:<8}): {weft['yarn_name']}  "
                    f"{weft['ppi']} PPI  —  {weft['yards']:.1f} yards"
                )
        lines += [
            "-" * 62,
            "  WARP",
            f"  Total ends        : {self.total_ends}",
            f"  Warp length       : {self.warp_length_inches:.1f}\" "
            f"({self.warp_length_yards:.2f} yd per end)",
            f"  Warp yardage      : {self.warp_yards:.1f} yards",
            f"  Warp weight       : {self.warp_weight_oz:.1f} oz",
            "-" * 62,
            "  WEFT",
        ]
        for w in self.weft_summary:
            lines.append(
                f"  {w['yarn_name']:<35} "
                f"{w['total_yards']:>7.1f} yards total  "
                f"({w['yards_per_piece']:.1f} yd/piece)"
            )
        lines += [
            f"  Total weft        : {self.total_weft_yards:.1f} yards",
            f"  Weft weight       : {self.total_weft_weight_oz:.1f} oz",
            "-" * 62,
            "  COMBINED TOTALS",
            f"  Total yardage     : {self.total_yards:.1f} yards",
            f"  Total weight      : {self.total_weight_oz:.1f} oz  "
            f"({self.total_weight_lbs:.2f} lbs)",
        ]
        if self.warnings:
            lines += [
                "-" * 62,
                "  ⚠  WARNINGS",
            ]
            for w in self.warnings:
                lines.append(f"  • {w}")
        lines.append("=" * 62)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core calculation functions
# ---------------------------------------------------------------------------

def _calc_piece(
    piece: WarpPiece,
    sett: int,
    ppi: int,
    warp_width: float,
    take_up_pct: float,
    gap_allowance: float,
) -> dict:
    """
    Calculate warp length and weft yardage for a single piece.

    warp_width  : the on-loom weaving width (already adjusted for draw-in)
    ppi         : total picks per inch across all weft yarns
    """
    # --- warp contribution ---
    woven_length = (piece.finished_length / (1 - take_up_pct)) + (piece.hem_allowance * 2)
    fringe_total = piece.fringe * 2
    piece_warp_length = woven_length + fringe_total + gap_allowance

    # --- weft contribution ---
    # weft draw-in: weft yarn travels over/under ends so uses slightly more
    # than the weaving width — use take_up_pct as the draw-in factor
    weft_width_yards = (warp_width * (1 + take_up_pct)) / 36

    weft_breakdown = []
    for weft in piece.weft_yarns:
        # determine this yarn's PPI
        if weft.ppi_override is not None:
            yarn_ppi = weft.ppi_override
        elif len(piece.weft_yarns) == 2:
            # two-weft structure: split PPI evenly between tabby and pattern
            yarn_ppi = ppi // 2
        else:
            yarn_ppi = ppi

        weft_yards = weft_width_yards * woven_length * yarn_ppi

        weft_breakdown.append({
            "yarn_name"       : weft.yarn.display_name,
            "yarn_id"         : weft.yarn.id,
            "yards_per_pound" : weft.yarn.yards_per_pound,
            "role"            : weft.role,
            "ppi"             : yarn_ppi,
            "yards"           : round(weft_yards, 1),
        })

    return {
        "label"            : piece.label,
        "finished_length"  : piece.finished_length,
        "finished_width"   : piece.finished_width,
        "hem_allowance"    : piece.hem_allowance,
        "fringe"           : piece.fringe,
        "woven_length"     : round(woven_length, 2),
        "fringe_total"     : fringe_total,
        "gap"              : gap_allowance,
        "piece_warp_length": round(piece_warp_length, 2),
        "weft_breakdown"   : weft_breakdown,
    }


def _summarize_weft(piece_details: list[dict], num_pieces: int) -> list[dict]:
    """
    Aggregate weft yardage across all pieces by yarn name.
    Returns one entry per unique weft yarn with total and per-piece yards.
    """
    totals: dict[str, dict] = {}
    for piece in piece_details:
        for weft in piece["weft_breakdown"]:
            name = weft["yarn_name"]
            if name not in totals:
                totals[name] = {
                    "yarn_name"       : name,
                    "yards_per_pound" : weft["yards_per_pound"],
                    "total_yards"     : 0.0,
                }
            totals[name]["total_yards"] += weft["yards"]

    # calculate per-piece average
    for entry in totals.values():
        entry["yards_per_piece"] = round(entry["total_yards"] / num_pieces, 1)
        entry["total_yards"]     = round(entry["total_yards"], 1)
        entry["weight_oz"]       = round(
            (entry["total_yards"] / entry["yards_per_pound"]) * 16, 1
        )

    return list(totals.values())


def calculate_warp(params: WarpParameters) -> WarpPlan:
    """
    Main entry point. Pass in a WarpParameters, get back a WarpPlan.
    """
    warnings = []

    # --- sett ---
    if params.sett_override is not None:
        sett = params.sett_override
        sett_was_overridden = True
    else:
        sett = round(params.yarn.wraps_per_inch * params.structure.sett_multiplier)
        sett_was_overridden = False

    # --- PPI (defaults to EPI for balanced weave) ---
    if params.ppi_override is not None:
        ppi = params.ppi_override
        ppi_was_overridden = True
    else:
        ppi = sett
        ppi_was_overridden = False

    # --- warp width (adjusted for draw-in) ---
    widest = max(p.finished_width for p in params.pieces)
    warp_width = widest / (1 - params.take_up_pct)

    if warp_width > params.loom.max_weaving_width:
        warnings.append(
            f"Calculated warp width ({warp_width:.1f}\") exceeds loom maximum "
            f"({params.loom.max_weaving_width}\"). Reduce width or sett."
        )

    # --- total ends ---
    total_ends = round(warp_width * sett)

    # --- per-piece breakdown ---
    piece_details = [
        _calc_piece(p, sett, ppi, warp_width, params.take_up_pct, params.gap_allowance)
        for p in params.pieces
    ]

    # --- warp length ---
    pieces_total_inches = sum(p["piece_warp_length"] for p in piece_details)
    warp_length_inches  = pieces_total_inches + params.loom.loom_waste
    warp_length_yards   = warp_length_inches / 36

    # --- warp yardage and weight ---
    warp_yards     = (total_ends * warp_length_inches) / 36
    warp_weight_oz = (warp_yards / params.yarn.yards_per_pound) * 16

    # --- weft totals ---
    weft_summary       = _summarize_weft(piece_details, len(params.pieces))
    total_weft_yards   = sum(w["total_yards"] for w in weft_summary)
    total_weft_weight_oz = sum(w["weight_oz"] for w in weft_summary)

    # --- combined ---
    total_yards      = warp_yards + total_weft_yards
    total_weight_oz  = warp_weight_oz + total_weft_weight_oz
    total_weight_lbs = total_weight_oz / 16

    return WarpPlan(
        loom_name            = params.loom.name,
        yarn_name            = params.yarn.display_name,
        yarn_yards_per_pound = params.yarn.yards_per_pound,
        structure_name       = params.structure.name,
        take_up_pct          = params.take_up_pct,
        gap_allowance        = params.gap_allowance,
        sett                 = sett,
        ppi                  = ppi,
        sett_was_overridden  = sett_was_overridden,
        ppi_was_overridden   = ppi_was_overridden,
        piece_details        = piece_details,
        total_ends           = total_ends,
        warp_length_inches   = round(warp_length_inches, 2),
        warp_length_yards    = round(warp_length_yards, 3),
        warp_yards           = round(warp_yards, 1),
        warp_weight_oz       = round(warp_weight_oz, 1),
        weft_summary         = weft_summary,
        total_weft_yards     = round(total_weft_yards, 1),
        total_weft_weight_oz = round(total_weft_weight_oz, 1),
        total_yards          = round(total_yards, 1),
        total_weight_oz      = round(total_weight_oz, 1),
        total_weight_lbs     = round(total_weight_lbs, 3),
        warnings             = warnings,
    )
