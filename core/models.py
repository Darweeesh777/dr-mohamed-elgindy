import re
from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.templatetags.static import static
from django.utils import timezone

YOUTUBE_ID_RE = re.compile(
    r'(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/|v/))'
    r'([A-Za-z0-9_-]{11})'
)
# Facebook video links: reels, watch?v=, /videos/<id>, share/v/ and fb.watch short links.
FACEBOOK_URL_RE = re.compile(
    r'^https://(?:(?:www|m|web)\.)?(?:facebook\.com/(?:reel/\d+|watch/?\?v=\d+'
    r'|[^/?#]+/videos/(?:[^/?#]+/)?\d+|share/[vr]/[A-Za-z0-9]+)|fb\.watch/[A-Za-z0-9_-]+)'
)
FACEBOOK_POSTER = 'images/video-facebook.svg'  # Facebook offers no stable public thumbnail


TOPICS = [
    ('cassation', 'Criminal cassation'),
    ('procedure', 'Procedural nullity'),
    ('trials', 'Trials & the right of defence'),
]

DURATION_VALIDATOR = RegexValidator(r'^(\d{1,2}:)?\d{1,2}:\d{2}$', 'Use minutes:seconds, e.g. 7:05 or 1:02:30.')


MAX_PHOTO_MB = 5


def validate_photo_size(file):
    if file.size > MAX_PHOTO_MB * 1024 * 1024:
        raise ValidationError(f'Image is larger than {MAX_PHOTO_MB} MB. Please compress it first.')


def is_facebook_video_url(url):
    return bool(FACEBOOK_URL_RE.match(url or ''))


def extract_youtube_id(url):
    """Return the 11-character video ID from any common YouTube link, or ''."""
    match = YOUTUBE_ID_RE.search(url or '')
    return match.group(1) if match else ''


class Video(models.Model):
    """A video hosted on YouTube or Facebook and shown on the site.

    Only the link is stored: YouTube or Facebook hosts and streams the file.
    Each video has exactly one of the two links.
    """

    title_ar = models.CharField('title (Arabic)', max_length=200)
    title_en = models.CharField(
        'title (English)', max_length=200, blank=True,
        help_text='Leave empty if there is no approved English title; the Arabic title is shown instead.',
    )
    description_ar = models.TextField('description (Arabic)', blank=True)
    description_en = models.TextField(
        'description (English)', blank=True,
        help_text='Optional. Without it, no description is shown on the English site.',
    )
    youtube_url = models.URLField(
        'YouTube link', max_length=300, blank=True,
        help_text='Any YouTube link to the video: watch, youtu.be, Shorts or live.',
    )
    youtube_id = models.CharField(max_length=11, editable=False, blank=True)
    facebook_url = models.URLField(
        'Facebook link', max_length=300, blank=True,
        help_text='Instead of a YouTube link: a Facebook reel or video link, e.g. https://www.facebook.com/reel/123…',
    )
    topic = models.CharField(max_length=20, choices=TOPICS, blank=True)
    duration = models.CharField(
        max_length=8, blank=True, validators=[DURATION_VALIDATOR],
        help_text='Optional, as shown on YouTube, e.g. 7:05 or 1:02:30.',
    )
    published_on = models.DateField('date', default=timezone.localdate)
    is_published = models.BooleanField('show on website', default=True)
    is_featured = models.BooleanField(
        'featured', default=False,
        help_text='Featured videos appear first on the home page (up to 3) and at the top of the Videos page.',
    )
    position = models.PositiveSmallIntegerField(
        'featured order', default=0, help_text='Lower numbers appear first among featured videos.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_on', '-id']

    def __str__(self):
        return self.title_ar

    def clean(self):
        if bool(self.youtube_url) == bool(self.facebook_url):
            raise ValidationError('Enter either a YouTube link or a Facebook link (one of the two).')
        if self.youtube_url and not extract_youtube_id(self.youtube_url):
            raise ValidationError({'youtube_url': 'This is not a recognised YouTube video link.'})
        if self.facebook_url and not is_facebook_video_url(self.facebook_url):
            raise ValidationError({'facebook_url': 'This is not a recognised Facebook video or reel link.'})

    def save(self, *args, **kwargs):
        self.youtube_id = extract_youtube_id(self.youtube_url)
        super().save(*args, **kwargs)

    @property
    def source(self):
        return 'youtube' if self.youtube_id else 'facebook'

    @property
    def key(self):
        """Identifies the video's player on a page."""
        return self.youtube_id or f'fb{self.pk}'

    @property
    def thumbnail_url(self):
        if self.source == 'facebook':
            return static(FACEBOOK_POSTER)
        return f'https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg'

    @property
    def watch_url(self):
        if self.source == 'facebook':
            return self.facebook_url
        return f'https://www.youtube.com/watch?v={self.youtube_id}'

    @property
    def embed_url(self):
        """Facebook's embedded player, or '' for a YouTube video."""
        if self.source != 'facebook':
            return ''
        return 'https://www.facebook.com/plugins/video.php?' + urlencode({'href': self.facebook_url, 'show_text': 'false'})

    def for_language(self, lang, topic_labels=None):
        """Values for one language. A missing English title falls back to the Arabic one, marked as Arabic."""
        if lang == 'en' and self.title_en:
            title, title_lang = self.title_en, 'en'
        else:
            title, title_lang = self.title_ar, 'ar'
        return {
            'id': self.key,
            'source': self.source,
            'embed_url': self.embed_url,
            'title': title,
            'title_lang': title_lang,
            'title_dir': 'rtl' if title_lang == 'ar' else 'ltr',
            'description': self.description_en if lang == 'en' else self.description_ar,
            'date': self.published_on,
            'duration': self.duration,
            'topic': self.topic,
            'topic_label': (topic_labels or {}).get(self.topic, ''),
            'thumbnail': self.thumbnail_url,
            'thumbnail_large': (f'https://i.ytimg.com/vi/{self.youtube_id}/sddefault.jpg'
                                if self.source == 'youtube' else self.thumbnail_url),
            'watch_url': self.watch_url,
        }


class ConsultationRequest(models.Model):
    """A consultation or appointment request sent from the website form.

    Only what the firm needs to reply is stored; the form asks visitors not to
    send confidential case details.
    """

    REQUEST_TYPES = [
        ('consultation', 'Legal consultation'),
        ('appointment', 'Appointment'),
    ]
    MATTERS = [
        ('criminal', 'Criminal case'),
        ('felony', 'Felony case'),
        ('cassation', 'Cassation appeal'),
        ('other', 'Other / not sure'),
    ]
    CONTACT_METHODS = [
        ('whatsapp', 'WhatsApp'),
        ('phone', 'Phone call'),
        ('email', 'Email'),
    ]

    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES, default='consultation')
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_METHODS, default='whatsapp')
    matter = models.CharField(max_length=20, choices=MATTERS, default='other')
    message = models.TextField(blank=True, max_length=1000)
    consent = models.BooleanField(default=False)
    language = models.CharField(max_length=5, default='ar')
    handled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'consultation request'
        verbose_name_plural = 'consultation requests'

    def __str__(self):
        return f'{self.full_name} — {self.get_request_type_display()} ({self.created_at:%Y-%m-%d})'


class SitePhoto(models.Model):
    """An uploaded photo for one fixed slot on the site (see core/photos.py)."""

    from .photos import SLOTS as _SLOTS
    SLOT_CHOICES = [(key, value[0]) for key, value in _SLOTS.items()]

    slot = models.CharField(max_length=30, choices=SLOT_CHOICES, unique=True)
    image = models.ImageField(
        upload_to='site-photos/',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']), validate_photo_size],
        help_text=f'JPG, PNG or WebP, up to {MAX_PHOTO_MB} MB. Use real photos with no client documents visible.',
    )
    alt_ar = models.CharField('description (Arabic)', max_length=200,
                              help_text='Short description of the photo for screen readers, e.g. «مكتب د. محمد الجندي».')
    alt_en = models.CharField('description (English)', max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'site photo'
        verbose_name_plural = 'site photos'
        ordering = ['slot']

    def __str__(self):
        return self.get_slot_display()

    def save(self, *args, **kwargs):
        # Replacing a photo removes the old file.
        if self.pk:
            old = SitePhoto.objects.filter(pk=self.pk).values_list('image', flat=True).first()
            if old and old != self.image.name:
                self.image.storage.delete(old)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        name, storage = self.image.name, self.image.storage
        super().delete(*args, **kwargs)
        if name:
            storage.delete(name)


def article_blocks(body):
    """Split plain article text into blocks: '## ' line = subheading, '- ' lines = list, else paragraph."""
    blocks, items = [], []
    for raw in body.replace('\r\n', '\n').split('\n'):
        line = raw.strip()
        if line.startswith('- '):
            items.append(line[2:].strip())
            continue
        if items:
            blocks.append({'type': 'list', 'items': items})
            items = []
        if not line:
            continue
        if line.startswith('## '):
            blocks.append({'type': 'heading', 'text': line[3:].strip()})
        else:
            blocks.append({'type': 'para', 'text': line})
    if items:
        blocks.append({'type': 'list', 'items': items})
    return blocks


class Article(models.Model):
    """A legal article, shown as a book on the Articles "library" shelves.

    The body is plain text: blank lines separate paragraphs (no HTML)."""

    title_ar = models.CharField('title (Arabic)', max_length=200)
    title_en = models.CharField('title (English)', max_length=200, blank=True,
                                help_text='Leave empty to show the Arabic title on the English site.')
    spine_ar = models.CharField('spine label (Arabic)', max_length=60, blank=True,
                                help_text='Short title for the book spine. Defaults to the title.')
    spine_en = models.CharField('spine label (English)', max_length=60, blank=True)
    category = models.CharField(max_length=20, choices=TOPICS)
    excerpt_ar = models.TextField('excerpt (Arabic)', max_length=400)
    excerpt_en = models.TextField('excerpt (English)', max_length=400, blank=True)
    body_ar = models.TextField('text (Arabic)', help_text='One paragraph per line. Start a line with "## " for a subheading, "- " for a list item.')
    body_en = models.TextField('text (English)', blank=True,
                               help_text='Optional. Without it, the English site shows the Arabic text.')
    author = models.CharField(max_length=120, default='د. محمد الجندي')
    published_on = models.DateField('date', default=timezone.localdate)
    is_published = models.BooleanField('show on website', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_on', '-id']

    def __str__(self):
        return self.title_ar

    def for_language(self, lang):
        use_en = lang == 'en' and self.title_en and self.body_en
        title = self.title_en if use_en else self.title_ar
        body = self.body_en if use_en else self.body_ar
        text_lang = 'en' if use_en else 'ar'
        words = len(body.split()) + len((self.excerpt_en if use_en else self.excerpt_ar).split())
        return {
            'pk': self.pk,
            'title': title,
            'spine': (self.spine_en if use_en else self.spine_ar) or title,
            'excerpt': (self.excerpt_en if use_en else self.excerpt_ar),
            'blocks': article_blocks(body),
            'lang': text_lang,
            'dir': 'rtl' if text_lang == 'ar' else 'ltr',
            'category': self.category,
            'author': self.author,
            'date': self.published_on,
            'minutes': max(1, -(-words // 180)),  # round up, ~180 words a minute
        }
