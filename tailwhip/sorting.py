"""Utilities for sorting Tailwind CSS classes."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from tailwhip.configuration import config


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

    # Try to find the longest matching prefix
    # e.g., "inline-flex" should match as prefix, not "inline" + value "flex"
    for i in range(len(remaining), 0, -1):
        candidate = "-".join([prefix, *remaining[:i]])
        if candidate in config.prefix_index:
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
        if direction is None and token in config.direction_index:
            direction = token
        elif size is None and token in config.size_index:
            size = token
        elif value is None and token in config.value_index:
            value = token
        elif color is None and token in config.color_index:
            color = token
        elif shade is None and token in config.shade_index:
            shade = token
        else:
            suffix_parts.append(token)

    return direction, size, value, color, shade, "-".join(suffix_parts)


@cache
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

    # 2. Split variants from the utility
    parts = remaining.split(config.variant_separator)
    variants = parts[:-1]  # All but the last are variants
    utility = parts[-1]  # Last part is the utility

    # 3. Check for negated prefix (-)
    negated = utility.startswith("-")
    if negated:
        utility = utility[1:]

    # 4. Handle alpha value (e.g., bg-red-500/50)
    alpha = None
    if "/" in utility:
        utility, alpha = utility.rsplit("/", 1)

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


def _tokenize(utility: str) -> list[str]:
    """
    Split a utility string into tokens, keeping arbitrary values together.

    Examples:
        "border-t-2" -> ["border", "t", "2"]
        "w-[100px]" -> ["w", "[100px]"]
        "grid-cols-[200px_1fr]" -> ["grid", "cols", "[200px_1fr]"]

    """
    tokens = []
    current = ""
    bracket_depth = 0

    for char in utility:
        if char == "[":
            bracket_depth += 1
            current += char
        elif char == "]":
            bracket_depth -= 1
            current += char
        elif char == "-" and bracket_depth == 0:
            if current:
                tokens.append(current)
            current = ""
        else:
            current += char

    if current:
        tokens.append(current)

    return tokens


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


def _component_rank(component_type: str, parsed: ParsedClass) -> tuple[int, str]:
    """
    Get the sort rank for a component type from a parsed class.

    Returns a tuple of (index, value) where:
    - index is the position in the component's list
    - value is the string value for secondary sorting

    Direction: no-direction sorts first (-1), e.g., border-1 before border-t-1.
    Other components: no-value sorts last (max_rank), e.g., border-1 before border-red.
    Unknown prefixes get -1 (sort first, non-Tailwind classes before Tailwind).
    Unknown values (not in the list) get max_rank (sort last).
    """
    # Get component data: (value, index_map, none_rank, unknown_rank)
    # Using if/elif chain instead of dict lookup for performance
    if component_type == "prefix":
        value, index_map, none_rank, unknown_rank = (
            parsed.prefix,
            config.prefix_index,
            -1,
            -1,
        )
    elif component_type == "direction":
        value, index_map, none_rank, unknown_rank = (
            parsed.direction,
            config.direction_index,
            -1,
            _MAX_RANK,
        )
    elif component_type == "size":
        value, index_map, none_rank, unknown_rank = (
            parsed.size,
            config.size_index,
            _MAX_RANK,
            _MAX_RANK,
        )
    elif component_type == "value":
        value, index_map, none_rank, unknown_rank = (
            parsed.value,
            config.value_index,
            _MAX_RANK,
            _MAX_RANK,
        )
    elif component_type == "color":
        value, index_map, none_rank, unknown_rank = (
            parsed.color,
            config.color_index,
            _MAX_RANK,
            _MAX_RANK,
        )
    elif component_type == "shade":
        value, index_map, none_rank, unknown_rank = (
            parsed.shade,
            config.shade_index,
            _MAX_RANK,
            _MAX_RANK,
        )
    elif component_type == "alpha":
        value, index_map, none_rank, unknown_rank = (
            parsed.alpha,
            config.alpha_index,
            _MAX_RANK,
            _MAX_RANK,
        )
    else:
        return (_MAX_RANK, "")

    if value is None:
        return (none_rank, "")

    idx = index_map.get(value, unknown_rank)
    return (idx, value)


def _get_variant_rank(variant: str) -> int:
    """Get the sort rank for a single variant, supporting prefix matching."""
    # Try exact match first (fast path)
    if variant in config.variant_index:
        return config.variant_index[variant]

    # Try prefix match (e.g., "min-[320px]" matches "min")
    for known_variant, idx in config.variant_index.items():
        if variant.startswith((known_variant + "-", known_variant + "[")):
            return idx

    return _MAX_RANK


def _variant_sort_key(variants: list[str]) -> tuple:
    """
    Generate a sort key for a list of variants.

    Returns a tuple that can be compared for sorting.
    """
    return tuple((_get_variant_rank(v), v) for v in variants)


def sort_key(classname: str) -> tuple:
    """
    Generate a sort key for a Tailwind CSS class.

    Sort order:
    1. Variants (by their order in variants list)
    2. Prefix (by order in prefixes list)
    3. Base utility flag (base utilities sort first within same prefix)
    4. Direction, Size, Value, Color, Shade, Alpha (by component_order)
    5. Suffix (arbitrary values sort last)
    """
    parsed = parse_class(classname)

    # Build the sort key
    key_parts: list = []

    # 1. Variants
    key_parts.append(_variant_sort_key(parsed.variants))

    # 2. Prefix
    key_parts.append(_component_rank("prefix", parsed))

    # 3. Base utility flag (base utilities sort first within same prefix)
    #    This ensures "border" < "border-t" and "blur" < "blur-sm"
    key_parts.append(0 if _is_base_utility(parsed) else 1)

    # 4. Components in order (skip variant and prefix)
    key_parts.extend(
        _component_rank(component_type, parsed)
        for component_type in config.component_order
        if component_type not in ("variant", "prefix")
    )

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
