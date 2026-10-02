"""Utilities for sorting Tailwind CSS classes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from tailwhip.configuration import lookups, register_cache_clearer


@dataclass(slots=True)
class ParsedClass:
    """A parsed Tailwind CSS class with all its components."""

    original: str
    important: bool
    negated: bool
    variants: list[str]
    prefix: str
    direction: str | None
    size: str | None
    value: str | None
    color: str | None
    shade: str | None
    alpha: str | None
    suffix: str  # Any remaining unparsed parts


def _extract_prefix_and_tokens(tokens: list[str]) -> tuple[str, list[str]]:
    """Extract the longest matching prefix and return remaining tokens."""
    if not tokens:
        return "", []

    prefix = tokens[0]
    remaining = tokens[1:]
    prefix_index = lookups.prefix_index

    # Try to find the longest matching prefix
    # e.g., "inline-flex" should match as prefix, not "inline" + value "flex"
    for i in range(len(remaining), 0, -1):
        candidate = "-".join([prefix, *remaining[:i]])
        if candidate in prefix_index:
            return candidate, remaining[i:]

    return prefix, remaining


def _parse_component_tokens(
    tokens: list[str],
) -> tuple[str | None, str | None, str | None, str | None, str | None, str]:
    """Parse tokens into component values: direction, size, value, color, shade, suffix."""
    direction = None
    size = None
    value = None
    color = None
    shade = None
    suffix_parts = []

    for token in tokens:
        if direction is None and token in lookups.direction_index:
            direction = token
        elif size is None and token in lookups.size_index:
            size = token
        elif value is None and token in lookups.value_index:
            value = token
        elif color is None and token in lookups.color_index:
            color = token
        elif shade is None and token in lookups.shade_index:
            shade = token
        else:
            suffix_parts.append(token)

    return direction, size, value, color, shade, "-".join(suffix_parts)


def parse_class(classname: str) -> ParsedClass:
    """
    Parse a Tailwind CSS class into its components.

    Examples:
        parse_class("flex") -> prefix="flex"
        parse_class("sm:hover:flex") -> variants=["sm", "hover"], prefix="flex"
        parse_class("!-mt-4") -> important=True, negated=True, prefix="mt", value="4"
        parse_class("border-t-red-500/50") -> prefix="border", direction="t",
                                              color="red", shade="500", alpha="50"

    """
    original = classname
    remaining = classname

    # 1. Check for important prefix (!)
    important = remaining.startswith("!")
    if important:
        remaining = remaining[1:]

    # 2. Split variants from the utility. Separators inside [...] or (...)
    #    belong to an arbitrary value, e.g. "supports-[display:grid]:grid".
    parts = _split_top_level(remaining, lookups.variant_separator)
    variants = parts[:-1]  # All but the last are variants
    utility = parts[-1]  # Last part is the utility

    # 3. Check for negated prefix (-)
    negated = utility.startswith("-")
    if negated:
        utility = utility[1:]

    # 4. Handle alpha value (e.g., bg-red-500/50). A "/" inside brackets belongs
    #    to the arbitrary value, e.g. "bg-[url(/img/bg.png)]".
    alpha = None
    utility_parts = _split_top_level(utility, "/")
    if len(utility_parts) > 1:
        alpha = utility_parts[-1]
        utility = "/".join(utility_parts[:-1])

    # 5. Tokenize and parse components
    tokens = _tokenize(utility)
    prefix, remaining_tokens = _extract_prefix_and_tokens(tokens)
    direction, size, value, color, shade, suffix = _parse_component_tokens(
        remaining_tokens
    )

    return ParsedClass(
        original=original,
        important=important,
        negated=negated,
        variants=variants,
        prefix=prefix,
        direction=direction,
        size=size,
        value=value,
        color=color,
        shade=shade,
        alpha=alpha,
        suffix=suffix,
    )


def _split_top_level(text: str, separator: str) -> list[str]:
    """
    Split text on separator, ignoring separators nested inside [...] or (...).

    Arbitrary values ("w-[calc(100%-2rem)]"), arbitrary variants
    ("supports-[display:grid]:") and CSS variable shorthands ("bg-(--brand)")
    contain characters that would otherwise be mistaken for separators.
    """
    # Without an opening bracket nothing can be nested, so a plain split is
    # equivalent and much faster than walking the string character by character.
    if "[" not in text and "(" not in text:
        return text.split(separator)

    parts: list[str] = []
    current: list[str] = []
    depth = 0
    index = 0

    while index < len(text):
        char = text[index]
        if char in "[(":
            depth += 1
        elif char in "])" and depth > 0:
            depth -= 1

        if depth == 0 and text.startswith(separator, index):
            parts.append("".join(current))
            current = []
            index += len(separator)
            continue

        current.append(char)
        index += 1

    parts.append("".join(current))
    return parts


def _tokenize(utility: str) -> list[str]:
    """
    Split a utility string into tokens, keeping arbitrary values together.

    Examples:
        "border-t-2" -> ["border", "t", "2"]
        "w-[100px]" -> ["w", "[100px]"]
        "grid-cols-[200px_1fr]" -> ["grid", "cols", "[200px_1fr]"]
        "bg-(--brand-color)" -> ["bg", "(--brand-color)"]

    """
    return [token for token in _split_top_level(utility, "-") if token]


def _is_base_utility(parsed: ParsedClass) -> bool:
    """Check if this is a base utility with no modifiers after prefix."""
    return (
        parsed.direction is None
        and parsed.size is None
        and parsed.value is None
        and parsed.color is None
        and parsed.shade is None
        and parsed.alpha is None
        and not parsed.suffix
    )


_MAX_RANK = 999999  # For unknown values not in any list

# The components compared after variants and prefix, keyed by their name in the
# component_order configuration. Each entry holds the ParsedClass attribute, the
# lookup table on `lookups`, the rank used when a class has no such component and
# the rank used when the value is not in the list:
#
# - Direction: no-direction sorts first (-1), e.g., border-1 before border-t-1.
# - Other components: no-value sorts last (max rank), e.g., border-1 before border-red.
# - Unknown values (not in the list) get max rank (sort last).
_COMPONENTS: dict[str, tuple[str, str, int, int]] = {
    "direction": ("direction", "direction_index", -1, _MAX_RANK),
    "size": ("size", "size_index", _MAX_RANK, _MAX_RANK),
    "value": ("value", "value_index", _MAX_RANK, _MAX_RANK),
    "color": ("color", "color_index", _MAX_RANK, _MAX_RANK),
    "shade": ("shade", "shade_index", _MAX_RANK, _MAX_RANK),
    "alpha": ("alpha", "alpha_index", _MAX_RANK, _MAX_RANK),
}

# Tables derived from the configuration by _refresh_tables(): the components to
# compare in configured order as (attribute, index, none_rank, unknown_rank), and
# the ("name-", "name[") prefixes with their rank for variants that take an
# argument, e.g. "min-[320px]".
_component_ranks: list[tuple[str, dict[str, int], int, int]] = []
_variant_prefixes: list[tuple[tuple[str, str], int]] = []


def _get_variant_rank(variant: str) -> int:
    """Get the sort rank for a single variant, supporting prefix matching."""
    # Try exact match first (fast path)
    rank = lookups.variant_index.get(variant)
    if rank is not None:
        return rank

    # Try prefix match (e.g., "min-[320px]" matches "min")
    for prefixes, rank in _variant_prefixes:
        if variant.startswith(prefixes):
            return rank

    return _MAX_RANK


def _variant_sort_key(variants: list[str]) -> tuple:
    """
    Generate a sort key for a list of variants.

    Returns a tuple that can be compared for sorting.
    """
    return tuple((_get_variant_rank(v), v) for v in variants)


@cache
def sort_key(classname: str) -> tuple:
    """
    Generate a sort key for a Tailwind CSS class.

    Sort order:
    1. Variants (by their order in variants list)
    2. Prefix (by order in prefixes list)
    3. Base utility flag (base utilities sort first within same prefix)
    4. Direction, Size, Value, Color, Shade, Alpha (by component_order)
    5. Suffix (arbitrary values sort last)

    Keys are cached per class name, as the same classes appear over and over
    across a codebase. The cache is dropped whenever the configuration changes.
    """
    parsed = parse_class(classname)

    key_parts: list = [
        # 1. Variants
        _variant_sort_key(parsed.variants),
        # 2. Prefix. Unknown prefixes get -1, so non-Tailwind classes sort first.
        (lookups.prefix_index.get(parsed.prefix, -1), parsed.prefix),
        # 3. Base utility flag (base utilities sort first within same prefix)
        #    This ensures "border" < "border-t" and "blur" < "blur-sm"
        0 if _is_base_utility(parsed) else 1,
    ]

    # 4. Components in configured order
    for attribute, index, none_rank, unknown_rank in _component_ranks:
        value = getattr(parsed, attribute)
        if value is None:
            key_parts.append((none_rank, ""))
        else:
            key_parts.append((index.get(value, unknown_rank), value))

    # 5. Suffix (arbitrary values sort last within same component structure)
    key_parts.append((0 if not parsed.suffix else 1, parsed.suffix))

    # 6. Original class name as final tiebreaker for stability
    key_parts.append(parsed.original)

    return tuple(key_parts)


def sort_classes(class_list: list[str]) -> list[str]:
    """
    Sort a list of Tailwind CSS classes in a consistent, logical order.

    Classes are deduplicated (preserving the first occurrence) and sorted
    according to the component_order configuration.
    """
    # Deduplicate while preserving first occurrence order
    deduped = list(dict.fromkeys(class_list))
    return sorted(deduped, key=sort_key)


def _refresh_tables() -> None:
    """Rebuild the sorting tables from the configuration and drop cached sort keys."""
    ranks = []
    for component in lookups.component_order:
        # Unknown component names are ignored; "variant" and "prefix" always
        # come first and are handled separately in sort_key()
        if component in _COMPONENTS:
            attribute, table, none_rank, unknown_rank = _COMPONENTS[component]
            ranks.append((attribute, getattr(lookups, table), none_rank, unknown_rank))
    _component_ranks[:] = ranks

    _variant_prefixes[:] = [
        ((variant + "-", variant + "["), rank)
        for variant, rank in lookups.variant_index.items()
    ]

    sort_key.cache_clear()


# Sort keys depend on the configuration lists, so the tables and the cache must be
# rebuilt whenever the configuration changes.
register_cache_clearer(_refresh_tables)
_refresh_tables()
