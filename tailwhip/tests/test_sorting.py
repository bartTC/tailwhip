"""
Tests for Tailwind CSS class sorting.

These tests verify that the sorting algorithm correctly orders classes
based on the component_order configuration and individual component lists.
"""

from __future__ import annotations

from tailwhip.configuration import update_configuration
from tailwhip.process import process_text
from tailwhip.sorting import parse_class, sort_classes

# =============================================================================
# Parsing Tests
# =============================================================================


class TestParseClass:
    """Tests for the parse_class function."""

    def test_simple_prefix(self) -> None:
        """Simple utility with just a prefix."""
        result = parse_class("flex")
        assert result.prefix == "flex"
        assert result.variants == []
        assert result.important is False
        assert result.negated is False

    def test_prefix_with_value(self) -> None:
        """Utility with prefix and numeric value."""
        result = parse_class("p-4")
        assert result.prefix == "p"
        assert result.value == "4"

    def test_prefix_with_direction(self) -> None:
        """Utility with prefix and direction."""
        result = parse_class("border-t")
        assert result.prefix == "border"
        assert result.direction == "t"

    def test_prefix_with_direction_and_value(self) -> None:
        """Utility with prefix, direction, and value."""
        result = parse_class("border-t-2")
        assert result.prefix == "border"
        assert result.direction == "t"
        assert result.value == "2"

    def test_prefix_with_color_and_shade(self) -> None:
        """Utility with color and shade."""
        result = parse_class("text-red-500")
        assert result.prefix == "text"
        assert result.color == "red"
        assert result.shade == "500"

    def test_prefix_with_direction_color_shade(self) -> None:
        """Utility with direction, color, and shade."""
        result = parse_class("border-t-red-500")
        assert result.prefix == "border"
        assert result.direction == "t"
        assert result.color == "red"
        assert result.shade == "500"

    def test_alpha_value(self) -> None:
        """Utility with alpha opacity value."""
        result = parse_class("bg-red-500/50")
        assert result.prefix == "bg"
        assert result.color == "red"
        assert result.shade == "500"
        assert result.alpha == "50"

    def test_important_prefix(self) -> None:
        """Important utility with ! prefix."""
        result = parse_class("!mt-4")
        assert result.important is True
        assert result.prefix == "mt"
        assert result.value == "4"

    def test_negated_value(self) -> None:
        """Negated utility with - prefix."""
        result = parse_class("-mt-4")
        assert result.negated is True
        assert result.prefix == "mt"
        assert result.value == "4"

    def test_important_and_negated(self) -> None:
        """Both important and negated."""
        result = parse_class("!-mt-4")
        assert result.important is True
        assert result.negated is True
        assert result.prefix == "mt"
        assert result.value == "4"

    def test_single_variant(self) -> None:
        """Utility with a single variant."""
        result = parse_class("hover:bg-red-500")
        assert result.variants == ["hover"]
        assert result.prefix == "bg"
        assert result.color == "red"
        assert result.shade == "500"

    def test_multiple_variants(self) -> None:
        """Utility with multiple stacked variants."""
        result = parse_class("sm:hover:focus:bg-red-500")
        assert result.variants == ["sm", "hover", "focus"]
        assert result.prefix == "bg"
        assert result.color == "red"

    def test_compound_prefix(self) -> None:
        """Compound prefix like inline-flex."""
        result = parse_class("inline-flex")
        assert result.prefix == "inline-flex"

    def test_arbitrary_value(self) -> None:
        """Arbitrary value in brackets."""
        result = parse_class("w-[100px]")
        assert result.prefix == "w"
        assert result.suffix == "[100px]"

    def test_size_modifier(self) -> None:
        """Size modifier like text-xl."""
        result = parse_class("text-xl")
        assert result.prefix == "text"
        assert result.size == "xl"

    def test_size_with_direction(self) -> None:
        """Size with direction like rounded-t-lg."""
        result = parse_class("rounded-t-lg")
        assert result.prefix == "rounded"
        assert result.direction == "t"
        assert result.size == "lg"


# =============================================================================
# Sorting Tests - Component Order
# =============================================================================


class TestSortingByVariant:
    """Tests for variant-based sorting."""

    def test_no_variant_before_variant(self) -> None:
        """Classes without variants come before classes with variants."""
        result = sort_classes(["hover:p-4", "p-4"])
        assert result == ["p-4", "hover:p-4"]

    def test_variant_order_breakpoints(self) -> None:
        """Breakpoint variants are ordered sm -> md -> lg -> xl."""
        result = sort_classes(["xl:p-4", "sm:p-4", "lg:p-4", "md:p-4"])
        assert result == ["sm:p-4", "md:p-4", "lg:p-4", "xl:p-4"]

    def test_variant_order_dark_before_breakpoints(self) -> None:
        """Dark mode comes before breakpoints."""
        result = sort_classes(["sm:p-4", "dark:p-4"])
        assert result == ["dark:p-4", "sm:p-4"]

    def test_variant_order_interactive(self) -> None:
        """Interactive variants are ordered hover -> focus -> active."""
        result = sort_classes(["active:p-4", "hover:p-4", "focus:p-4"])
        assert result == ["hover:p-4", "focus:p-4", "active:p-4"]

    def test_stacked_variants(self) -> None:
        """Stacked variants are compared element by element."""
        result = sort_classes(["lg:hover:p-4", "sm:hover:p-4"])
        assert result == ["sm:hover:p-4", "lg:hover:p-4"]


class TestSortingByPrefix:
    """Tests for prefix-based sorting."""

    def test_layout_before_spacing(self) -> None:
        """Layout utilities come before spacing."""
        result = sort_classes(["p-4", "flex"])
        assert result == ["flex", "p-4"]

    def test_container_first(self) -> None:
        """Container is always first."""
        result = sort_classes(["p-4", "flex", "container"])
        assert result == ["container", "flex", "p-4"]

    def test_margin_before_padding(self) -> None:
        """Margin comes before padding."""
        result = sort_classes(["p-4", "m-4"])
        assert result == ["m-4", "p-4"]

    def test_prefix_alphabetical_for_unknown(self) -> None:
        """Unknown prefixes are sorted alphabetically."""
        result = sort_classes(["zzz-custom", "aaa-custom"])
        assert result == ["aaa-custom", "zzz-custom"]


class TestSortingByDirection:
    """Tests for direction-based sorting."""

    def test_no_direction_first(self) -> None:
        """No direction comes before directional variants."""
        result = sort_classes(["border-t", "border"])
        assert result == ["border", "border-t"]

    def test_direction_order(self) -> None:
        """Directions follow the configured order: x, y, t, r, b, l."""
        result = sort_classes(["border-l", "border-t", "border-y", "border-x"])
        assert result == ["border-x", "border-y", "border-t", "border-l"]

    def test_direction_with_values(self) -> None:
        """Direction sorting works with values."""
        result = sort_classes(["border-b-2", "border-t-2"])
        assert result == ["border-t-2", "border-b-2"]


class TestSortingBySize:
    """Tests for size-based sorting."""

    def test_size_order(self) -> None:
        """Sizes follow the configured order: xs, sm, md, lg, xl, etc."""
        result = sort_classes(["text-xl", "text-sm", "text-lg", "text-xs"])
        assert result == ["text-xs", "text-sm", "text-lg", "text-xl"]

    def test_no_size_before_size(self) -> None:
        """No size comes before sized variants."""
        result = sort_classes(["blur-sm", "blur"])
        assert result == ["blur", "blur-sm"]

    def test_size_with_direction(self) -> None:
        """Size sorting works with direction."""
        result = sort_classes(["rounded-t-xl", "rounded-t-sm"])
        assert result == ["rounded-t-sm", "rounded-t-xl"]


class TestSortingByValue:
    """Tests for value-based sorting."""

    def test_numeric_value_order(self) -> None:
        """Numeric values follow configured order."""
        result = sort_classes(["p-8", "p-2", "p-4"])
        assert result == ["p-2", "p-4", "p-8"]

    def test_zero_first(self) -> None:
        """Zero comes first."""
        result = sort_classes(["m-4", "m-0"])
        assert result == ["m-0", "m-4"]


class TestSortingByColor:
    """Tests for color-based sorting."""

    def test_no_color_before_color(self) -> None:
        """Non-color utilities come before color utilities."""
        result = sort_classes(["text-red-500", "text-xl"])
        assert result == ["text-xl", "text-red-500"]

    def test_color_order(self) -> None:
        """Colors follow configured order."""
        result = sort_classes(["bg-blue-500", "bg-red-500", "bg-gray-500"])
        assert result == ["bg-gray-500", "bg-red-500", "bg-blue-500"]

    def test_black_white_first(self) -> None:
        """Black and white come early in color order."""
        result = sort_classes(["text-red-500", "text-black", "text-white"])
        assert result == ["text-black", "text-white", "text-red-500"]


class TestSortingByShade:
    """Tests for shade-based sorting."""

    def test_shade_order(self) -> None:
        """Shades follow numeric order 50 -> 100 -> ... -> 950."""
        result = sort_classes(["bg-red-700", "bg-red-300", "bg-red-500"])
        assert result == ["bg-red-300", "bg-red-500", "bg-red-700"]


class TestSortingByAlpha:
    """Tests for alpha-based sorting."""

    def test_alpha_before_no_alpha(self) -> None:
        """Alpha variants come before no-alpha (consistent with other components)."""
        result = sort_classes(["bg-red-500/50", "bg-red-500"])
        assert result == ["bg-red-500/50", "bg-red-500"]

    def test_alpha_order(self) -> None:
        """Alpha values are ordered numerically."""
        result = sort_classes(["bg-red-500/75", "bg-red-500/25", "bg-red-500/50"])
        assert result == ["bg-red-500/25", "bg-red-500/50", "bg-red-500/75"]


# =============================================================================
# Sorting Tests - Special Cases
# =============================================================================


class TestNegatedClasses:
    """Tests for negated class handling."""

    def test_negated_stays_with_group(self) -> None:
        """Negated classes stay with their non-negated siblings."""
        result = sort_classes(["mx-4", "-mx-2", "my-4"])
        # -mx-2 should be near mx-4, not separated
        assert result.index("-mx-2") < result.index("my-4")

    def test_negated_margin_order(self) -> None:
        """Negated margins maintain proper order."""
        result = sort_classes(["-mb-4", "mt-4", "-ml-4"])
        assert result in (["mt-4", "-mb-4", "-ml-4"],)


class TestImportantClasses:
    """Tests for important class handling."""

    def test_important_stays_with_group(self) -> None:
        """Important classes stay with their non-important siblings."""
        result = sort_classes(["!mt-4", "mt-4", "p-4"])
        # Both mt-4 variants should come before p-4
        mt_indices = [result.index("!mt-4"), result.index("mt-4")]
        p_index = result.index("p-4")
        assert all(i < p_index for i in mt_indices)


class TestDeduplication:
    """Tests for duplicate class handling."""

    def test_duplicates_removed(self) -> None:
        """Duplicate classes are removed."""
        result = sort_classes(["p-4", "p-4", "p-4"])
        assert result == ["p-4"]

    def test_first_occurrence_kept(self) -> None:
        """First occurrence of duplicate is kept."""
        result = sort_classes(["p-4", "flex", "p-4"])
        assert result == ["flex", "p-4"]


class TestArbitraryValues:
    """Tests for arbitrary value handling."""

    def test_arbitrary_width(self) -> None:
        """Arbitrary width values are handled."""
        result = sort_classes(["w-[100px]", "w-4"])
        # Known value should come before arbitrary
        assert result == ["w-4", "w-[100px]"]

    def test_arbitrary_grid(self) -> None:
        """Arbitrary grid values are handled."""
        result = sort_classes(["grid-cols-[200px_1fr]", "grid-cols-2"])
        assert result == ["grid-cols-2", "grid-cols-[200px_1fr]"]


# =============================================================================
# Integration Tests
# =============================================================================


class TestProcessText:
    """Tests for full text processing."""

    def test_html_class_attribute(self) -> None:
        """HTML class attributes are sorted."""
        html = '<div class="p-4 flex container"></div>'
        expected = '<div class="container flex p-4"></div>'
        assert process_text(html) == expected

    def test_css_apply(self) -> None:
        """CSS @apply directives are sorted."""
        css = "@apply p-4 flex container;"
        expected = "@apply container flex p-4;"
        assert process_text(css) == expected

    def test_template_expressions_skipped(self) -> None:
        """Template expressions are not modified."""
        html = '<div class="p-4 container {{ extra }}"></div>'
        assert process_text(html) == html

    def test_empty_class_unchanged(self) -> None:
        """Empty class attributes are unchanged."""
        html = '<div class=""></div>'
        assert process_text(html) == html


class TestCustomColors:
    """Tests for custom color configuration."""

    def test_custom_colors_recognized(self) -> None:
        """Custom colors are recognized and sorted."""
        update_configuration({"custom_colors": ["brand", "accent"]})

        result = sort_classes(["text-brand", "text-red-500"])
        # Custom colors should be sorted after built-in colors
        assert result == ["text-red-500", "text-brand"]


# =============================================================================
# Real-World Examples
# =============================================================================


class TestRealWorldExamples:
    """Tests with realistic class combinations."""

    def test_button_classes(self) -> None:
        """Typical button styling classes."""
        classes = [
            "hover:bg-blue-600",
            "text-white",
            "font-bold",
            "py-2",
            "px-4",
            "rounded",
            "bg-blue-500",
        ]
        result = sort_classes(classes)
        # Spacing before typography, bg before rounded (by prefix order)
        assert result.index("py-2") < result.index("font-bold")
        assert result.index("bg-blue-500") < result.index("rounded")
        assert result.index("bg-blue-500") < result.index("hover:bg-blue-600")

    def test_card_classes(self) -> None:
        """Typical card component classes."""
        classes = [
            "shadow-lg",
            "p-6",
            "bg-white",
            "rounded-lg",
            "max-w-sm",
            "mx-auto",
        ]
        result = sort_classes(classes)
        # Sizing before spacing before effects
        assert result.index("max-w-sm") < result.index("mx-auto")
        assert result.index("p-6") < result.index("bg-white")

    def test_responsive_text(self) -> None:
        """Responsive text sizing."""
        classes = [
            "lg:text-xl",
            "text-base",
            "md:text-lg",
            "sm:text-sm",
        ]
        result = sort_classes(classes)
        assert result == ["text-base", "sm:text-sm", "md:text-lg", "lg:text-xl"]
