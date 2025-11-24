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
