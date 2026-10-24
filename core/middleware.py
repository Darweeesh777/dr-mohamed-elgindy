from django.conf import settings

SUPPORTED = {code for code, _ in settings.LANGUAGES}
COOKIE_AGE = 60 * 60 * 24 * 365


class ArabicDefaultMiddleware:
    """Arabic for new visitors; remember a visitor's chosen language afterwards.

    Runs before LocaleMiddleware. A visitor with no saved language is treated as
    Arabic regardless of the browser's Accept-Language, so the bare domain always
    opens /ar/. Visiting a /ar/ or /en/ page saves that language in the standard
    language cookie, which LocaleMiddleware then uses for prefix-less URLs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) not in SUPPORTED:
            request.META['HTTP_ACCEPT_LANGUAGE'] = settings.LANGUAGE_CODE

        response = self.get_response(request)

        prefix = request.path_info.strip('/').split('/', 1)[0]
        if prefix in SUPPORTED and request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) != prefix:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, prefix, max_age=COOKIE_AGE,
                                samesite='Lax', secure=not settings.DEBUG)
        return response
