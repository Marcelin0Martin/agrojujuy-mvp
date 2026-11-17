import time
from django.conf import settings
from django.contrib.sessions.backends.base import UpdateError
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date


class IsolatedSessionMiddleware(SessionMiddleware):
    """
    Aísla completamente la sesión de /admin/ de la sesión de la web principal.
    Permite que un usuario esté autenticado como Productor o Profesional en la web
    y simultáneamente como Administrador en /admin/ en la misma ventana del navegador
    sin interferencia ni sobrescritura de cookies.
    """

    def _get_cookie_config(self, request):
        if request.path.startswith('/admin'):
            return (
                getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'agrojujuy_admin_sessionid'),
                getattr(settings, 'ADMIN_SESSION_COOKIE_PATH', '/admin/'),
            )
        return (
            getattr(settings, 'SESSION_COOKIE_NAME', 'agrojujuy_web_sessionid'),
            getattr(settings, 'SESSION_COOKIE_PATH', '/'),
        )

    def process_request(self, request):
        cookie_name, _ = self._get_cookie_config(request)
        session_key = request.COOKIES.get(cookie_name)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response

        cookie_name, cookie_path = self._get_cookie_config(request)

        if cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                cookie_name,
                path=cookie_path,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ("Cookie",))
        else:
            if accessed:
                patch_vary_headers(response, ("Cookie",))
            if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
                if request.session.get_expire_at_browser_close():
                    max_age = None
                    expires = None
                else:
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)
                if response.status_code < 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        raise SessionInterrupted(
                            "The request's session was deleted before the "
                            "request completed. The user may have logged "
                            "out in a concurrent request, for example."
                        )
                    response.set_cookie(
                        cookie_name,
                        request.session.session_key,
                        max_age=max_age,
                        expires=expires,
                        domain=settings.SESSION_COOKIE_DOMAIN,
                        path=cookie_path,
                        secure=settings.SESSION_COOKIE_SECURE,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                    )
        return response


class OWASPSecurityHeadersMiddleware:
    """
    Aplica cabeceras de seguridad conforme a OWASP Top 10:2025 / ASVS 5.0 Nivel 2 (SKILL.md sección 2.3).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault('X-Frame-Options', 'DENY')
        response.setdefault(
            'Permissions-Policy',
            'geolocation=(), microphone=(), camera=(), payment=(), usb=()'
        )
        response.setdefault(
            'Content-Security-Policy',
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none';"
        )
        if getattr(request, 'user', None) and request.user.is_authenticated:
            response.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        return response
