import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

# [link text](https://example.com) — https only; the text is escaped first.
LINK_RE = re.compile(r'\[([^\]\n]{1,200})\]\((https://[^\s)]{1,500})\)')


BOLD_RE = re.compile(r'\*\*([^*\n]{1,300})\*\*')


@register.filter
def inline_links(value):
    """Escape article text, then turn **bold** into <strong> and [text](https://…) into external links."""
    escaped = BOLD_RE.sub(r'<strong>\1</strong>', escape(value))
    return mark_safe(LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', escaped))
