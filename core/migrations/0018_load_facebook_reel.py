"""Load the firm's first Facebook reel (title supplied by the firm)."""

import datetime

from django.db import migrations

REEL_URL = 'https://www.facebook.com/reel/1629105785578255'


def load(apps, schema_editor):
    Video = apps.get_model('core', 'Video')
    if Video.objects.filter(facebook_url=REEL_URL).exists():
        return
    Video.objects.create(
        title_ar='الي شباب المحامين استخراج المتهم من محبسه وإجراء تحليل له نقض وبراءه',
        facebook_url=REEL_URL,
        published_on=datetime.date(2026, 10, 25),
    )


def unload(apps, schema_editor):
    apps.get_model('core', 'Video').objects.filter(facebook_url=REEL_URL).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0017_video_facebook_link')]
    operations = [migrations.RunPython(load, unload)]
