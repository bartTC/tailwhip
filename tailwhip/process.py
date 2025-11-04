"""Process HTML and CSS content to sort Tailwind CSS classes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tailwhip.configuration import (
    APPLY_RE,
    CLASS_ATTR_RE,
    SKIP_EXPRESSIONS,
)
from tailwhip.context import get_config
from tailwhip.sorting import sort_classes

if TYPE_CHECKING:
    import re


def split_classes(s: str) -> list[str]:
    """Split a string of space-separated CSS classes into a list.

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


def process_class_attr(match: re.Match[str]) -> str:
    """Process and sort CSS classes within an HTML class attribute.

    Extracts class names from an HTML class attribute regex match, sorts them using
    Tailwind CSS ordering rules, and reconstructs the attribute. Preserves the original
    quote style. Skips processing if Django/Jinja template expressions are detected.

    Args:
        match: A regex match object containing groups 'full', 'quote', and 'val'

    Returns:
        The reconstructed class attribute string with sorted classes, or the original
        string if processing was skipped

    Examples:
        >>> # Input: class="flex container p-4"
        >>> # Output: class="container flex p-4"

        >>> # Input: class='hover:bg-blue-500 bg-red-500'
        >>> # Output: class='bg-red-500 hover:bg-blue-500'

        >>> # Input: class="text-{{ color }}-500 flex"  # Django template
        >>> # Output: class="text-{{ color }}-500 flex"  # Unchanged

        >>> # Input: class=""
        >>> # Output: class=""  # Unchanged

    """
    config = get_config()
    full = match.group("full")
    quote = match.group("quote")
    val = match.group("val")

    # Skip if a template expression appears inside the class attribute
    if any(skip_expr in val for skip_expr in SKIP_EXPRESSIONS):
        return full

    classes = split_classes(val)

    # Skip if no classes were found
    if not classes:
        return full

    sorted_classes = sort_classes(classes)
    new_val = " ".join(sorted_classes)
    return f"class={quote}{new_val}{quote}"


def process_apply_directive(match: re.Match[str]) -> str:
    """Process and sort CSS classes within a Tailwind @apply directive.

    Extracts class names from a CSS @apply directive regex match, sorts them using
    Tailwind CSS ordering rules, and reconstructs the directive.

    Args:
        match: A regex match object containing a 'classes' group

    Returns:
        The reconstructed @apply directive string with sorted classes, or the original
        string if no classes were found

    Examples:
        >>> # Input: @apply flex container p-4;
        >>> # Output: @apply container flex p-4;

        >>> # Input: @apply hover:bg-blue-500 bg-red-500 transition;
        >>> # Output: @apply bg-red-500 transition hover:bg-blue-500;

        >>> # Input: @apply text-lg font-bold text-blue-500;
        >>> # Output: @apply text-lg font-bold text-blue-500;

        >>> # Input: @apply;
        >>> # Output: @apply;  # Unchanged

    """
    config = get_config()
    classes_str = match.group("classes").strip()

    # Skip if a template expression appears inside the class attribute
    if any(skip_expr in classes_str for skip_expr in SKIP_EXPRESSIONS):
        return match.group(0)

    classes = split_classes(classes_str)

    # Skip if no classes were found
    if not classes:
        return match.group(0)

    sorted_classes = sort_classes(classes)
    new_classes = " ".join(sorted_classes)
    return f"@apply {new_classes};"


def process_html(text: str) -> str:
    """Process all HTML class attributes in the given text.

    Finds all class attributes using regex and sorts their CSS classes according to
    Tailwind CSS ordering rules. Operates on each class attribute independently,
    skipping those containing Django/Jinja template expressions.

    Args:
        text: HTML content as a string

    Returns:
        The HTML content with all class attributes sorted

    Examples:
        >>> process_html('<div class="flex container p-4"></div>')
        '<div class="container flex p-4"></div>'

        >>> process_html('<p class="text-blue-500 font-bold">Hello</p>')
        '<p class="font-bold text-blue-500">Hello</p>'

        >>> html = '<div class="flex p-4"><span class="text-lg">Text</span></div>'
        >>> process_html(html)
        '<div class="flex p-4"><span class="text-lg">Text</span></div>'

        >>> # Django templates are preserved
        >>> process_html('<div class="flex {{ extra_classes }}"></div>')
        '<div class="flex {{ extra_classes }}"></div>'

    """
    return CLASS_ATTR_RE.sub(process_class_attr, text)


def process_css(text: str) -> str:
    """Process all @apply directives in CSS content.

    Finds all Tailwind @apply directives using regex and sorts their CSS classes
    according to Tailwind CSS ordering rules.

    Args:
        text: CSS content as a string

    Returns:
        The CSS content with all @apply directives sorted

    Examples:
        >>> process_css('.btn { @apply flex p-4 container; }')
        '.btn { @apply container flex p-4; }'

        >>> process_css('.card { @apply rounded shadow-lg bg-white; }')
        '.card { @apply rounded shadow-lg bg-white; }'

        >>> css = '''
        ... .button {
        ...   @apply bg-blue-500 hover:bg-blue-700 text-white;
        ... }
        ... '''
        >>> process_css(css)
        # Returns with sorted classes in @apply

    """
    return APPLY_RE.sub(process_apply_directive, text)


def process_text(text: str) -> str:
    """Process file content by sorting Tailwind classes.

    Processes both HTML class attributes and CSS @apply directives in the same pass.
    This works for any file type since unmatched patterns are simply ignored.

    Args:
        text: The file content as a string

    Returns:
        The processed content with sorted CSS classes

    Examples:
        >>> process_text('<div class="flex p-4"></div>')
        '<div class="flex p-4"></div>'

        >>> process_text('.btn { @apply flex p-4; }')
        '.btn { @apply flex p-4; }'

        >>> process_text('<template class="grid gap-4"></template>')
        '<template class="gap-4 grid"></template>'

        >>> process_text('@apply rounded shadow;')
        '@apply rounded shadow;'

    """
    # Process both HTML class attributes and CSS @apply directives
    # If the pattern doesn't match, the text is unchanged
    text = process_html(text)
    return process_css(text)
