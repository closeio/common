import datetime

from django.conf import settings
from django.contrib.auth.middleware import get_user
from django.core.exceptions import MiddlewareNotUsed


class DebugSQLMiddleware(object):
    def __init__(self):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

    def process_response(self, request, response):
        if not request.path.startswith(settings.STATIC_URL) and not request.path == '/favicon.ico':
            from django.db import connection
            for q in connection.queries:
                print q.get('duration', q.get('time')), q
                print
        return response


class ExceptionMiddleware(object):
    def __init__(self):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

    """
    def process_request(self, request):
        import time
        import random
        time.sleep(random.randrange(1, 10)/10.0)
    """

    def process_exception(self, request, exception):
        import traceback
        traceback.print_exc()


class AuthenticationMiddleware(object):
    def process_request(self, request):
        request.user = get_user(request)


class SSLMiddleware:
    def __init__(self):
        pass

    def process_request(self, request):
        def is_secure():
            if settings.USE_SSL:
                return True
            else:
                return False

        request.is_secure = is_secure

    def process_response(self, request, response):
        response['P3P'] = 'CP="IDC DSP COR ADM DEVi TAIi PSA PSD IVAi IVDi CONi HIS OUR IND CNT"'
        return response


class LastLoginMiddleware(object):
    def process_request(self, request):
        if request.user and request.user.is_authenticated():
            request.user.last_login = datetime.datetime.utcnow()
            request.user.save()


class LastLoginByTemplatedResponseMiddleware(object):
    def process_template_response(self, request, response):
        if request.user and request.user.is_authenticated():
            request.user.last_login = datetime.datetime.utcnow()
            request.user.save()
        return response


import threading
from collections import defaultdict

_thread_locals = threading.local()

def get_request_cache():
    request_cache = getattr(_thread_locals, 'request_cache', None)
    if not request_cache:
        request_cache = defaultdict(lambda: None)
        _thread_locals.request_cache = request_cache
    return request_cache
