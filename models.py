import datetime

from django.db import models
from django.db.models.fields import EmailField
from django.contrib.localflavor.us.us_states import STATE_CHOICES


def email_field_init(self, *args, **kwargs):
    kwargs['max_length'] = kwargs.get('max_length', 254)
    self._original__init__(*args, **kwargs)
EmailField._original__init__ = EmailField.__init__
EmailField.__init__ = email_field_init


class ActiveManager(models.Manager):
    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(is_active=True)


class Base(models.Model):
    date_created = models.DateTimeField(blank=True, editable=False)
    date_updated = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        abstract = True
        ordering = ('-date_created',)

    def save(self, *args, **kwargs):
        if not kwargs.get('skip_validation', False):
            self.full_clean() #enforce model level validation
        now = datetime.datetime.utcnow()
        update_timestamps = kwargs.pop('update_timestamps', True)
        if update_timestamps:
            if not self.pk and not self.date_created:
                self.date_created = now
            self.date_updated = now
        super(Base, self).save(*args, **kwargs)

    def has_changed(instance, field):
        """Determine if an attribute has changed since the last save()"""
        # http://zmsmith.com/2010/05/django-check-if-a-field-has-changed/
        if not instance.pk:
            return False
        old_value = instance.__class__._default_manager.filter(pk=instance.pk).values(field).get()[field]
        return not getattr(instance, field) == old_value


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

