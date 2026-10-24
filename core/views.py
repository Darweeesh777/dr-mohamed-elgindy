from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language

from .content import BUILT_PAGES, PAGES, PRIVACY_APPROVED, get_content
from .forms import ConsultationForm
from .models import Article, Video
from .photos import site_photos

HOME_VIDEO_COUNT = 3
VIDEOS_PER_PAGE = 12


def _lang():
    lang = (get_language() or 'ar')[:2]
    return lang if lang in ('ar', 'en') else 'ar'


def _video_cards(videos, lang):
    labels = get_content(lang)['videos']['topics']
    return [video.for_language(lang, labels) for video in videos]


def _home_videos():
    """Featured videos in their set order, topped up with the latest ones."""
    published = Video.objects.filter(is_published=True)
    featured = list(published.filter(is_featured=True).order_by('position', '-published_on')[:HOME_VIDEO_COUNT])
    if len(featured) < HOME_VIDEO_COUNT:
        featured += list(published.exclude(pk__in=[v.pk for v in featured])[:HOME_VIDEO_COUNT - len(featured)])
    return featured


def _case_stages(lang):
    """Case path stages, each with its explainer video when that video is published."""
    t = get_content(lang)
    stages = t['case_path']['stages']
    videos = {v.youtube_id: v for v in Video.objects.filter(
        is_published=True, youtube_id__in=[s['video'] for s in stages])}
    labels = t['videos']['topics']
    return [
        {**stage, 'number': f'{i:02d}', 'last': i == len(stages),
         'video_card': videos[stage['video']].for_language(lang, labels) if stage['video'] in videos else None}
        for i, stage in enumerate(stages, 1)
    ]


def _handle_consultation(request, lang, url_name):
    """Consultation form for a page: (form, redirect) — redirect is set after a valid POST."""
    if request.method == 'POST':
        form = ConsultationForm(request.POST, lang=lang)
        if form.is_valid():
            form.save()
            messages.success(request, get_content(lang)['form']['success'])
            return form, redirect(reverse(url_name) + '#consultation')
        return form, None
    requested = request.GET.get('type')
    initial = {'request_type': requested} if requested in ('consultation', 'appointment') else {}
    return ConsultationForm(lang=lang, initial=initial), None


def home(request):
    lang = _lang()
    form, done = _handle_consultation(request, lang, 'core:home')
    if done:
        return done

    return render(request, 'core/home.html', {
        'form': form,
        'page': 'home',
        'photos': site_photos(lang),
        'video_cards': _video_cards(_home_videos(), lang),
        'case_stages': _case_stages(lang),
        'video_placeholders': range(3),
        'articles': range(3),
        'article_cards': [a.for_language(lang) for a in Article.objects.filter(is_published=True)[:3]],
    })


def videos(request):
    lang = _lang()
    labels = get_content(lang)['videos']['topics']
    published = Video.objects.filter(is_published=True)

    topic = request.GET.get('topic', '')
    if topic not in labels:
        topic = ''

    # The top featured video gets the spotlight on the unfiltered first page,
    # and is left out of the grid so it is not shown twice.
    spotlight = None
    videos_qs = published.filter(topic=topic) if topic else published
    if not topic:
        spotlight = published.filter(is_featured=True).order_by('position', '-published_on').first()
        if spotlight:
            videos_qs = videos_qs.exclude(pk=spotlight.pk)

    paginator = Paginator(videos_qs, VIDEOS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))
    show_spotlight = spotlight is not None and page_obj.number == 1

    counts = {key: published.filter(topic=key).count() for key in labels}
    topics = [{'key': '', 'label': get_content(lang)['videos']['all'], 'count': published.count(), 'active': not topic}]
    topics += [
        {'key': key, 'label': label, 'count': counts[key], 'active': key == topic}
        for key, label in labels.items() if counts[key]
    ]

    return render(request, 'core/videos.html', {
        'page': 'videos',
        'page_obj': page_obj,
        'topic': topic,
        'topics': topics,
        'total': published.count(),
        'spotlight': spotlight.for_language(lang, labels) if show_spotlight else None,
        'video_cards': _video_cards(page_obj.object_list, lang),
    })


PRINCIPLE_ICONS = ['lock', 'document', 'speech', 'search']


def about(request):
    lang = _lang()
    t = get_content(lang)
    return render(request, 'core/about.html', {
        'page': 'about',
        'photos': site_photos(lang),
        'principles': [{'icon': icon, **item} for icon, item in zip(PRINCIPLE_ICONS, t['principles']['items'])],
    })


def contact(request):
    lang = _lang()
    form, done = _handle_consultation(request, lang, 'core:contact')
    if done:
        return done
    return render(request, 'core/contact.html', {'page': 'contact', 'form': form})


SHELF_MIN_BOOKS = 3  # shelves are topped up with "coming soon" volumes


def articles(request):
    lang = _lang()
    t = get_content(lang)
    published = Article.objects.filter(is_published=True)
    query = request.GET.get('q', '').strip()[:100]
    if query:
        published = published.filter(Q(title_ar__icontains=query) | Q(title_en__icontains=query)
                                     | Q(body_ar__icontains=query) | Q(body_en__icontains=query))
    shelves = []
    for key, label in t['videos']['topics'].items():
        books = [a.for_language(lang) for a in published.filter(category=key)]
        shelves.append({'key': key, 'label': label, 'books': books,
                        'spares': range(max(0, SHELF_MIN_BOOKS - len(books))) if not query else range(0)})
    return render(request, 'core/articles.html', {
        'page': 'articles', 'shelves': shelves, 'query': query,
        'total': sum(len(s['books']) for s in shelves),
    })


def article_detail(request, pk):
    lang = _lang()
    obj = get_object_or_404(Article, pk=pk, is_published=True)
    related = Article.objects.filter(is_published=True, category=obj.category).exclude(pk=pk)[:3]
    return render(request, 'core/article_detail.html', {
        'page': 'articles',
        'article': obj.for_language(lang),
        'category_label': get_content(lang)['videos']['topics'].get(obj.category, ''),
        'related': [a.for_language(lang) for a in related],
    })


def privacy(request):
    return render(request, 'core/privacy.html', {'page': 'privacy', 'approved': PRIVACY_APPROVED})


def pending(request, page):
    """Honest stand-in for pages planned but not built yet."""
    if page not in PAGES or page in BUILT_PAGES:
        raise Http404
    return render(request, 'core/pending.html', {'page': page})
