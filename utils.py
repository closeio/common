import datetime
from decimal import Decimal
import os
import hashlib
import operator
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import Q
from django.core.cache import cache
from django.core.mail import mail_admins, EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import loader, RequestContext
from django.utils import simplejson as json
from django.utils.hashcompat import md5_constructor
from django.utils.http import urlquote
from functional import compose

from phonenumbers.phonenumberutil import format_number, parse


def get_image_filename(prefix, obj, filename):
    # Get a unique filename.
    # If the file already exists, Django file storage will add "_" to filename,
    # like "32135162132__.jpg"
    extension = os.path.splitext(filename)[1] # e.g. ".jpg"
    new_filename = hashlib.md5(filename.encode('utf8')+str(datetime.datetime.now())).hexdigest()
    filepath = os.path.join(prefix, new_filename[:2], u'%s%s' % (new_filename, extension))
    return filepath


def invalidate_template_cache(fragment_name, *variables):
    args = md5_constructor(u':'.join(apply(compose(urlquote, unicode), variables)))
    cache_key = 'template.cache.%s.%s' % (fragment_name, args.hexdigest())
    cache.delete(cache_key)


def mail_exception(subject=None, context=None, vars=True):
    import traceback, sys

    exc_info = sys.exc_info()

    if not subject:
        subject = exc_info[1].__class__.__name__

    message = ''

    if context:
        message += 'Context:\n\n'
        try:
            message += '\n'.join(['%s: %s' % (k, v) for k, v in context.iteritems()])
        except:
            message += 'Error reporting context.'
        message += '\n\n\n\n'


    if vars:
        tb = exc_info[2]
        stack = []

        while tb:
            stack.append(tb.tb_frame)
            tb = tb.tb_next

        message = "Locals by frame, innermost last:\n"

        for frame in stack:
            message += "\nFrame %s in %s at line %s\n" % (frame.f_code.co_name,
                                                 frame.f_code.co_filename,
                                                 frame.f_lineno)
            for key, value in frame.f_locals.items():
                message += "\t%16s = " % key
                # We have to be careful not to cause a new error in our error
                # printer! Calling repr() on an unknown object could cause an
                # error we don't want.
                try:
                    message += '%s\n' % repr(value)
                except:
                    message += "<ERROR WHILE PRINTING VALUE>\n"


    message += '\n\n\n%s\n' % (
            '\n'.join(traceback.format_exception(*exc_info)),
        )

    if settings.DEBUG:
        print subject
        print
        print message
    else:
        mail_admins(subject, message, fail_silently=True)


def resolve_dotted_path(path):
    dot = path.rindex('.')
    mod_name, func_name = path[:dot], path[dot+1:]
    return getattr(__import__(mod_name, {}, {}, ['']), func_name)


def utctoday():
    now = datetime.datetime.utcnow()
    today = datetime.date(*now.timetuple()[:3])
    return today


def localtoday():
    from django_tz.global_tz import get_timezone
    import pytz

    tz = get_timezone()
    local_now = tz.normalize(pytz.utc.localize(datetime.datetime.utcnow()).astimezone(tz))
    local_today = datetime.date(*local_now.timetuple()[:3])
    return local_today


def ellipsize(s, length):
    if not s:
        return ''
    if len(s) <= length:
        return s
    else:
        return s[:length-3] + '...'


# MixPanel
def mp_track_event(request, event_name, properties=None, **kwargs):
    import re
    from mixpanel.tasks import EventTracker
    if not settings.MIXPANEL_ENABLED:
        return

    if properties == None:
        properties = {}
    
    if 'distinct_id' not in properties:
        properties['distinct_id'] = request.COOKIES.get('mpDistinctID', None)
    
    properties['campaign'] = request.COOKIES.get('campaign', 'None')
 
    if hasattr(settings, 'ANALYTICS_EXCLUSION_TOKEN'):
        utmv = request.COOKIES.get('__utmv', None)
        pattern = re.compile(".*?" + settings.ANALYTICS_EXCLUSION_TOKEN + "*") 
        if utmv and pattern.match(utmv):
            return

    try:
        et = EventTracker()
        args = (event_name, properties)
        et.delay(*args, **kwargs)
    except Exception, err:
        pass


# JSON
class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return str(obj).split('.')[0]
        if isinstance(obj, datetime.date):
            return str(obj)
        return obj


def dumps(obj, **params):
    return json.dumps(obj, cls=Encoder, **params)


def loads(obj):
    return json.loads(obj)


# SQL
def sql(cursor, sql):
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    cursor.execute(sql)
    rows = [dict_factory(cursor, row) for row in cursor.fetchall()]
    return rows


def get_search_q(fields, kw):
    q_list = []
    words = (re.sub('\s{2,}', ' ', kw).strip()).split(' ')
    for word in words:
        l = []
        if word:
            for field in fields:
                q = Q(**{ '%s__iregex' % field: '[[:<:]]%s' % word})
                l.append(q)
                     
        if l:
            q_list.append(reduce(operator.or_, l))

    return q_list and reduce(operator.and_, q_list) or Q()


# Like reverse(), but returns an full URL 
def full_reverse(*args, **kwargs):
    return 'http%s://%s%s' % (
        use_ssl() and 's' or '',
        Site.objects.get_current().domain,
        reverse(*args, **kwargs)
    )


def full_url(url):
    return 'http%s://%s%s' % (
        use_ssl() and 's' or '',
        Site.objects.get_current().domain,
        url
    )


def memoize(keyformat, time=60):
    """Decorator to memoize functions using memcache."""
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            key = keyformat % args[0:keyformat.count('%')]
            data = cache.get(key)
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            cache.set(key, data, time)
            return data
        return wrapper if settings.CACHE else fxn
    return decorator


def memoize_model(time=60):
    def decorator(fxn):
        def wrapper(*args, **kwargs):
            key = '%s.%s.%s.%d' % ( fxn.__module__, args[0].__class__.__name__, fxn.__name__, args[0].pk )
            data = cache.get(key)
            if data is not None:
                return data
            data = fxn(*args, **kwargs)
            cache.set(key, data, time)
            return data
        return wrapper if settings.CACHE else fxn
    return decorator


def date_range(start, end):
    len = (end-start).days
    dates = [start+datetime.timedelta(days=n) for n in range(len+1)]
    return dates


# returns a tuple (n, obj) where n means:
#     0: nothing changed
#     1: updated object
#     2: created object
def create_or_update(model_class, filter_attrs, attrs, create_attrs={}, update_attrs={}):
    rows = model_class.objects.filter(**filter_attrs)
    if rows:
        updated = rows.exclude(**attrs).update(**dict(attrs, **update_attrs))
        if updated:
            return 1, rows[0]
        else:
            return 0, rows[0]
    else:
        attrs.update(filter_attrs)
        attrs.update(create_attrs)
        obj = model_class.objects.create(**attrs)
        return 2, obj



# SQL
def sql(cursor, sql):
    def dict_factory(cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    cursor.execute(sql)
    rows = [dict_factory(cursor, row) for row in cursor.fetchall()]
    return rows


def render_html_email(name, context):
    import pynliner

    subject = loader.render_to_string('%s.subj.txt' % name, context).strip()
    text_body = loader.render_to_string('%s.body.txt' % name, context)
    html_body = loader.render_to_string('%s.body.html' % name, context)

    css_body = loader.render_to_string(['%s.css' % name, 'shop/notification/email/base.css'])

    # convert to inline-css
    html_body = pynliner.Pynliner().from_string(html_body).with_cssString(css_body).run()

    return subject, text_body, html_body


def use_ssl():
    if hasattr(settings, 'USE_SSL'):
        return settings.USE_SSL
    return False


def full_url_context(request):
    return {
        'STATIC_URL': full_url(settings.STATIC_URL),
        'MEDIA_URL': full_url(settings.MEDIA_URL),
        'BASE_URL': 'http%s://%s' % (use_ssl() and 's' or '', Site.objects.get_current().domain),
    }


def send_html_email(request, recipient, name, extra_context, sender=None, mixpanel_campaign=None):

    if request:
        subject, text, html = render_html_email(name, RequestContext(request, extra_context, processors=[full_url_context]))
    else:
        context = {}
        context.update(full_url_context(None))
        context.update(extra_context)
        subject, text, html = render_html_email(name, context)

    if mixpanel_campaign:
        from mixpanel_email import MixpanelEmail
        api = MixpanelEmail(
            settings.MIXPANEL_API_TOKEN,
            mixpanel_campaign,
        )

        html = api.add_tracking(recipient, html)

    if sender:
        from_email = '%s <%s>' % (sender.get_full_name() or sender.email, settings.MASKED_FROM_EMAIL)
    else:
        from_email = settings.DEFAULT_FROM_EMAIL

    message = EmailMultiAlternatives(subject, text, from_email, [recipient])
    message.attach_alternative(html, 'text/html')
    message.send()


def format_us_phone_number(value):
    phone = parse(value, 'US')
    formatted = format_number(phone, PhoneNumberFormat.E164)
    if phone.extension:
        formatted += 'x%s' % phone.extension
    return formatted

