import datetime

from django.db import models
from django.db.models.fields import EmailField

def email_field_init(self, *args, **kwargs):
    kwargs['max_length'] = kwargs.get('max_length', 254)
    self._original__init__(*args, **kwargs)
EmailField._original__init__ = EmailField.__init__
EmailField.__init__ = email_field_init


class Base(models.Model):
    date_created = models.DateTimeField(blank=True, editable=False)
    date_updated = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        now = datetime.datetime.utcnow()
        if not self.pk and not self.date_created:
            self.date_created = now
        self.date_updated = now
        super(Base, self).save(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ('-date_created',)


