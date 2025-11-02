"""Constants used by tailwhip."""

from __future__ import annotations

import re

from rich.theme import Theme

# File glob(s) to process
GLOBS = ["**/*.html", "**/*.css"]

# Skip if a template expression appears inside the class attribute
# List of strings that indicate template expressions to skip
SKIP_EXPRESSIONS = ["{{", "{%", "<%"]

# Recognize Tailwind variants (order doesn't matter; we sort lexicographically)
# e.g. "sm:hover:focus:text-blue-500" => variants ["focus", "hover", "sm"]
VARIANT_SEP = ":"

# A lightweight utility ranking derived from common Tailwind "best practice" ordering.
# This is not exhaustive, but it's practical. Unknown utilities fall to the end.
#
# SORTING MECHANISM: ------------------
#
# Each regex pattern in this list defines a GROUP. Groups are matched in order (top
# to bottom). When a utility class is encountered, it's tested against each pattern
# until a match is found. The matched group's index becomes the utility's rank (lower
# index = sorts earlier).
#
# WHY MULTIPLE PATTERNS IN ONE GROUP?
#
# Some logical categories (e.g., "Layout & display") contain multiple related patterns.
# These are kept as separate regex entries rather than one mega-pattern because:
#
#   1. Readability: Easier to see what utilities belong together
#   2. Maintainability: Simpler to add/remove/modify individual patterns
#   3. Order control: You can fine-tune the sort order within a category
#      (e.g., "flex" before "grid" before "table")
#
# WHY SINGLE PATTERNS?
#
# Single patterns are used when:
#
#   - The utility is standalone or unique (e.g., "container")
#   - It needs precise positioning in the sort order
#   - It's a catch-all for a prefix (e.g., "text-" matches text-sm, text-lg, etc.)
#
# WITHIN-GROUP SORTING:
#
# Classes matching the SAME group index are then sorted:
#
#   1. Non-color utilities before color utilities
#   2. Alphabetically by the full class name
#
# Example: "flex", "flex-col", "flex-row" all match r"(flex|inline-flex)" and sort alphabetically.
#
GROUPS = [
    #
    # 0) Components (Tailwind "components" layer comes before utilities)
    r"(^| )(container)( |$)",
    #
    # 1) Layout & display
    r"(hidden|visible|invisible)",
    r"(z)-",
    r"(block|inline-block|inline|flow-root|contents)",
    r"(flex|inline-flex)",
    r"(grid|inline-grid)",
    r"(table|inline-table)",
    r"(box-border|box-content|box-decoration-(slice|clone))",
    r"(isolate|isolation-auto)",
    r"(static|fixed|absolute|relative|sticky)",
    r"(inset|top|right|bottom|left|z)-",
    r"(float|clear)-(left|right|none|start|end)",
    #
    # floats/clears
    r"(columns)-",
    #
    # CSS multi-column
    r"(break)-(inside|before|after)-",
    #
    # page/column breaks
    r"(overflow|overscroll)-",
    #
    # scrolling/overflow
    r"(scroll|scroll-m|scroll-p|scroll-smooth)",
    #
    # scroll behavior & margins
    r"(snap)-",
    #
    # 2) Flexbox & Grid
    r"(order|grow|shrink|basis)-",
    r"(grid-cols|grid-rows|grid-flow|auto-cols|auto-rows)-",
    r"(col-(span|start|end)|row-(span|start|end))-",
    r"(gap|space-[xy])-",
    #
    # 3) Alignment & distribution (box alignment)
    r"(place|content|items|self|justify|align)-",
    #
    # 4) Sizing
    r"(size)-",
    r"(w)-",
    r"(min-w)-",
    r"(max-w)-",
    r"(h)-",
    r"(min-h)-",
    r"(max-h)-",
    r"(aspect)-",
    #
    # 5) Spacing (x,y,t,r,b,l)
    r"(m)-",
    r"(mx)-",
    r"(my)-",
    r"(mt)-",
    r"(mr)-",
    r"(mb)-",
    r"(ml)-",
    r"(p)-",
    r"(px)-",
    r"(py)-",
    r"(pt)-",
    r"(pr)-",
    r"(pb)-",
    r"(pl)-",
    #
    # 6) Typography
    r"(font)-",
    r"(text-(balance|pretty|wrap))",
    r"(text)-",
    r"(tracking)-",
    r"(leading)-",
    r"(list)-",
    r"(indent)-",
    r"(placeholder)-",
    r"(whitespace|break|hyphens)-",
    r"(tab-size)-",
    r"(line-clamp)-",
    #
    # official plugin utility
    r"(antialiased|subpixel-antialiased|truncate)",
    #
    # single-token type utils
    r"(tabular-nums|slashed-zero|lining-nums|oldstyle-nums|proportional-nums|ordinal)",
    #
    # content-['…'] utilities
    r"(content)-",
    #
    # 7) Backgrounds
    # includes bg-clip, -origin, -repeat, -size, -position, -attachment, colors
    r"(bg)-",
    #
    # gradients
    r"(from)-",
    r"(to)-",
    r"(via)-",
    #
    #
    # 8) Borders & outlines & rings & divide
    r"(rounded)-",
    r"(border)-",
    r"(divide)-",
    r"(ring)-",
    r"(outline)-",
    #
    # 9) Effects
    r"(shadow)-",
    r"(opacity)-",
    r"(mix-blend)-",
    r"(backdrop|filter|blur|brightness|contrast|grayscale|hue-rotate|invert|saturate|sepia|drop-shadow)-",
    #
    # 10) Transforms
    r"(transform|scale|rotate|translate|skew|origin)-",
    #
    # 11) Transitions & animation
    r"(transition|duration|ease|delay|animate)-",
    #
    # 12) Interactivity & misc
    r"(cursor|select|pointer-events|resize|appearance|accent|caret|touch)-",
    r"(object)-",
    #
    # object-fit/position
    r"(outline-none)",
    #
    # single token
    r"(stroke|fill)-",
    #
    # SVG
    #
    # 13) Accessibility helpers (kept near the end so utility groups dominate)
    r"(sr-only|not-sr-only)",
    #
    # 14) Group/peer & attribute base selectors (as raw classes, not variants)
    r"(peer|group|aria-|data-)(:|$)",
]

VARIANT_PREFIX_ORDER = [
    #
    #  Container queries (most specific, come first)
    r"@container:",
    r"@\w+:",
    #
    #  Direction & theme
    r"(rtl|ltr):",
    r"dark:",
    #
    #  Media-like variants
    r"(portrait|landscape|print):",
    r"(motion-safe|motion-reduce):",
    r"(contrast-more|contrast-less):",
    #
    #  Container & size queries (if using v4 container queries)
    r"(supports-\[.*\]|supports-.*:)",
    #
    #  supports: variant patterns
    r"(size-.*:|cq-.*:)",
    #
    #  Breakpoints (mobile-first)
    r"min-\[.*\]:",
    r"max-\[.*\]:",
    r"sm:",
    r"md:",
    r"lg:",
    r"xl:",
    r"2xl:",
    #
    #  Structural/state
    r"(first):",
    r"(last):",
    r"(only):",
    r"(odd):",
    r"(even):",
    r"(first-of-type|last-of-type|only-of-type):",
    r"(visited|target|open|empty):",
    r"(enabled|disabled|read-only|required|optional):",
    r"(checked|indeterminate|default):",
    r"(valid|invalid):",
    r"(in-range|out-of-range):",
    r"(placeholder-shown):",
    r"(autofill):",
    r"(focus-within):",
    r"(hover|focus|focus-visible|focus-within|active):",
    r"(pressed|selected):",
    r"(current):",
    r"(aria-.*:|data-.*:)",
    #
    #  attribute variants
    r"(group(-\[.*\])?:.*:|group-.*:)",
    #
    #  group/compound (e.g. group-hover:)
    r"(peer(-\[.*\])?:.*:|peer-.*:)",
    #
    #  peer/compound (e.g. peer-checked:)
    r"(marker:|selection:|file:|placeholder:|backdrop:|first-letter:|first-line:)",
]


# Standard Tailwind color names (extracted from the palette)
TAILWIND_COLORS = {
    "transparent",
    "current",
    "black",
    "white",
    "amber",
    "blue",
    "blue-gray",
    "cool-gray",
    "cyan",
    "emerald",
    "fuchsia",
    "gray",
    "green",
    "indigo",
    "light-blue",
    "lime",
    "orange",
    "pink",
    "purple",
    "red",
    "rose",
    "sky",
    "teal",
    "true-gray",
    "violet",
    "warm-gray",
    "yellow",
}


GROUP_PATTERNS = [re.compile("^" + g) for g in GROUPS]

CLASS_ATTR_RE = re.compile(
    r"""(?P<full>\bclass\s*=\s*(?P<quote>["'])(?P<val>.*?)(?P=quote))""",
    re.IGNORECASE | re.DOTALL,
)

APPLY_RE = re.compile(
    r"""@apply\s+(?P<classes>[^;]+);""",
    re.MULTILINE,
)

CONSOLE_THEME = Theme(
    {
        "important": "white on deep_pink4",
        "highlight": "yellow1",
        "filename": "white",
        "bold": "sky_blue1",
    }
)

VERBOSITY_NONE = 0
VERBOSITY_LOUD = 2
VERBOSITY_ALL = 3
