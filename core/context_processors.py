import re

from django.conf import settings
from django.urls import reverse, translate_url
from django.utils.translation import get_language

from .content import BUILT_PAGES, PAGES, get_content


def map_embed_url(coords, lang):
    """Google Maps embed URL for 'lat,lng' (no API key needed), or '' if not set or malformed."""
    match = re.fullmatch(r'\s*(-?\d{1,3}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*', coords or '')
    if not match:
        return ''
    return f'https://maps.google.com/maps?q={match.group(1)},{match.group(2)}&z=17&hl={lang}&output=embed'


def asset_version():
    """Changes whenever the stylesheet or script changes, so browsers fetch the new copy."""
    static = settings.BASE_DIR / 'static'
    return str(int(max((static / f).stat().st_mtime for f in ('css/style.css', 'js/main.js'))))


def site(request):
    """Language, interface text and firm details shared by every template."""
    lang = (get_language() or settings.LANGUAGE_CODE)[:2]
    if lang not in ('ar', 'en'):
        lang = 'ar'
    alt_lang = 'en' if lang == 'ar' else 'ar'
    t = get_content(lang)

    firm_cfg = settings.FIRM
    whatsapp_digits = re.sub(r'\D', '', firm_cfg.get('whatsapp_number', ''))
    firm = {
        'phone': firm_cfg.get('phone'),
        'office_phone': firm_cfg.get('office_phone', ''),
        'email': firm_cfg.get('email'),
        'address': firm_cfg.get(f'address_{lang}'),
        'hours': firm_cfg.get(f'hours_{lang}'),
        'maps_url': firm_cfg.get('maps_url'),
        'google_business_url': firm_cfg.get('google_business_url', ''),
        'map_embed_url': map_embed_url(firm_cfg.get('map_coords', ''), lang),
        'whatsapp_url': f'https://wa.me/{whatsapp_digits}' if whatsapp_digits else '',
        'whatsapp_display': f'+{whatsapp_digits}' if whatsapp_digits else '',
    }

    path = request.get_full_path()
    site_url = firm_cfg.get('site_url', '').rstrip('/')
    alternates = {}
    if site_url:
        for code, _ in settings.LANGUAGES:
            alternates[code] = site_url + translate_url(request.path, code)

    match = getattr(request, 'resolver_match', None)
    current = match.url_name if match and match.namespace == 'core' else ''
    nav = [
        {
            'key': key,
            'label': t['nav'][key],
            'url': reverse(f'core:{key}'),
            'built': key in BUILT_PAGES,
            'active': key == current,
        }
        for key in PAGES
    ]

    social = [
        {'key': key, 'label': t['social'][key], 'url': url}
        for key, url in settings.FIRM_SOCIAL
        if url
    ]

    return {
        'lang': lang,
        'nav': nav,
        'social': social,
        'youtube_url': next((s['url'] for s in social if s['key'] == 'youtube'), ''),
        'dir': 'rtl' if lang == 'ar' else 'ltr',
        'alt_lang': alt_lang,
        'alt_lang_url': translate_url(path, alt_lang),
        't': t,
        'firm': firm,
        'built_pages': BUILT_PAGES,
        'canonical_url': alternates.get(lang, ''),
        'alternates': alternates,
        'static_export': settings.STATIC_EXPORT,
        'asset_version': asset_version(),
    }
