"""
Tests for Tailwind CSS class sorting.

This module tests the core sorting algorithm that reorders Tailwind classes
according to utility groups, variants, and color priorities.

Test Coverage:
- Utility group ordering (layout, spacing, typography, etc.)
- Variant sorting (responsive, hover, focus, etc.)
- Color vs non-color utility prioritization
- Alphabetical sorting within groups
- Custom color handling
- CSS @apply directive processing
- HTML class attribute processing
- Template markup handling (skip expressions)
- Complex real-world examples (kitchen sink)

The sorting algorithm follows this hierarchy:
1. Group by utility type (using utility_groups regex patterns)
2. Sort by variant specificity (using variant_groups patterns)
3. Separate colors from non-colors (colors come last)
4. Alphabetically within each category
"""

from __future__ import annotations

import random

import pytest

from tailwhip.configuration import update_configuration
from tailwhip.process import process_text
from tailwhip.sorting import sort_classes


def shuffle(lst: list[str]) -> list[str]:
    """Shuffle a list and ensuring no element stays in the original position."""
    if len(lst) <= 1:
        msg = "Cannot shuffle a list with less than 2 elements."
        raise AssertionError(msg)

    shuffled = lst.copy()

    tries = 0
    while True:
        random.shuffle(shuffled)

        if shuffled != lst:
            return shuffled

        tries += 1

        if tries > 100:
            msg = "Unable to produce a shuffled list after 100 tries."
            raise AssertionError(msg)


# Test sorting of classes. Each of these groups contains a valid and correctly
# ordered set of classes. The testrun is going to shuffle them, sort them and
# compare the result.
#
# To mitigate shuffling randomness, we run the test multiple times.
CLASS_GROUPS = (
    # Container comes always first. But non-tailwind classes are firster.
    [
        "select2-container",  # Not tailwind
        "container",  # Container is first
        "m-2",
        "font-bold",
        "text-xl",
    ],
    #  Margin first, then padding. X, then Y, then in clockwise order.
    #
    #  m ->
    #      none -> x -> y -> t -> r -> b -> l
    #  p->
    #      none -> x -> y -> t -> r -> b -> l
    [
        "m-2",
        "mx-64",
        "my-128",
        "mt-4",
        "mr-8",
        "mb-16",
        "ml-32",
        "p-1",
        "px-32",
        "py-64",
        "pt-2",
        "pr-4",
        "pb-8",
        "pl-16",
    ],
    # Negative values don't change order.
    [
        "m-2",
        "-mx-64",
        "-my-128",
        "mt-4",
        "-mr-8",
        "mb-16",
        "-ml-32",
        "p-1",
        "-px-32",
        "py-64",
        "-pt-2",
        "-pr-4",
        "pb-8",
        "pl-16",
    ],
    # Negative values in variants retain order.
    [
        "-m-1",
        "sm:-m-2",
        "md:-m-3",
        "lg:-m-4",
        "xl:-m-5",
        "2xl:-m-6",
        "3xl:-m-7",
    ],
    # Size, W, Min-W, Max-W, H, Min-H, Max-H, Aspect.
    [
        "size-4",
        "w-10",
        "min-w-full",
        "max-w-md",
        "h-12",
        "min-h-screen",
        "max-h-96",
        "aspect-square",
    ],
    # Same, but more complex values
    [
        "size-[40px]",
        "w-[72rem]",
        "min-w-[320px]",
        "max-w-5xl",
        "h-[calc(100vh-4rem)]",
        "min-h-[60vh]",
        "max-h-[800px]",
        "aspect-[3/2]",
    ],
    # min-*: then max-*: variant
    [
        "text-base",
        "min-[320px]:text-sm",
        "max-[1024px]:hidden",
        "max-[320px]:text-sm",
    ],
    # Font first, then Text, Colors are always last of each group
    [
        r"font-light",
        r"font-gray-500",
        r"text-pretty",
        r"text-xl",
        r"text-black/90",
        r"text-red-400",
    ],
    # Breakpoints: none -> sm -> md -> lg -> xl -> 2xl
    [
        "p-2",
        "font-light",
        "text-sm",
        "text-gray-600",
        "sm:p-4",
        "sm:font-normal",
        "sm:text-base",
        "sm:text-gray-700",  # Color is last
        "md:p-6",
        "md:font-medium",
        "md:text-lg",
        "md:text-gray-800",
        "lg:p-8",
        "lg:font-semibold",
        "lg:text-xl",
        "lg:text-gray-900",
        "xl:p-10",
        "xl:font-bold",
        "xl:text-2xl",
        "xl:text-black",
        "2xl:p-12",
        "2xl:font-extrabold",
        "2xl:text-3xl",
        "2xl:text-black/90",
    ],
    # first: -> last: -> odd: -> even:
    [
        "first:border-t-0",
        "last:border-b-0",
        "odd:bg-gray-100",
        "even:bg-white",
    ],
    # dark: -> sm: -> md: -> lg: -> etc. And also within sub groups.
    [
        "dark:text-white",
        "dark:md:hover:text-blue-300",
        "dark:lg:hover:bg-gray-900",
        "sm:disabled:opacity-50",
        "md:first:px-4",
        "md:focus:text-white",
        "lg:text-xl",
        "lg:focus:hover:bg-blue-500",
        "first:mt-0",
        "focus:text-black",
        "hover:bg-red-500",
        "group-hover:bg-blue-500",
        "peer-checked:bg-green-500",
    ],
    [
        "border-1",  # No group, No color
        "border-t-2",
        "border-red-400",  # No group, Color
        "border-t-blue-500",
        "dark:border-1",  # Dark first
        "dark:border-t-2",
        "dark:border-red-400",  # Dark colors
        "dark:border-t-blue-500",
        "sm:border-1",  # Breakpoint before other
        "sm:border-t-2",
        "sm:border-red-400",
        "sm:border-t-blue-500",
        "focus:sm:border-1",  # Small breakpoint before large
        "focus:sm:border-t-2",
        "focus:sm:border-red-400",
        "focus:sm:border-t-blue-500",
        "focus:lg:border-1",
        "focus:lg:border-t-2",
        "focus:lg:border-red-400",
        "focus:lg:border-t-blue-500",
        "focus:border-1",  # No breakpoint after other
        "focus:border-t-2",
        "focus:border-red-400",
        "focus:border-t-blue-500",
    ],
    # Grid -> Cols -> Rows -> Gap
    [
        "grid",
        "grid-cols-[200px_1fr_2fr]",
        "grid-rows-4",
        "gap-4",
    ],
    # Gradient From -> To -> Via
    [
        "m-4",
        "bg-gradient-to-br",
        "from-pink-500",
        "to-yellow-500",
        "via-red-500",
    ],
    # Backdrop Blue Brightness etc.
    [
        "p-6",
        "bg-white/50",
        "backdrop-blur-md",
        "backdrop-brightness-75",
        "backdrop-contrast-125",
    ],
    # Arbitrary HTML
    [
        "p-2",
        "[&_a]:hover:underline",
        "[&>*]:p-4",
        "[&_a]:text-blue-500",
    ],
    # After before Before
    [
        "after:content-['>']",
        "before:content-['']",
        "before:content-['★']",
    ],
    # Classes which maybe standalone
    [
        "hidden",
        "grow",
        "grow-0",
        "shrink",
        "shrink-0",
        "truncate",
        "truncate-0",
    ],
    # Cols before rows
    [
        "grid",
        "grid-cols-2",
        "grid-rows-4",
        "gap-4",
    ],
    # Cols before rows
    [
        "flex",
        "flex-col",
        "flex-col-reverse",
        "flex-row",
        "flex-row-reverse",
        "items-stretch",
    ],
    # Gap X before Y
    [
        "grid",
        "gap-2",
        "gap-x-2",
        "gap-y-2",
        "space-x-2",
        "space-y-2",
    ],
    # Container queries come before variants
    [
        "p-4",
        "@container:p-4",
        "@lg:text-xl",
        "@xl:grid-cols-3",
        "dark:p-4",
        "lg:p-4",
        "xl:p-4",
    ],
    # Top -> Right -> Bottom -> Left
    [
        "top-[10px]",
        "right-[20px]",
        "bottom-[30px]",
        "left-[40px]",
    ],
)


@pytest.mark.parametrize("classes", CLASS_GROUPS)
@pytest.mark.parametrize("iteration", range(10))
def test_sorting(classes: list[str], iteration: int) -> None:  # noqa: ARG001
    """
    Test sorting of classes.

    The classes in the parameter are in the correct order. We shuffle them before
    we do the comparison. To mitigate randomness, we run the test multiple times.
    """
    result = sort_classes(shuffle(classes))
    assert result == classes


@pytest.mark.parametrize("iteration", range(10))
def test_sorting_custom_colors(iteration: int, monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: ARG001
    """Custom colors are sorted along with other colors."""
    update_configuration(
        {"custom_colors": {"primary", "secondary-500", "border-almond-500"}}
    )

    classes = [
        "border-1",  # Non colors
        "border-b-4",
        "border-t-2",
        "border-almond-500",  # Border Colors
        "border-primary",
        "border-red-400",
        "border-t-blue-500",  # Border Top Colors
        "border-t-secondary-500",
    ]

    result = sort_classes(shuffle(classes))
    assert result == classes


def test_kitchen_sink_example() -> None:
    """Test a complex real-world example with many advanced features."""
    html = """
<div class="group relative p-[calc(1rem+2px)] m-[clamp(1rem,5vw,3rem)]
            backdrop-blur-md backdrop-brightness-75 bg-white/80
            before:content-[''] before:absolute before:inset-0
            hover:backdrop-blur-lg lg:hover:backdrop-brightness-90
            [&>*]:p-4 [&_a]:text-blue-500 [&_a]:hover:underline
            grid grid-cols-[200px_1fr_2fr] gap-[calc(1rem+2px)]
            min-[320px]:grid-cols-1 min-[768px]:grid-cols-2
            shadow-[0_35px_35px_rgba(0,0,0,0.25)]">
    <h1 class="backdrop-blur-md before:content-[''] [&>*]:p-4
               grid-cols-[200px_1fr] p-[calc(1rem+2px)]
               group-hover:bg-blue-500 shadow-[0_10px_20px_rgba(0,0,0,0.1)]">Test</h1>
</div>
    """
    expected = """
<div class="grid grid-cols-[200px_1fr_2fr] relative gap-[calc(1rem+2px)] m-[clamp(1rem,5vw,3rem)] p-[calc(1rem+2px)] bg-white/80 shadow-[0_35px_35px_rgba(0,0,0,0.25)] backdrop-blur-md backdrop-brightness-75 group min-[320px]:grid-cols-1 min-[768px]:grid-cols-2 lg:hover:backdrop-brightness-90 hover:backdrop-blur-lg [&_a]:hover:underline [&>*]:p-4 [&_a]:text-blue-500 before:absolute before:inset-0 before:content-['']">
    <h1 class="grid-cols-[200px_1fr] p-[calc(1rem+2px)] shadow-[0_10px_20px_rgba(0,0,0,0.1)] backdrop-blur-md group-hover:bg-blue-500 [&>*]:p-4 before:content-['']">Test</h1>
</div>
    """
    result = process_text(html)
    assert result == expected


def test_css_apply_advanced() -> None:
    """Test CSS @apply with advanced features."""
    css = """
.advanced {
    @apply backdrop-blur-md before:content-[''] [&>*]:p-4
           grid-cols-[200px_1fr] p-[calc(1rem+2px)]
           group-hover:bg-blue-500 shadow-[0_10px_20px_rgba(0,0,0,0.1)];
}
#other {
    @apply group relative p-[calc(1rem+2px)] m-[clamp(1rem,5vw,3rem)]
            backdrop-blur-md backdrop-brightness-75 bg-white/80
            before:content-[''] before:absolute before:inset-0
            hover:backdrop-blur-lg lg:hover:backdrop-brightness-90
            [&>*]:p-4 [&_a]:text-blue-500 [&_a]:hover:underline
            grid grid-cols-[200px_1fr_2fr] gap-[calc(1rem+2px)]
            min-[320px]:grid-cols-1 min-[768px]:grid-cols-2
            shadow-[0_35px_35px_rgba(0,0,0,0.25)];
}
    """
    expected = """
.advanced {
    @apply grid-cols-[200px_1fr] p-[calc(1rem+2px)] shadow-[0_10px_20px_rgba(0,0,0,0.1)] backdrop-blur-md group-hover:bg-blue-500 [&>*]:p-4 before:content-[''];
}
#other {
    @apply grid grid-cols-[200px_1fr_2fr] relative gap-[calc(1rem+2px)] m-[clamp(1rem,5vw,3rem)] p-[calc(1rem+2px)] bg-white/80 shadow-[0_35px_35px_rgba(0,0,0,0.25)] backdrop-blur-md backdrop-brightness-75 group min-[320px]:grid-cols-1 min-[768px]:grid-cols-2 lg:hover:backdrop-brightness-90 hover:backdrop-blur-lg [&_a]:hover:underline [&>*]:p-4 [&_a]:text-blue-500 before:absolute before:inset-0 before:content-[''];
}
    """
    result = process_text(css)
    assert result == expected


@pytest.mark.parametrize(
    "html",
    [
        '<div class="p-4 container {{ extra_classes }}"></div>',
        '<div class="{% if not active %}hidden{% endif %} p-4 container"></div>',
        ".container{ @apply p-4 container {{ extra_classes }}; }",
        ".container{ @apply; }",
        ".container{ @apply ; }",
        '<div class=""></div>',
        '<div class=" "></div>',
        "<div class=''></div>",
    ],
)
def test_unprocessed_content(html: str) -> None:
    """Empty classes or classes with Template syntax are not changed."""
    result = process_text(html)
    assert result == html


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            '<div class="p-4 container">{{ title }}</div>',
            '<div class="container p-4">{{ title }}</div>',
        ),
        (
            '{% if not active %}<div class="p-4 container">{{ title }}</div>{% endif %}',
            '{% if not active %}<div class="container p-4">{{ title }}</div>{% endif %}',
        ),
        (
            "{% if css %}.container{ @apply p-4 container; }{% endif %}",
            "{% if css %}.container{ @apply container p-4; }{% endif %}",
        ),
    ],
)
def test_template_markup_outside(html: str, expected: str) -> None:
    """Template syntax is not in the classes, so this is sorted."""
    result = process_text(html)
    assert result == expected


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            '<div class="p-4 container p-4"></div>',
            '<div class="container p-4"></div>',
        ),
        ("@apply p-4 container p-4;", "@apply container p-4;"),
    ],
)
def test_duplicate_classes_are_squashed(html: str, expected: str) -> None:
    """Duplicate classes are squashed."""
    result = process_text(html)
    assert result == expected
