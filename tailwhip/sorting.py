"""Utilities for sorting Tailwind CSS classes."""

from __future__ import annotations

import re

from tailwhip.configuration import config


def variant_rank(variant: str) -> int:
    """
    Determine the sort order rank of a variant.

    Args:
        variant: A variant string (e.g., 'hover', 'sm', 'dark')

    Returns:
        An integer representing the variant's rank. Lower values sort earlier.
        Unknown variants receive a rank of len(VARIANT_PATTERNS) + 1.

    """
    variant_with_colon = f"{variant}:"
    for i, pat in enumerate(config.VARIANT_PATTERNS):
        if pat.match(variant_with_colon):
            return i
    return len(config.VARIANT_PATTERNS) + 1  # unknowns to the end


def variant_base(classname: str) -> tuple[list[str], str]:
    """
    Split a Tailwind CSS class into its variants and base utility.

    Variants are modifiers that apply conditions to utilities (e.g., responsive
    breakpoints, pseudo-classes). This function separates them from the base utility
    and sorts variants by VARIANT_PREFIX_ORDER to ensure consistent ordering.

    Args:
        classname: A Tailwind CSS class string, potentially with variants separated
                   by colons

    Returns:
        A tuple containing:
            - A sorted list of variant strings (ordered by VARIANT_PREFIX_ORDER)
            - The base utility string

    Examples:
        >>> variant_base('text-blue-500')
        ([], 'text-blue-500')

        >>> variant_base('hover:text-blue-500')
        (['hover'], 'text-blue-500')

        >>> variant_base('sm:hover:focus:text-blue-500')
        (['sm', 'hover', 'focus'], 'text-blue-500')

        >>> variant_base('lg:dark:hover:bg-gray-900')
        (['dark', 'lg', 'hover'], 'bg-gray-900')

    """
    parts = classname.split(config.variant_separator)
    base = parts[-1]
    unique_variants = list(dict.fromkeys(parts[:-1]))  # dedupe while preserving order
    variants = sorted(unique_variants, key=lambda v: (variant_rank(v), v))
    return variants, base


def is_color_utility(utility: str) -> bool:
    """
    Check if a utility is a color-related utility.

    Color utilities follow patterns like:
    - text-{color}-{shade}: text-gray-600, text-blue-500
    - bg-{color}-{shade}: bg-red-400, bg-green-50
    - border-{color}-{shade}: border-gray-200
    - text-{color}: text-black, text-white, text-transparent
    - And similar for ring-, from-, via-, to-, divide-, placeholder-, etc.

    Args:
        utility: A base Tailwind CSS utility string (without variants)

    Returns:
        True if the utility includes a Tailwind color name, False otherwise

    Examples:
        >>> is_color_utility('text-gray-600')
        True

        >>> is_color_utility('text-sm')
        False

        >>> is_color_utility('bg-blue-500')
        True

        >>> is_color_utility('text-custom-color')
        False

        >>> is_color_utility('border-red-400')
        True

        >>> is_color_utility('bg-brand-500')
        True

    """
    # Strip opacity modifier (e.g., /90, /50) before checking
    utility_without_opacity = utility.split("/")[0]

    # Check for multi-part custom colors first (e.g., "secondary-500" in "border-t-secondary-500")
    return any(color in utility_without_opacity for color in config.all_colors)


def utility_rank(utility: str) -> int:
    """
    Determine the sort order rank of a Tailwind CSS utility class.

    Utilities are categorized into groups (layout, spacing, typography, etc.) defined
    in GROUP_PATTERNS. Each group has a rank that determines its position in sorted
    output. Lower ranks appear earlier. Unknown utilities are placed at the end.

    Args:
        utility: A base Tailwind CSS utility string (without variants)

    Returns:
        An integer representing the utility's group rank. Lower values sort earlier.
        Unknown utilities receive a rank of len(GROUP_PATTERNS) + 1.

    Examples:
        >>> utility_rank('container')  # Layout utilities come first
        0

        >>> utility_rank('flex')  # Display utilities
        1

        >>> utility_rank('mt-4')  # Spacing utilities
        2

        >>> utility_rank('text-blue-500')  # Typography/color utilities
        5

        >>> utility_rank('unknown-utility')  # Unknown utilities go to end
        15

    """
    # Strip leading negative sign for matching, so -mt-4 matches the same pattern as mt-4
    utility_to_match = utility.lstrip("-")

    for i, pat in enumerate(config.UTILITY_PATTERNS):
        if pat.match(utility_to_match):
            return i
    return -1  # len(configuration.GROUP_PATTERNS) + 1  # Unknown classes to the front


def parse_utility_components(utility: str) -> tuple[str, str | None, str | None, str]:
    """
    Parse a utility into its components: prefix, direction, size, and suffix.

    Many Tailwind utilities follow patterns like:
    - <name>-<direction>: border-t, m-x, rounded-l
    - <name>-<size>: text-sm, rounded-lg, shadow-xl
    - <name>-<direction>-<size>: rounded-t-lg, border-r-2

    Args:
        utility: A base Tailwind CSS utility string (without variants)

    Returns:
        A tuple of (prefix, direction, size, suffix) where:
        - prefix: The utility name before direction/size
        - direction: The direction component (x, y, t, r, b, l, etc.) or None
        - size: The size component (sm, lg, xl, etc.) or None
        - suffix: Any remaining parts after size (for complex utilities)

    Examples:
        >>> parse_utility_components('border-t')
        ('border', 't', None, '')

        >>> parse_utility_components('rounded-lg')
        ('rounded', None, 'lg', '')

        >>> parse_utility_components('rounded-t-lg')
        ('rounded', 't', 'lg', '')

        >>> parse_utility_components('border-[2px]')
        ('border', None, '[2px]', '')

    """
    # Handle arbitrary values like border-[2px]
    # These should be treated as part of the suffix, not as direction/size
    if "[" in utility:
        # Match pattern like "border-[2px]" or "rounded-t-[10px]"
        match = re.match(r"^([^-]+)-(.+?)-(\[.+?\])(.*)$", utility)
        if match:
            prefix, middle, arb_value, suffix = match.groups()
            # Check if middle part is a direction
            direction = middle if middle in config.directions else None
            # Arbitrary values are not sizes - include them in the suffix
            if direction:
                return (prefix, direction, None, arb_value + suffix)
            return (prefix, None, None, middle + "-" + arb_value + suffix)

        match = re.match(r"^([^-]+)-(\[.+?\])(.*)$", utility)
        if match:
            prefix, arb_value, suffix = match.groups()
            # Arbitrary value is part of suffix, not a size
            return (prefix, None, None, arb_value + suffix)

    parts = utility.split("-")
    if len(parts) == 1:
        return (utility, None, None, "")

    prefix = parts[0]
    remaining = parts[1:]

    # Try to match direction and size patterns
    direction = None
    size = None
    suffix_parts = []

    # Check if first remaining part is a direction
    if remaining and remaining[0] in config.directions:
        direction = remaining[0]
        remaining = remaining[1:]

    # Check if next part is a size
    if remaining and remaining[0] in config.sizes:
        size = remaining[0]
        remaining = remaining[1:]

    # If we didn't find direction, check if first part is a size
    min_parts_for_suffix = 2
    if direction is None and not remaining and parts[1:]:
        if parts[1] in config.sizes:
            size = parts[1]
            suffix_parts = parts[2:] if len(parts) > min_parts_for_suffix else []
        else:
            suffix_parts = parts[1:]
    else:
        suffix_parts = remaining

    suffix = "-".join(suffix_parts) if suffix_parts else ""
    return (prefix, direction, size, suffix)


def direction_rank(direction: str | None) -> int:
    """Get the rank of a direction for sorting."""
    if direction is None:
        return -1  # No direction comes first
    try:
        return config.directions.index(direction)
    except ValueError:
        return len(config.directions)  # Unknown directions go last


def size_rank(size: str | None) -> int:
    """Get the rank of a size for sorting."""
    if size is None:
        return -1  # No size comes first
    try:
        return config.sizes.index(size)
    except ValueError:
        return len(config.sizes)  # Unknown sizes go last


def sort_key(
    cls: str,
) -> tuple[tuple[tuple[int, str], ...], int, bool, str, int, int, str]:
    """
    Generate a sort key for a Tailwind CSS class.

    Creates a tuple that enables proper sorting of Tailwind classes.
    Classes are sorted by:

    1. Variants (by their rank order from VARIANT_PREFIX_ORDER, then alphabetically)
    2. Utility rank (by category)
    3. Color status (non-color utilities before color utilities)
    4. Base utility name prefix (alphabetically within category)
    5. Direction rank (x, y, t, r, b, l, etc.)
    6. Size rank (sm, md, lg, xl, etc.)
    7. Suffix (any remaining parts)

    Args:
        cls: A complete Tailwind CSS class string (with or without variants)

    Returns:
        A tuple suitable for sorting

    Examples:
        >>> sort_key('text-sm')
        ((), 5, False, 'text', -1, <size_rank('sm')>, '')

        >>> sort_key('border-t')
        ((), 8, False, 'border', <direction_rank('t')>, -1, '')

        >>> sort_key('rounded-t-lg')
        ((), 8, False, 'rounded', <direction_rank('t')>, <size_rank('lg')>, '')

    """
    variants, base = variant_base(cls)
    variant_keys = tuple((variant_rank(v), v) for v in variants)
    is_color = is_color_utility(base)

    # Strip leading negative sign for consistent sorting (e.g., -m-4 sorts with m-4)
    base_for_sorting = base.lstrip("-")

    # Parse direction and size components
    prefix, direction, size, suffix = parse_utility_components(base_for_sorting)

    return (
        variant_keys,
        utility_rank(base),
        is_color,
        prefix,
        direction_rank(direction),
        size_rank(size),
        suffix,
    )


def sort_classes(class_list: list[str]) -> list[str]:
    """
    Sort a list of Tailwind CSS classes in a consistent, logical order.

    Classes are deduplicated (preserving the first occurrence) and sorted by:

    1. Variants (non-responsive before responsive, alphabetically)
    2. Utility category (layout, display, spacing, typography, etc.)
    3. Utility name (alphabetically within category)

    Args:
        class_list: A list of Tailwind CSS class strings

    Returns:
        A sorted and deduplicated list of class strings

    Examples:
        >>> sort_classes(['text-blue-500', 'flex', 'container'])
        ['container', 'flex', 'text-blue-500']

        >>> sort_classes(['hover:bg-blue-500', 'bg-red-500', 'p-4'])
        ['p-4', 'bg-red-500', 'hover:bg-blue-500']

        >>> sort_classes(['lg:text-xl', 'sm:text-sm', 'text-base'])
        ['text-base', 'sm:text-sm', 'lg:text-xl']

        >>> sort_classes(['flex', 'flex', 'container', 'flex'])  # Deduplication
        ['container', 'flex']

        >>> sort_classes(['hover:focus:text-blue-500', 'text-red-500', 'sm:flex', 'flex'])
        ['flex', 'sm:flex', 'text-red-500', 'focus:hover:text-blue-500']

    """
    # Use colors from configuration (includes custom colors if configured)
    deduped = list(dict.fromkeys(class_list))
    return sorted(deduped, key=lambda cls: sort_key(cls))
