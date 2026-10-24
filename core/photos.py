"""Photo slots on the site. Each slot shows, in order: the photo uploaded in the
admin ("Site photos"), else the static file at its path, else a marked placeholder."""
from django.contrib.staticfiles import finders
from django.templatetags.static import static

# key: (label, static fallback, recommended width, height)
SLOTS = {
    'home_portrait': ('Home — hero portrait of Dr. Elgindi', 'images/photos/lawyer.jpg', 1200, 1500),
    'home_office': ('Home — "About the firm" office photo', 'images/photos/office.jpg', 1500, 1200),
    'about_hero': ('About — hero background', 'images/about/hero.jpg', 1600, 1000),
    'about_office': ('About — 01 About the firm', 'images/about/office.jpg', 1200, 750),
    'about_practice': ('About — 02 Practice areas', 'images/about/practice.jpg', 1200, 750),
    'about_team': ('About — 03 Our team', 'images/about/team.jpg', 1200, 750),
    'about_values': ('About — 04 Our principles', 'images/about/values.jpg', 1200, 750),
    'about_cta': ('About — 05 Consultation', 'images/about/cta.jpg', 1200, 750),
}


def site_photos(lang):
    """{slot: {'url': str or '', 'alt': str}} for every slot."""
    from .models import SitePhoto
    uploaded = {p.slot: p for p in SitePhoto.objects.exclude(image='')}
    result = {}
    for key, (_, static_path, _, _) in SLOTS.items():
        photo = uploaded.get(key)
        if photo:
            result[key] = {'url': photo.image.url, 'alt': photo.alt_en if lang == 'en' and photo.alt_en else photo.alt_ar}
        else:
            result[key] = {'url': static(static_path) if finders.find(static_path) else '', 'alt': ''}
    return result
