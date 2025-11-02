# Tailwhip — Tailwind CSS class sorter

Tailwhip is a pure Python Tailwind CSS class sorter that works with any HTML or CSS 
file — including Django templates and other templating languages.

## Why Tailwhip?

The [official Prettier plugin][1] for sorting Tailwind classes doesn’t play well 
with many template languages, such as Django. While there are Prettier plugins that 
add limited support for [Jinja templates][2], they often require configuration 
workarounds or restrict what you can do with Prettier.

Tailwhip takes a more pragmatic approach. Instead of trying to parse and understand 
every possible template syntax, it focuses on sorting Tailwind classes reliably.

[1]: https://github.com/tailwindlabs/prettier-plugin-tailwindcss
[2]: https://github.com/davidodenwald/prettier-plugin-jinja-template

How it works:

1.	It finds all `class=""` attributes and `@apply` directives in the given files.
2.	It sorts the contained classes according to the official Tailwind CSS class order.
3.	If a class attribute contains template syntax (e.g., `{{ ... }}` or `{% ... %}`), 
    Tailwhip leaves it untouched.

This approach ensures Tailwhip works across diverse environments — Django, Flask, 
Jinja2, or even custom templating engines — without breaking your templates or 
requiring complicated setup.
