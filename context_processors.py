from django.contrib.sites.models import Site
from django.conf import settings

def globals(request):
    return {
        'site': Site.objects.get_current(),
        'ssl': request.is_secure(),
    } 
