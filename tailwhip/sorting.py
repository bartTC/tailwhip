"""Utilities for sorting Tailwind CSS classes."""

from __future__ import annotations

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


def is_color_utility(utility: str, all_colors: set[str]) -> bool:
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
        all_colors: Set of all color names (standard + custom)

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
    return any(color in utility_without_opacity for color in all_colors)


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


def sort_key(
    cls: str, all_colors: set[str]
) -> tuple[tuple[tuple[int, str], ...], int, bool, str]:
    """
    Generate a sort key for a Tailwind CSS class.

    Creates a tuple that enables proper sorting of Tailwind classes.
    Classes are sorted by:

    1. Variants (by their rank order from VARIANT_PREFIX_ORDER, then alphabetically)
    2. Utility rank (by category)
    3. Color status (non-color utilities before color utilities)
    4. Base utility name (alphabetically within category)

    Args:
        cls: A complete Tailwind CSS class string (with or without variants)
        all_colors: Set of all color names (standard + custom)

    Returns:
        A tuple suitable for sorting

    Examples:
        >>> sort_key('text-sm')
        ((), 5, False, 'text-sm')

        >>> sort_key('text-blue-500')
        ((), 5, True, 'text-blue-500')

        >>> sort_key('hover:text-blue-500')
        (((10, 'hover'),), 5, True, 'text-blue-500')

        >>> sort_key('sm:hover:flex')
        (((3, 'sm'), (10, 'hover')), 1, False, 'flex')

        >>> sort_key('lg:container')
        (((3, 'lg'),), 0, False, 'container')

    """
    variants, base = variant_base(cls)
    variant_keys = tuple((variant_rank(v), v) for v in variants)
    is_color = is_color_utility(base, all_colors)
    return variant_keys, utility_rank(base), is_color, base


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
    all_colors = config.tailwind_colors | config.custom_colors
    deduped = list(dict.fromkeys(class_list))
    return sorted(deduped, key=lambda cls: sort_key(cls, all_colors))
