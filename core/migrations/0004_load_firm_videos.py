"""Load the firm's YouTube videos supplied on 2026-10-23.

Titles are the YouTube titles with hashtags removed and spelling/punctuation
tidied (e.g. الي → إلى، براءه → براءة); the wording is unchanged. Dates and
durations are from YouTube. English titles are left empty until approved
English titles exist. Featured order: most-watched video, then one cassation
explainer and one felony/cassation case, to cover the firm's practice areas.
"""
import datetime

from django.db import migrations

VIDEOS = [
    # (youtube_id, title_ar, description_ar, topic, duration, published, featured position or None)
    ('fQQNIEvokMU', 'طلبات د. محمد الجندي محامي سارة خليفة أمام المحكمة',
     '', 'trials', '17:23', '2025-12-08', 1),
    ('brCba5KkqUg', 'إلى شباب وشيوخ المحامين: النقض الجنائي وكيفية كتابته، والحكم نقض وبراءة',
     '', 'cassation', '7:45', '2026-08-06', 2),
    ('jFEdpD9mcGY', 'نقض وبراءة وإلغاء السجن المؤبد في اتجار بالمواد المخدرة',
     '', 'cassation', '9:07', '2026-08-15', 3),
    ('IhFoeQtS-2E', 'إلى شباب المحامين: استخراج المتهم من محبسه وإجراء تحليل له، نقض وبراءة',
     '', 'procedure', '6:54', '2026-10-06', None),
    ('AbLfixzSnao', 'إلى شباب المحامين: بطلان إجراءات أخذ العينة بمعرفة النيابة، نقض وبراءة',
     '', 'procedure', '5:47', '2026-10-06', None),
    ('mCIm0E7samQ', 'إلى شباب المحامين: مشاهدة سيارة متوقفة وبداخلها أشخاص يستنشقون مخدرات، نقض وبراءة',
     '', 'procedure', '7:05', '2026-09-19', None),
    ('wyxoSroUyH8', 'لا تعقيب على أحكام القضاء ليست قاعدة قانونية، وكفالة حق الدفاع وشرعيته',
     '', 'trials', '7:17', '2026-09-09', None),
    ('kuez5QYNn-A', 'الحكم الصادر ضد سارة خليفة حكم باطل يصل لدرجة الانعدام لبطلان إجراءات المحاكمة',
     'الحكم الصادر ضد سارة خليفة هو حكم باطل يصل لدرجة الانعدام لبطلان إجراءات المحاكمة والإخلال الجسيم بحق الدفاع والخطأ في تطبيق القانون.',
     'trials', '3:48', '2026-09-05', None),
    ('wczSD_28O7I', 'إلى شباب المحامين: الاستيقاف للسيارات وتجاوز استعمال السلطة',
     '', 'procedure', '4:21', '2026-09-04', None),
    ('fGP6JHrO87U', 'النقض الجنائي في جريمة تأليف تشكيل عصابي للاتجار بالمواد المخدرة',
     '', 'cassation', '6:42', '2026-08-08', None),
    ('6UfIU237HTQ', 'د. محمد الجندي محامي سارة خليفة يفجّر مفاجآت مدوية',
     '', 'trials', '5:55', '2025-12-08', None),
    ('huGFERgw_fc', 'د. محمد الجندي يكشف كواليس مثيرة في أولى جلسات محاكمة سارة خليفة',
     'د. محمد الجندي يكشف كواليس مثيرة في أولى جلسات المحاكمة، ومفاجآت بالمستندات والشهادات الرسمية.',
     'trials', '11:06', '2025-09-06', None),
]


def load(apps, schema_editor):
    Video = apps.get_model('core', 'Video')
    for vid, title, desc, topic, duration, published, position in VIDEOS:
        Video.objects.update_or_create(
            youtube_id=vid,
            defaults={
                'youtube_url': f'https://www.youtube.com/watch?v={vid}',
                'title_ar': title,
                'description_ar': desc,
                'topic': topic,
                'duration': duration,
                'published_on': datetime.date.fromisoformat(published),
                'is_published': True,
                'is_featured': position is not None,
                'position': position or 0,
            },
        )


def unload(apps, schema_editor):
    Video = apps.get_model('core', 'Video')
    Video.objects.filter(youtube_id__in=[v[0] for v in VIDEOS]).delete()


class Migration(migrations.Migration):
    dependencies = [('core', '0003_video_topic_duration_featured')]
    operations = [migrations.RunPython(load, unload)]
