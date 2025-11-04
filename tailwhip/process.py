"""Process HTML and CSS content to sort Tailwind CSS classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tailwhip.configuration import config
from tailwhip.sorting import sort_classes

if TYPE_CHECKING:
    import re


def split_classes(s: str) -> list[str]:
    """
    Split a string of space-separated CSS classes into a list.

    Handles multiple consecutive spaces and strips leading/trailing whitespace.
    Empty strings are filtered out from the result.

    Args:
        s: A string containing space-separated CSS class names

    Returns:
        A list of individual class name strings

    Examples:
        >>> split_classes('flex container p-4')
        ['flex', 'container', 'p-4']

        >>> split_classes('  flex   container  ')
        ['flex', 'container']

        >>> split_classes('hover:bg-blue-500 lg:text-xl')
        ['hover:bg-blue-500', 'lg:text-xl']

        >>> split_classes('')
        []

        >>> split_classes('   ')
        []

    """
    return s.strip().split()


def process_pattern(match: re.Match[str], template: str) -> str:
    """
    Process and sort CSS classes within a pattern match.

    Extracts class names from a regex match, sorts them using Tailwind CSS
    ordering rules, and reconstructs the match using a template string.
    Skips processing if template expressions are detected.

    Args:
        match: A regex match object that must contain a 'classes' named group
        template: Format string for reconstruction, using named groups from the match

    Returns:
        The reconstructed string with sorted classes, or the original string
        if processing was skipped

    Examples:
        >>> # HTML class attribute:
        >>> # Input: class="flex container p-4"
        >>> # Output: class="container flex p-4"

        >>> # CSS @apply:
        >>> # Input: @apply flex container p-4;
        >>> # Output: @apply container flex p-4;

        >>> # Template expression (skipped):
        >>> # Input: class="text-{{ color }}-500 flex"
        >>> # Output: class="text-{{ color }}-500 flex"  # Unchanged

    """
    classes_str = match.group("classes")

    # Skip if a template expression appears inside the class attribute
    if any(skip_expr in classes_str for skip_expr in config.skip_expressions):
        return match.group(0)

    classes = split_classes(classes_str)

    # Skip if no classes were found
    if not classes:
        return match.group(0)

    sorted_classes = sort_classes(classes)

    # Get all named groups from the match as context
    context = match.groupdict()
    # Override 'classes' with sorted version
    context["classes"] = " ".join(sorted_classes)

    # Use template to reconstruct
    return template.format(**context)


def process_text(text: str) -> str:
    """
    Process file content by sorting Tailwind classes.

    Processes all configured patterns (HTML class, CSS @apply, etc.) in a single
    pass. This works for any file type since unmatched patterns are simply ignored.

    Args:
        text: The file content as a string

    Returns:
        The processed content with sorted CSS classes

    Examples:
        >>> process_text('<div class="flex p-4"></div>')
        '<div class="flex p-4"></div>'

        >>> process_text('.btn { @apply flex p-4; }')
        '.btn { @apply flex p-4; }'

        >>> process_text('@apply rounded shadow;')
        '@apply rounded shadow;'

    """
    # Process all configured patterns in order
    # If a pattern doesn't match, the text is unchanged
    for pattern in config.APPLY_PATTERNS:
        text = pattern.regex.sub(
            lambda match, template=pattern.template: process_pattern(match, template),
            text,
        )
    return text
