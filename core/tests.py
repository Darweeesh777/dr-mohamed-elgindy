import re

from django.test import TestCase, override_settings

import datetime

from django.core.exceptions import ValidationError

from .models import ConsultationRequest, Video, extract_youtube_id

VALID = {
    'request_type': 'consultation',
    'full_name': '  أحمد   علي ',
    'phone': '+20 100 000 0000',
    'email': '',
    'preferred_contact': 'whatsapp',
    'matter': 'criminal',
    'message': '',
    'consent': 'on',
    'website': '',
}


class PageTests(TestCase):
    def test_root_redirects_to_language_prefix(self):
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ar')
        self.assertRedirects(response, '/ar/', fetch_redirect_response=False)

    def test_arabic_home_is_rtl(self):
        response = self.client.get('/ar/')
        self.assertContains(response, '<html lang="ar" dir="rtl">')
        self.assertContains(response, 'اطلب استشارة قانونية')
        self.assertContains(response, 'href="/en/"')

    def test_english_home_is_ltr(self):
        response = self.client.get('/en/')
        self.assertContains(response, '<html lang="en" dir="ltr">')
        self.assertContains(response, 'Request a Legal Consultation')
        self.assertContains(response, 'href="/ar/"')

    def test_unbuilt_pages_are_marked_and_not_indexed(self):
        for lang in ('ar', 'en'):
            for page in ():
                response = self.client.get(f'/{lang}/{page}/')
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'name="robots" content="noindex"')

    def test_language_switch_keeps_the_page(self):
        response = self.client.get('/ar/videos/')
        self.assertContains(response, 'href="/en/videos/"')

    def test_request_type_preselected_from_query(self):
        response = self.client.get('/ar/?type=appointment')
        inputs = re.findall(r'<input[^>]*name="request_type"[^>]*>', response.content.decode())
        checked = [tag for tag in inputs if ' checked' in tag]
        self.assertEqual(len(checked), 1)
        self.assertIn('value="appointment"', checked[0])

    @override_settings(FIRM={'site_url': ''})
    def test_missing_contact_details_show_placeholders(self):
        response = self.client.get('/en/')
        self.assertContains(response, 'WhatsApp number to be added')
        self.assertNotContains(response, 'wa.me')

    def test_social_links_open_in_new_tab(self):
        response = self.client.get('/ar/')
        for url in ('https://www.facebook.com/share/1BzhYdzhTy/',
                    'https://www.tiktok.com/@dr.mohamedelgandy',
                    'https://www.youtube.com/@drmohamedelgendy'):
            self.assertContains(response, f'href="{url}" target="_blank" rel="noopener"')
        self.assertContains(response, 'شاهد على يوتيوب')
        self.assertNotContains(response, 'تُضاف الروابط بعد اعتمادها')

    @override_settings(FIRM_SOCIAL=[('facebook', ''), ('tiktok', ''), ('youtube', '')])
    def test_social_placeholder_when_no_accounts(self):
        response = self.client.get('/en/')
        self.assertContains(response, 'Links will be added once approved')
        self.assertNotContains(response, 'Watch on YouTube')

    @override_settings(FIRM={'whatsapp_number': '+20 123 456 7890', 'site_url': ''})
    def test_whatsapp_link_uses_configured_number(self):
        response = self.client.get('/en/')
        self.assertContains(response, 'href="https://wa.me/201234567890"')


class ConsultationFormTests(TestCase):
    def test_valid_submission_is_saved(self):
        response = self.client.post('/ar/', VALID)
        self.assertRedirects(response, '/ar/#consultation', fetch_redirect_response=False)
        request = ConsultationRequest.objects.get()
        self.assertEqual(request.full_name, 'أحمد علي')
        self.assertEqual(request.language, 'ar')

    def test_success_message_shown_after_redirect(self):
        response = self.client.post('/en/', VALID, follow=True)
        self.assertContains(response, 'Your request has been recorded.')

    def test_invalid_phone_is_rejected_in_page_language(self):
        response = self.client.post('/ar/', {**VALID, 'phone': 'abc'})
        self.assertEqual(ConsultationRequest.objects.count(), 0)
        self.assertContains(response, 'يُرجى إدخال رقم هاتف صحيح.')
        self.assertContains(response, 'aria-invalid="true"')

    def test_required_fields_use_django_arabic_messages(self):
        response = self.client.post('/ar/', {**VALID, 'full_name': '', 'consent': ''})
        self.assertContains(response, 'هذا الحقل مطلوب')

    def test_email_required_when_preferred(self):
        response = self.client.post('/en/', {**VALID, 'preferred_contact': 'email'})
        self.assertContains(response, 'Please enter your email address')
        self.assertEqual(ConsultationRequest.objects.count(), 0)

    def test_honeypot_blocks_bots(self):
        self.client.post('/en/', {**VALID, 'website': 'http://spam.example'})
        self.assertEqual(ConsultationRequest.objects.count(), 0)

    def test_csrf_is_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        response = client.post('/en/', VALID)
        self.assertEqual(response.status_code, 403)


class FirmVideosTests(TestCase):
    """The firm's videos loaded by migration 0004."""

    def test_twelve_videos_loaded(self):
        self.assertEqual(Video.objects.filter(is_published=True).count(), 12)

    def test_home_shows_the_three_featured_videos_in_order(self):
        content = self.client.get('/ar/').content.decode()
        ids = re.findall(r'data-youtube-id="([^"]+)"', content)
        self.assertEqual(ids, ['fQQNIEvokMU', 'brCba5KkqUg', 'jFEdpD9mcGY'])

    def test_videos_page_spotlight_and_grid(self):
        content = self.client.get('/ar/videos/').content.decode()
        ids = re.findall(r'data-youtube-id="([^"]+)"', content)
        self.assertEqual(ids[0], 'fQQNIEvokMU')          # spotlight first
        self.assertEqual(len(ids), 12)                     # spotlight + 11, no duplicates
        self.assertEqual(len(set(ids)), 12)
        self.assertIn('فيديو مميز', content)

    def test_topic_filter(self):
        content = self.client.get('/ar/videos/?topic=cassation').content.decode()
        ids = re.findall(r'data-youtube-id="([^"]+)"', content)
        self.assertEqual(sorted(ids), sorted(['brCba5KkqUg', 'jFEdpD9mcGY', 'fGP6JHrO87U']))
        self.assertNotIn('فيديو مميز', content)            # no spotlight when filtered
        self.assertIn('aria-current="true"', content)

    def test_unknown_topic_shows_everything(self):
        content = self.client.get('/en/videos/?topic=nope').content.decode()
        self.assertEqual(len(re.findall(r'data-youtube-id=', content)), 12)


class VideoTests(TestCase):
    def setUp(self):
        Video.objects.all().delete()  # start from an empty library, not the firm's loaded videos

    def make(self, **kwargs):
        data = {
            'title_ar': 'حقوق المتهم أثناء التحقيق',
            'youtube_url': 'https://youtu.be/dQw4w9WgXcQ?si=abc',
            'published_on': datetime.date(2026, 10, 1),
        }
        data.update(kwargs)
        return Video.objects.create(**data)

    def test_extracts_id_from_common_link_formats(self):
        for url in (
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ&t=30',
            'https://youtu.be/dQw4w9WgXcQ?si=F93W4a6SD1QFvaDG',
            'https://youtube.com/shorts/dQw4w9WgXcQ?feature=share',
            'https://www.youtube.com/live/dQw4w9WgXcQ',
            'https://www.youtube.com/embed/dQw4w9WgXcQ',
            'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
        ):
            self.assertEqual(extract_youtube_id(url), 'dQw4w9WgXcQ', url)
        self.assertEqual(extract_youtube_id('https://www.youtube.com/@drmohamedelgendy'), '')

    def test_non_video_link_is_rejected(self):
        video = Video(title_ar='x', youtube_url='https://www.youtube.com/@drmohamedelgendy')
        with self.assertRaises(ValidationError):
            video.full_clean()

    def test_home_shows_latest_published_videos_only(self):
        self.make(title_ar='مخفي', youtube_url='https://youtu.be/aaaaaaaaaaa', is_published=False)
        for i in range(4):
            self.make(title_ar=f'فيديو {i}', youtube_url=f'https://youtu.be/bbbbbbbbbb{i}',
                      published_on=datetime.date(2026, 10, i + 1))
        content = self.client.get('/ar/').content.decode()
        self.assertIn('data-youtube-id="bbbbbbbbbb3"', content)
        self.assertNotIn('data-youtube-id="bbbbbbbbbb0"', content)  # only the latest three
        self.assertNotIn('مخفي', content)
        self.assertNotIn('[عنوان الفيديو]', content)  # placeholders replaced

    def test_home_keeps_placeholders_without_videos(self):
        self.assertContains(self.client.get('/ar/'), '[عنوان الفيديو]')

    def test_english_falls_back_to_arabic_title_marked_as_arabic(self):
        self.make()
        response = self.client.get('/en/videos/')
        self.assertContains(response, 'lang="ar" dir="rtl">حقوق المتهم أثناء التحقيق</h3>')

    def test_english_title_used_when_present(self):
        self.make(title_en="The accused's rights during investigation")
        self.assertContains(self.client.get('/en/videos/'), 'lang="en" dir="ltr">The accused&#x27;s rights')

    def test_videos_page_lists_and_paginates(self):
        for i in range(13):
            self.make(title_ar=f'فيديو {i}', youtube_url=f'https://youtu.be/cccccccc{i:03d}')
        first = self.client.get('/ar/videos/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.content.decode().count('data-youtube-id='), 12)
        self.assertContains(first, 'rel="next"')
        second = self.client.get('/ar/videos/?page=2')
        self.assertEqual(second.content.decode().count('data-youtube-id='), 1)

    def test_videos_page_empty_state(self):
        response = self.client.get('/en/videos/')
        self.assertContains(response, 'No videos have been published on the site yet.')
        self.assertNotContains(response, 'noindex')

    def test_videos_nav_item_no_longer_marked_soon(self):
        content = self.client.get('/en/videos/').content.decode()
        self.assertRegex(content, r'href="/en/videos/" aria-current="page">\s*Videos\s*</a>')


class AboutPageTests(TestCase):
    def test_arabic_sections_in_order(self):
        response = self.client.get('/ar/about/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="ar" dir="rtl">')
        content = response.content.decode()
        order = [content.index(f'id="{s}"') for s in
                 ('about-firm', 'about-practice', 'about-team', 'about-values', 'about-cta')]
        self.assertEqual(order, sorted(order))
        self.assertEqual(content.count('class="tl-marker'), 5)
        for text in ('عن المكتب', 'مجالات العمل', 'فريق العمل', 'قيمنا ومبادئنا', 'محكمة النقض'):
            self.assertIn(text, content)
        self.assertNotIn('noindex', content)

    def test_english_is_ltr(self):
        response = self.client.get('/en/about/')
        self.assertContains(response, '<html lang="en" dir="ltr">')
        for text in ('About the firm', 'Practice areas', 'Our team', 'Our principles', 'Court of Cassation'):
            self.assertContains(response, text)

    def test_sections_alternate_sides(self):
        content = self.client.get('/ar/about/').content.decode()
        self.assertIn('class="tl-row tl-row--alt" id="about-practice"', content)
        self.assertIn('class="tl-row tl-row--alt" id="about-values"', content)

    def test_missing_photos_show_marked_placeholders(self):
        content = self.client.get('/en/about/').content.decode()
        self.assertEqual(content.count('class="img-slot"'), 6)
        self.assertIn('The approved photograph goes here', content)

    def test_no_invented_claims(self):
        content = self.client.get('/ar/about/').content.decode()
        self.assertIn('تُضاف هنا أسماء أعضاء الفريق', content)
        self.assertNotIn('خبرة قانونية .. لحماية حقوقك', content)

    def test_about_nav_item_no_longer_marked_soon(self):
        content = self.client.get('/en/about/').content.decode()
        self.assertRegex(content, r'href="/en/about/" aria-current="page">\s*About Us\s*</a>')


class CasePathTests(TestCase):
    def test_case_path_sits_after_our_approach_on_home(self):
        content = self.client.get('/ar/').content.decode()
        approach = content.index('id="approach-title"')
        path = content.index('id="case-path-title"')
        videos = content.index('id="videos-title"')
        self.assertLess(approach, path)
        self.assertLess(path, videos)
        for title in ('الضبط والقبض', 'التحقيق', 'المحاكمة', 'الطعن بالنقض'):
            self.assertIn(title, content)

    def test_stage_explainers_use_the_firms_videos(self):
        content = self.client.get('/en/').content.decode()
        ids = re.findall(r'data-video-dialog-open="([^"]+)"', content)
        self.assertEqual(ids, ['wczSD_28O7I', 'AbLfixzSnao', 'wyxoSroUyH8', 'fGP6JHrO87U'])
        self.assertIn('<dialog class="video-dialog"', content)

    def test_stage_without_published_video_has_no_link(self):
        Video.objects.filter(youtube_id='fGP6JHrO87U').update(is_published=False)
        content = self.client.get('/ar/').content.decode()
        self.assertNotIn('data-video-dialog-open="fGP6JHrO87U"', content)
        self.assertIn('الطعن بالنقض', content)

    def test_not_on_about_page(self):
        self.assertNotContains(self.client.get('/ar/about/'), 'case-path')


class ContactPageTests(TestCase):
    def test_page_structure_both_languages(self):
        ar = self.client.get('/ar/contact/')
        self.assertEqual(ar.status_code, 200)
        self.assertContains(ar, '<html lang="ar" dir="rtl">')
        for text in ('كيف يمكننا مساعدتك؟', 'موقف عاجل', 'قضية منظورة أو حكم صادر', 'استفسار أو موعد',
                     'ماذا يحدث بعد الإرسال؟', 'العنوان ومواعيد العمل'):
            self.assertContains(ar, text)
        en = self.client.get('/en/contact/')
        self.assertContains(en, '<html lang="en" dir="ltr">')
        self.assertContains(en, 'How can we help?')
        self.assertNotContains(en, 'noindex')

    def test_form_posts_back_to_contact_page(self):
        content = self.client.get('/ar/contact/').content.decode()
        self.assertIn('action="/ar/contact/#consultation"', content)
        response = self.client.post('/ar/contact/', VALID)
        self.assertRedirects(response, '/ar/contact/#consultation', fetch_redirect_response=False)
        self.assertEqual(ConsultationRequest.objects.count(), 1)

    def test_home_form_still_posts_to_home(self):
        self.assertContains(self.client.get('/en/'), 'action="/en/#consultation"')

    @override_settings(FIRM={'site_url': ''})
    def test_urgent_route_without_numbers_shows_placeholder(self):
        content = self.client.get('/en/contact/').content.decode()
        self.assertIn('Direct contact number to be added', content)
        self.assertNotIn('href="tel:', content)

    @override_settings(FIRM={'phone': '+20 2 1234 5678', 'whatsapp_number': '201234567890', 'site_url': ''})
    def test_urgent_route_uses_configured_numbers(self):
        content = self.client.get('/ar/contact/').content.decode()
        self.assertIn('href="tel:+20 2 1234 5678"', content)
        self.assertIn('href="https://wa.me/201234567890"', content)
        self.assertIn('+201234567890', content)  # shown on the business card

    def test_contact_nav_item_no_longer_marked_soon(self):
        content = self.client.get('/en/contact/').content.decode()
        self.assertRegex(content, r'href="/en/contact/" aria-current="page">\s*Contact Us\s*</a>')


import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile

from .models import SitePhoto

_MEDIA = tempfile.mkdtemp()


def _jpeg(size=(40, 30)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', size, (120, 100, 60)).save(buf, 'JPEG')
    return SimpleUploadedFile('photo.jpg', buf.getvalue(), content_type='image/jpeg')


@override_settings(MEDIA_ROOT=_MEDIA)
class SitePhotoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(_MEDIA, ignore_errors=True)

    def test_placeholders_without_uploads(self):
        self.assertEqual(self.client.get('/ar/about/').content.decode().count('class="img-slot"'), 6)

    def test_uploaded_photo_replaces_placeholder_with_alt(self):
        SitePhoto.objects.create(slot='about_team', image=_jpeg(), alt_ar='فريق المكتب', alt_en='The team')
        ar = self.client.get('/ar/about/').content.decode()
        self.assertIn('/media/site-photos/', ar)
        self.assertIn('alt="فريق المكتب"', ar)
        self.assertEqual(ar.count('class="img-slot"'), 5)
        self.assertIn('alt="The team"', self.client.get('/en/about/').content.decode())

    def test_home_portrait_slot(self):
        SitePhoto.objects.create(slot='home_portrait', image=_jpeg(), alt_ar='د. محمد الجندي')
        self.assertContains(self.client.get('/ar/'), 'alt="د. محمد الجندي"')

    def test_validation_rejects_non_images_and_large_files(self):
        bad = SitePhoto(slot='about_cta', alt_ar='x',
                        image=SimpleUploadedFile('notes.txt', b'hello', content_type='text/plain'))
        with self.assertRaises(ValidationError):
            bad.full_clean()
        big = _jpeg()
        big.size = 6 * 1024 * 1024
        with self.assertRaises(ValidationError):
            SitePhoto(slot='about_hero', alt_ar='x', image=big).full_clean()

    def test_replacing_deletes_old_file(self):
        photo = SitePhoto.objects.create(slot='about_office', image=_jpeg(), alt_ar='x')
        old = photo.image.name
        photo.image = _jpeg((50, 30))
        photo.save()
        self.assertFalse(photo.image.storage.exists(old))

    def test_admin_add_page_loads(self):
        from django.contrib.auth import get_user_model
        admin = get_user_model().objects.create_superuser('t', 't@example.com', 'pw-Strong-123')
        self.client.force_login(admin)
        self.assertContains(self.client.get('/admin/core/sitephoto/add/'), 'Recommended size')


from .models import Article, article_blocks
from .templatetags.article_text import inline_links


class ArticleTests(TestCase):
    def make(self, **kwargs):
        data = {'title_ar': 'مقال اختبار', 'category': 'procedure', 'excerpt_ar': 'مقتطف قصير.',
                'body_ar': '## عنوان فرعي\nفقرة أولى.\n- بند أول\n- بند ثان\nفقرة أخيرة.'}
        data.update(kwargs)
        return Article.objects.create(**data)

    def test_firms_articles_loaded(self):
        self.assertEqual(Article.objects.filter(is_published=True).count(), 9)

    def test_library_page_both_languages(self):
        for lang in ('ar', 'en'):
            response = self.client.get(f'/{lang}/articles/')
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'noindex')
        self.assertContains(self.client.get('/ar/articles/'), 'المكتبة القانونية')

    def test_article_sits_on_its_shelf(self):
        art = self.make(title_ar='مقال على رف النقض', spine_ar='رف النقض', category='cassation')
        content = self.client.get('/ar/articles/').content.decode()
        shelf = content.split('id="shelf-cassation"')[1].split('class="shelf__board"')[0]
        self.assertIn(f'href="/ar/articles/{art.pk}/"', shelf)
        self.assertIn('رف النقض', shelf)

    def test_detail_renders_headings_and_lists(self):
        art = self.make()
        content = self.client.get(f'/ar/articles/{art.pk}/').content.decode()
        self.assertIn('<h2 class="reading__h2">عنوان فرعي</h2>', content)
        self.assertIn('<li>بند أول</li>', content)
        self.assertIn('<p>فقرة أخيرة.</p>', content)
        self.assertIn('مدة القراءة:', content)

    def test_article_blocks_parser(self):
        blocks = article_blocks('## ع\nف\n- أ\n- ب\nج')
        self.assertEqual([b['type'] for b in blocks], ['heading', 'para', 'list', 'para'])
        self.assertEqual(blocks[2]['items'], ['أ', 'ب'])

    def test_links_and_bold_render_safely(self):
        html = inline_links('**مهم** [المصدر](https://example.com/a) <script>x</script>')
        self.assertIn('<strong>مهم</strong>', html)
        self.assertIn('<a href="https://example.com/a" target="_blank" rel="noopener">المصدر</a>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)

    def test_unsafe_links_not_turned_into_links(self):
        for bad in ('[x](javascript:alert(1))', '[x](http://example.com)'):
            self.assertNotIn('<a ', inline_links(bad))

    def test_hidden_article_not_listed_or_reachable(self):
        art = self.make(title_ar='مقال مخفي', is_published=False)
        self.assertNotContains(self.client.get('/ar/articles/'), 'مقال مخفي')
        self.assertEqual(self.client.get(f'/ar/articles/{art.pk}/').status_code, 404)
        self.assertNotContains(self.client.get('/ar/'), 'مقال مخفي')

    def test_search(self):
        self.make(title_ar='مقال عن البحث الفريد')
        response = self.client.get('/ar/articles/', {'q': 'الفريد'})
        self.assertContains(response, 'مقال عن البحث الفريد')
        self.assertContains(response, 'نتائج البحث عن')
        nothing = self.client.get('/ar/articles/', {'q': 'لا يوجد شيء كهذا'})
        self.assertContains(nothing, 'لا توجد مقالات تطابق بحثك.')

    def test_english_falls_back_to_arabic_marked_as_arabic(self):
        art = self.make()
        content = self.client.get(f'/en/articles/{art.pk}/').content.decode()
        self.assertIn('<article class="reading" lang="ar" dir="rtl">', content)
        self.assertIn('<html lang="en" dir="ltr">', content)

    def test_english_version_used_when_complete(self):
        art = self.make(title_en='Test article', excerpt_en='Short excerpt.', body_en='First paragraph.')
        content = self.client.get(f'/en/articles/{art.pk}/').content.decode()
        self.assertIn('<article class="reading" lang="en" dir="ltr">', content)
        self.assertIn('Test article', content)

    def test_empty_shelves_show_coming_soon_volumes(self):
        Article.objects.all().delete()
        content = self.client.get('/ar/articles/').content.decode()
        self.assertEqual(content.count('book--soon'), 9)  # 3 shelves x 3 volumes

    def test_home_shows_latest_articles(self):
        art = self.make(title_ar='أحدث مقال', published_on=datetime.date(2030, 1, 1))
        self.assertContains(self.client.get('/ar/'), f'href="/ar/articles/{art.pk}/"')

    def test_related_articles_from_same_shelf(self):
        a = self.make(title_ar='الأول', category='trials')
        b = self.make(title_ar='الثاني', category='trials')
        content = self.client.get(f'/ar/articles/{a.pk}/').content.decode()
        self.assertIn(f'href="/ar/articles/{b.pk}/"', content)
        self.assertIn('من الرف نفسه', content)


class SiteFeatureTests(TestCase):
    def test_privacy_page_both_languages_and_draft_flag(self):
        ar = self.client.get('/ar/privacy/')
        self.assertEqual(ar.status_code, 200)
        self.assertContains(ar, 'سياسة الخصوصية')
        self.assertContains(ar, 'مسودة بانتظار مراجعة المكتب واعتماده.')
        self.assertContains(self.client.get('/en/privacy/'), 'Privacy Policy')

    def test_privacy_linked_from_footer_and_form(self):
        content = self.client.get('/ar/contact/').content.decode()
        self.assertGreaterEqual(content.count('href="/ar/privacy/"'), 2)  # footer + form note

    def test_article_share_buttons(self):
        art = Article.objects.first()
        content = self.client.get(f'/ar/articles/{art.pk}/').content.decode()
        self.assertIn('https://wa.me/?text=', content)
        self.assertIn('https://www.facebook.com/sharer/sharer.php?u=http%3A//testserver/ar/articles/', content)
        self.assertIn('data-copy-link="http://testserver/ar/articles/', content)

    @override_settings(FIRM={'whatsapp_number': '201068686896', 'site_url': ''})
    def test_floating_whatsapp_on_every_page(self):
        for path in ('/ar/', '/en/about/', '/ar/articles/', '/ar/privacy/'):
            self.assertContains(self.client.get(path), 'class="wa-float" href="https://wa.me/201068686896"')

    @override_settings(FIRM={'site_url': ''})
    def test_no_floating_whatsapp_without_number(self):
        self.assertNotContains(self.client.get('/ar/'), 'class="wa-float"')

    @override_settings(FIRM={'google_business_url': 'https://g.page/example', 'site_url': ''})
    def test_google_business_link_when_set(self):
        content = self.client.get('/ar/contact/').content.decode()
        self.assertGreaterEqual(content.count('href="https://g.page/example"'), 2)  # contact + footer

    @override_settings(FIRM={'site_url': ''})
    def test_no_google_business_link_when_unset(self):
        self.assertNotContains(self.client.get('/ar/contact/'), 'المكتب على Google')


class LanguageDefaultTests(TestCase):
    def test_new_visitor_always_gets_arabic(self):
        for header in ('en-US,en;q=0.9', 'fr', 'ar', ''):
            response = self.client.get('/', HTTP_ACCEPT_LANGUAGE=header)
            self.assertRedirects(response, '/ar/', fetch_redirect_response=False)

    def test_arabic_home_is_rtl_with_english_switch(self):
        response = self.client.get('/ar/', HTTP_ACCEPT_LANGUAGE='en-US')
        self.assertContains(response, '<html lang="ar" dir="rtl">')
        self.assertContains(response, 'class="lang-switch" href="/en/"')

    def test_chosen_language_is_remembered(self):
        self.client.get('/en/about/', HTTP_ACCEPT_LANGUAGE='ar')
        response = self.client.get('/', HTTP_ACCEPT_LANGUAGE='ar')
        self.assertRedirects(response, '/en/', fetch_redirect_response=False)
        self.client.get('/ar/')
        self.assertRedirects(self.client.get('/'), '/ar/', fetch_redirect_response=False)

    def test_share_section_redesign(self):
        art = Article.objects.first()
        content = self.client.get(f'/ar/articles/{art.pk}/').content.decode()
        self.assertIn('class="share__title" id="share-title">شارك المقال</h2>', content)
        self.assertNotIn('twitter.com', content)
        self.assertIn('تم نسخ الرابط', content)
