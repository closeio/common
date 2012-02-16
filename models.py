import datetime

from django.db import models
from django.db.models.fields import EmailField
from django.contrib.localflavor.us.us_states import STATE_CHOICES


def email_field_init(self, *args, **kwargs):
    kwargs['max_length'] = kwargs.get('max_length', 254)
    self._original__init__(*args, **kwargs)
EmailField._original__init__ = EmailField.__init__
EmailField.__init__ = email_field_init


class Base(models.Model):
    date_created = models.DateTimeField(blank=True, editable=False)
    date_updated = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True
        ordering = ('-date_created',)

    def save(self, *args, **kwargs):
        self.full_clean() #enforce model level validation
        now = datetime.datetime.utcnow()
        if not self.pk and not self.date_created:
            self.date_created = now
        self.date_updated = now
        super(Base, self).save(*args, **kwargs)


class Address(Base):
    address = models.CharField(max_length=80)
    address_2 = models.CharField(null=True, blank=True, max_length=80)
    city = models.CharField(null=True, blank=True, max_length=40)
    state = models.CharField(null=True, blank=True, max_length=2, choices=STATE_CHOICES)
    zip = models.CharField(max_length=5)

    class Meta:
        abstract = True

    def __unicode__(self):
        return ', '.join([self.address, self.zip])
        
    def as_text(self):
        return '\n'.join([part for part in [
            self.address,
            self.address_2,
            '%s, %s %s' % (self.city, self.state, self.zip)
            ] if part])

