from django.contrib import admin
from django.utils.html import format_html

from .models import Article, ConsultationRequest, SitePhoto, Video
from .photos import SLOTS


@admin.register(SitePhoto)
class SitePhotoAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'slot', 'size_hint', 'alt_ar', 'updated_at')
    list_display_links = ('thumb', 'slot')
    readonly_fields = ('preview', 'size_hint')
    fields = ('slot', 'size_hint', 'image', 'preview', 'alt_ar', 'alt_en')

    @admin.display(description='Recommended size')
    def size_hint(self, obj):
        if not obj or not obj.slot:
            return 'Choose a slot; sizes: ' + ', '.join(f'{v[0]}: {v[2]}×{v[3]}' for v in SLOTS.values())
        _, _, w, h = SLOTS[obj.slot]
        return f'{w} × {h} px ({"portrait" if h > w else "landscape"})'

    @admin.display(description='')
    def thumb(self, obj):
        return format_html('<img src="{}" alt="" style="width:96px;height:64px;object-fit:cover">', obj.image.url) if obj.image else ''

    @admin.display(description='Current photo')
    def preview(self, obj):
        if not obj or not obj.image:
            return 'Shown after saving.'
        return format_html('<img src="{}" alt="" style="max-width:360px;max-height:260px;object-fit:contain">', obj.image.url)


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'request_type', 'matter', 'preferred_contact', 'phone', 'language', 'handled', 'created_at')
    list_filter = ('handled', 'request_type', 'matter', 'preferred_contact', 'language')
    list_editable = ('handled',)
    search_fields = ('full_name', 'phone', 'email')
    readonly_fields = ('created_at', 'language')


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'title_ar', 'topic', 'published_on', 'is_published', 'is_featured', 'position')
    list_display_links = ('thumbnail', 'title_ar')
    list_editable = ('is_published', 'is_featured', 'position')
    list_filter = ('is_published', 'is_featured', 'topic')
    search_fields = ('title_ar', 'title_en')
    date_hierarchy = 'published_on'
    readonly_fields = ('preview',)
    fieldsets = (
        (None, {'fields': ('youtube_url', 'preview', 'topic', 'duration', 'published_on', 'is_published')}),
        ('Home page', {'fields': ('is_featured', 'position')}),
        ('Arabic', {'fields': ('title_ar', 'description_ar')}),
        ('English', {'fields': ('title_en', 'description_en')}),
    )

    @admin.display(description='')
    def thumbnail(self, obj):
        return format_html('<img src="{}" alt="" style="width:96px;height:54px;object-fit:cover">', obj.thumbnail_url)

    @admin.display(description='Preview')
    def preview(self, obj):
        if not obj.youtube_id:
            return 'Shown after saving.'
        return format_html(
            '<a href="{}" target="_blank" rel="noopener"><img src="{}" alt="" style="width:240px;height:135px;object-fit:cover"></a>',
            obj.watch_url, obj.thumbnail_url,
        )


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title_ar', 'category', 'author', 'published_on', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'category')
    search_fields = ('title_ar', 'title_en', 'body_ar')
    date_hierarchy = 'published_on'
    fieldsets = (
        (None, {'fields': ('category', 'author', 'published_on', 'is_published')}),
        ('Arabic', {'fields': ('title_ar', 'spine_ar', 'excerpt_ar', 'body_ar')}),
        ('English (optional)', {'fields': ('title_en', 'spine_en', 'excerpt_en', 'body_en')}),
    )
