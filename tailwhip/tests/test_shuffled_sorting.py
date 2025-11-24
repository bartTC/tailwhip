"""Tests for Tailwind CSS class sorting with randomized input order."""

import random

import pytest

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
    # Shortcuts like 'outline' for 'outline-1' are valid and come first.
    [
        "rounded",
        "rounded-md",
        "border",
        "border-1",
        "-border-rounded-1",
        "border-2",
        "border-rounded-2",
        "ring",
        "ring-8",
        "outline",
        "outline-2",
        "outline-offset-2",
        "-outline-offset-3",
        "outline-rounded",
        "shadow",
        "shadow-lg",
        "blur",
        "blur-sm",
        "grayscale",
        "grayscale-0",
        "invert",
        "invert-0",
        "sepia",
        "sepia-0",
        "drop-shadow",
        "drop-shadow-md",
        "transform",
        "transform-gpu",
        "transition",
        "transition-all",
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
        r"text-xl",
        r"text-black/90",
        r"text-red-400",
        r"text-pretty",
    ],
    # Breakpoints: none -> sm -> md -> lg -> xl -> 2xl
    [
        "p-2",
        "font-light",
        "text-sm",
        "text-gray-600",
        "sm:p-4",
        "sm:font-normal",
        "sm:text-gray-700",
        "sm:text-base",
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
        "hover:bg-red-500",
        "focus:text-black",
        "group-hover:bg-blue-500",
        "peer-checked:bg-green-500",
    ],
    # Border: no-direction before has-direction, value before color
    [
        "border-1",
        "border-red-400",
        "border-t-2",
        "border-t-blue-500",
        "dark:border-1",
        "dark:border-red-400",
        "dark:border-t-2",
        "dark:border-t-blue-500",
        "sm:border-1",
        "sm:border-red-400",
        "sm:border-t-2",
        "sm:border-t-blue-500",
        "focus:border-1",
        "focus:border-red-400",
        "focus:border-t-2",
        "focus:border-t-blue-500",
        "focus:sm:border-1",
        "focus:sm:border-red-400",
        "focus:sm:border-t-2",
        "focus:sm:border-t-blue-500",
        "focus:lg:border-1",
        "focus:lg:border-red-400",
        "focus:lg:border-t-2",
        "focus:lg:border-t-blue-500",
    ],
    # Grid -> Cols -> Rows -> Gap
    [
        "grid",
        "grid-cols-[200px_1fr_2fr]",
        "grid-rows-4",
        "gap-4",
    ],
    # Gradient From -> Via -> To
    [
        "m-4",
        "bg-gradient-to-br",
        "from-pink-500",
        "via-red-500",
        "to-yellow-500",
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
        "[&>*]:p-4",
        "[&_a]:text-blue-500",
        "[&_a]:hover:underline",
    ],
    # Before Before After
    [
        "before:content-['']",
        "before:content-['★']",
        "after:content-['>']",
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
        "flex-row",
        "flex-row-reverse",
        "flex-col",
        "flex-col-reverse",
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
    # Rounded -> size -> orientation -> orientation-size
    [
        "rounded",
        "rounded-xs",
        "rounded-sm",
        "rounded-md",
        "rounded-lg",
        "rounded-xl",
        "rounded-t-sm",
        "rounded-tr-xs",
        "rounded-r-md",
        "rounded-br-md",
        "rounded-b-xs",
        "rounded-bl-xl",
        "rounded-l-sm",
        "rounded-tl-lg",
    ],
    # Interactive variant order: hover -> focus -> focus-visible -> active
    [
        "bg-blue-500",
        "hover:bg-blue-600",
        "focus:bg-blue-700",
        "focus-visible:ring-2",
        "active:bg-blue-800",
    ],
    # Group and peer variants
    [
        "text-gray-500",
        "hover:text-gray-600",
        "group-hover:text-gray-700",
        "group-focus:text-gray-800",
        "peer-hover:text-gray-600",
        "peer-checked:text-green-500",
    ],
    # Text sizes: xs -> sm -> base -> lg -> xl -> 2xl...
    [
        "text-xs",
        "text-sm",
        "text-lg",
        "text-xl",
        "text-2xl",
        "text-3xl",
    ],
    # Blur sizes
    [
        "blur",
        "blur-sm",
        "blur-md",
        "blur-lg",
        "blur-xl",
        "blur-2xl",
        "blur-3xl",
    ],
    # Inset: base -> x -> y -> individual directions
    [
        "inset-0",
        "inset-x-0",
        "inset-y-0",
        "top-0",
        "right-0",
        "bottom-0",
        "left-0",
    ],
    # Divide: no-direction (color) first, then x, then y
    [
        "divide-gray-200",
        "divide-x-2",
        "divide-y-4",
    ],
    # Scroll margin directions
    [
        "scroll-m-4",
        "scroll-mx-4",
        "scroll-my-4",
        "scroll-mt-4",
        "scroll-mr-4",
        "scroll-mb-4",
        "scroll-ml-4",
    ],
    # Complex stacked variants with directions (breakpoints before interactive)
    [
        "border-2",
        "border-t-4",
        "sm:border-2",
        "sm:border-t-4",
        "sm:hover:border-2",
        "sm:hover:border-t-4",
        "lg:hover:border-2",
        "lg:hover:border-t-4",
        "hover:border-2",
        "hover:border-t-4",
    ],
    # Opacity with alpha values
    [
        "bg-black/0",
        "bg-black/25",
        "bg-black/50",
        "bg-black/75",
        "bg-black/100",
    ],
    # Color shades ordering (alphabetical colors, numeric shades)
    [
        "text-blue-50",
        "text-blue-500",
        "text-blue-950",
        "text-red-50",
        "text-red-500",
        "text-red-950",
    ],
    # Ring utilities
    [
        "ring",
        "ring-1",
        "ring-2",
        "ring-blue-500",
        "ring-offset-2",
        "ring-offset-blue-500",
    ],
    # Z-index ordering
    [
        "z-0",
        "z-10",
        "z-20",
        "z-50",
    ],
    # Translate with directions
    [
        "translate-x-0",
        "translate-x-4",
        "translate-y-0",
        "translate-y-4",
    ],
    # Scale utilities
    [
        "scale-0",
        "scale-50",
        "scale-100",
        "scale-x-50",
        "scale-y-50",
    ],
    # Rotate utilities (suffix values sort alphabetically)
    [
        "rotate-0",
        "rotate-180",
        "rotate-45",
        "rotate-90",
    ],
    # Animation and transition (suffix values sort alphabetically)
    [
        "transition",
        "transition-all",
        "duration-100",
        "duration-200",
        "duration-300",
        "ease-in",
        "ease-out",
        "delay-100",
        "delay-200",
        "animate-ping",
        "animate-spin",
    ],
    # Cursor utilities (suffix values sort alphabetically)
    [
        "cursor-auto",
        "cursor-not-allowed",
        "cursor-pointer",
        "cursor-wait",
    ],
    # Overflow combinations
    [
        "overflow-auto",
        "overflow-hidden",
        "overflow-x-auto",
        "overflow-y-hidden",
    ],
    # Object fit and position (suffix values sort alphabetically)
    [
        "object-center",
        "object-contain",
        "object-cover",
        "object-top",
    ],
    # Important modifier (! sorts before non-!)
    [
        "!m-0",
        "m-4",
        "!p-0",
        "p-4",
    ],
    # Aria variants
    [
        "bg-gray-100",
        "aria-checked:bg-blue-500",
        "aria-disabled:opacity-50",
        "aria-expanded:rotate-180",
    ],
    # Data variants
    [
        "text-gray-500",
        "data-active:text-blue-500",
        "data-disabled:opacity-50",
    ],
    # Print variant
    [
        "block",
        "print:hidden",
    ],
    # Motion variants
    [
        "transition-transform",
        "motion-safe:transition-all",
        "motion-reduce:transition-none",
    ],
    # Contrast variants
    [
        "text-gray-600",
        "contrast-more:text-gray-900",
        "contrast-less:text-gray-400",
    ],
    # Placeholder styling
    [
        "text-gray-900",
        "placeholder:text-gray-400",
        "placeholder:italic",
    ],
    # Selection styling (within selection: variant, text before bg by prefix order)
    [
        "text-black",
        "selection:text-white",
        "selection:bg-blue-500",
    ],
    # File input styling (within file: variant, sorted by prefix order)
    [
        "text-sm",
        "file:mr-4",
        "file:text-white",
        "file:bg-blue-500",
        "file:rounded",
        "file:border-0",
    ],
    # Marker styling for lists
    [
        "list-disc",
        "marker:text-blue-500",
    ],
    # First-letter and first-line (font before text by prefix order)
    [
        "text-base",
        "first-letter:font-bold",
        "first-letter:text-4xl",
        "first-line:uppercase",
    ],
    # Backdrop pseudo-element
    [
        "bg-white",
        "backdrop:bg-black/50",
    ],
    # Complex real-world button (sorted by prefix order within each variant group)
    [
        "inline-flex",
        "gap-2",
        "items-center",
        "justify-center",
        "px-4",
        "py-2",
        "font-medium",
        "text-sm",
        "text-white",
        "bg-blue-500",
        "rounded-lg",
        "shadow-sm",
        "transition-colors",
        "duration-200",
        "disabled:opacity-50",
        "disabled:cursor-not-allowed",
        "hover:bg-blue-600",
        "focus:ring-2",
        "focus:ring-blue-500",
        "focus:ring-offset-2",
        "focus:outline-none",
    ],
    # Complex real-world card (hover: border before shadow by prefix order)
    [
        "relative",
        "flex",
        "flex-col",
        "gap-4",
        "p-6",
        "bg-white",
        "rounded-xl",
        "border",
        "border-gray-200",
        "shadow-lg",
        "dark:bg-gray-800",
        "dark:border-gray-700",
        "hover:border-gray-300",
        "hover:shadow-xl",
    ],
    # Complex real-world input (sorted by variant order then prefix order)
    [
        "block",
        "w-full",
        "px-3",
        "py-2",
        "text-sm",
        "text-gray-900",
        "bg-white",
        "rounded-md",
        "border",
        "border-gray-300",
        "shadow-sm",
        "disabled:text-gray-500",
        "disabled:bg-gray-50",
        "focus:border-blue-500",
        "focus:ring-1",
        "focus:ring-blue-500",
        "focus:outline-none",
        "placeholder:text-gray-400",
    ],
    # Logical properties (start/end)
    [
        "ms-4",
        "me-4",
        "ps-4",
        "pe-4",
    ],
    # Line clamp
    [
        "line-clamp-1",
        "line-clamp-2",
        "line-clamp-3",
    ],
    # Columns
    [
        "columns-1",
        "columns-2",
        "columns-3",
    ],
    # Aspect ratio
    [
        "aspect-auto",
        "aspect-square",
        "aspect-video",
    ],
    # Break utilities
    [
        "break-inside-auto",
        "break-inside-avoid",
        "break-before-auto",
        "break-after-auto",
    ],
    # Will-change (suffix values sort alphabetically)
    [
        "will-change-auto",
        "will-change-contents",
        "will-change-scroll",
        "will-change-transform",
    ],
    # Touch action (suffix values sort alphabetically)
    [
        "touch-auto",
        "touch-manipulation",
        "touch-none",
    ],
    # Accent color (colors before "auto" suffix alphabetically)
    [
        "accent-blue-500",
        "accent-pink-500",
        "accent-auto",
    ],
    # Caret color
    [
        "caret-black",
        "caret-blue-500",
        "caret-transparent",
    ],
    # Scroll snap (suffix values sort alphabetically)
    [
        "snap-center",
        "snap-end",
        "snap-start",
        "snap-x",
        "snap-y",
    ],
    # Scroll padding
    [
        "scroll-p-4",
        "scroll-px-4",
        "scroll-py-4",
        "scroll-pt-4",
        "scroll-pb-4",
    ],
    # Hyphens (suffix values sort alphabetically)
    [
        "hyphens-auto",
        "hyphens-manual",
        "hyphens-none",
    ],
    # Whitespace
    [
        "whitespace-normal",
        "whitespace-nowrap",
        "whitespace-pre",
    ],
    # Word break
    [
        "break-words",
        "break-all",
        "break-keep",
    ],
    # Text decoration (decoration suffix values sort alphabetically)
    [
        "underline",
        "overline",
        "line-through",
        "no-underline",
        "decoration-double",
        "decoration-solid",
    ],
    # Font variant numeric
    [
        "tabular-nums",
        "slashed-zero",
        "lining-nums",
        "oldstyle-nums",
    ],
    # SVG utilities (stroke values before colors, fill colors alphabetically)
    [
        "stroke-1",
        "stroke-2",
        "stroke-black",
        "fill-blue-500",
        "fill-current",
    ],
    # Screen reader utilities
    [
        "sr-only",
        "not-sr-only",
    ],
)


@pytest.mark.parametrize("classes", CLASS_GROUPS)
def test_sorting(classes: list[str]) -> None:
    """
    Test sorting of classes.

    The classes in the parameter are in the correct order. We shuffle them before
    we do the comparison. To mitigate randomness, we run the test multiple times.
    """
    result = sort_classes(shuffle(classes))
    assert result == classes
