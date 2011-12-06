import cgi
import datetime
import urllib
import urlparse

from django import template
from django.utils.translation import ungettext, ugettext as _
from django.template.defaulttags import URLNode, url

from common.utils import full_url, ellipsize as _ellipsize


register = template.Library()

@register.filter
def humanized_time(timestamp = None):
    """
    Returns a humanized string representing time difference
    between now() and the input timestamp.
    
    The output rounds up to days, hours, minutes, or seconds.
    4 days 5 hours returns '4 days'
    0 days 4 hours 3 minutes returns '4 hours', etc...
    """

    now = datetime.datetime.utcnow()

    if not now > timestamp:
        timeDiff = now - now
    else:
        timeDiff = now - timestamp

    days = timeDiff.days
    hours = timeDiff.seconds/3600
    minutes = timeDiff.seconds%3600/60
    seconds = timeDiff.seconds%3600%60

    if days > 0:
        return ungettext('%(count)d day ago', '%(count)d days ago', days) % { 'count': days }
    elif hours > 0:
        return ungettext('%(count)d hour ago', '%(count)d hours ago', hours) % { 'count': hours }
    elif minutes > 0:
        return ungettext('%(count)d min ago', '%(count)d mins ago', minutes) % { 'count': minutes }
    elif seconds > 0:
        if seconds < 3:
            return _('now')
        return ungettext('%(count)d sec ago', '%(count)d secs ago', seconds) % { 'count': seconds }
    else:
        return _('now')


@register.filter
def humanized_duration(duration):
    days = duration // 86400
    hours = (duration % 86400) // 3600
    minutes = (duration % 86400) % 3600 // 60
    seconds = (duration % 86400) % 3600 % 60

    text_days = ungettext('%(count)d day', '%(count)d days', days) % { 'count': days }
    text_hours = ungettext('%(count)d hour', '%(count)d hours', hours) % { 'count': hours }
    text_minutes = ungettext('%(count)d min', '%(count)d mins', minutes) % { 'count': minutes }
    text_seconds = ungettext('%(count)d sec', '%(count)d secs', seconds) % { 'count': seconds }

    if days > 0:
        return u'%s %s' % (text_days, text_hours)
    if hours > 0:
        return u'%s %s' % (text_hours, text_minutes)
    if minutes > 0:
        return u'%s %s' % (text_minutes, text_seconds)

    return text_seconds


@register.simple_tag(takes_context=True)
def append_to_get(context, key, value):
    request = context['request']
    params = dict(cgi.parse_qsl(request.META.get('QUERY_STRING')))
    params[key] = value

    return '?%s' % urllib.urlencode(params)


@register.simple_tag(takes_context=True)
def remove_from_get(context, key):
    request = context['request']
    params = dict(cgi.parse_qsl(request.META.get('QUERY_STRING')))
    try:
        del params[key]
    except KeyError:
        pass

    return '?%s' % urllib.urlencode(params)


class AbsoluteURLNode(URLNode):
    def render(self, context):
        path = super(AbsoluteURLNode, self).render(context)
        return full_url(path)

def abs_url(parser, token, node_cls=AbsoluteURLNode):
    """Just like {% url %} but ads the domain of the current site."""
    node_instance = url(parser, token)
    return node_cls(view_name=node_instance.view_name,
        args=node_instance.args,
        kwargs=node_instance.kwargs,
        asvar=node_instance.asvar)

abs_url = register.tag(abs_url) 


@register.filter
def ellipsize(value, length):
    return _ellipsize(value, length)
