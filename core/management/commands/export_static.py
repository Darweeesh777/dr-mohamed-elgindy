"""Export the public site as static files for a static host (Cloudflare).

Run with STATIC_EXPORT=1 so the consultation form becomes direct-contact links:
    STATIC_EXPORT=1 python manage.py export_static
Pages are found by following internal links from /ar/ and /en/, and written as
<path>/index.html. Static assets and uploaded photos are copied alongside.
"""

import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

LINK = re.compile(r'href="(/(?:ar|en)/[^"#?]*)')


class Command(BaseCommand):
    help = 'Export the public pages, static assets and site photos to a folder.'

    def add_arguments(self, parser):
        parser.add_argument('--out', default=str(settings.BASE_DIR / 'site'))

    def handle(self, *args, **options):
        if not settings.STATIC_EXPORT:
            raise CommandError('Set STATIC_EXPORT=1 so the form is replaced by direct contact links.')
        out = Path(options['out'])
        if out.exists():
            shutil.rmtree(out)
        out.mkdir(parents=True)

        client = Client(HTTP_HOST='localhost')
        queue, seen = ['/ar/', '/en/'], set()
        while queue:
            path = queue.pop()
            if path in seen:
                continue
            seen.add(path)
            response = client.get(path)
            if response.status_code != 200:
                raise CommandError(f'{path} returned {response.status_code}')
            html = response.content.decode('utf-8')
            target = out / path.strip('/') / 'index.html'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding='utf-8')
            queue.extend(link for link in LINK.findall(html) if link not in seen)

        # The bare domain opens the Arabic site, as on the Django version.
        (out / 'index.html').write_text(
            '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/ar/">'
            '<link rel="canonical" href="/ar/"><a href="/ar/">/ar/</a>', encoding='utf-8')

        shutil.copytree(settings.BASE_DIR / 'static', out / 'static')
        if Path(settings.MEDIA_ROOT).exists():
            shutil.copytree(settings.MEDIA_ROOT, out / 'media')
        self.stdout.write(self.style.SUCCESS(f'Exported {len(seen)} pages to {out}'))
