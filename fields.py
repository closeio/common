from phonenumbers import PhoneNumber
from phonenumbers.phonenumberutil import format_number, parse, PhoneNumberFormat, is_possible_number

from django.db import models
from django import forms
from django.utils import simplejson as json

from common.utils import dumps, loads, Encoder
from common.validators import valid_us_phone


class JSONWidget(forms.Textarea):
    def render(self, name, value, attrs=None):
        if not isinstance(value, basestring):
            value = dumps(value, indent=2)
        return super(JSONWidget, self).render(name, value, attrs)

class JSONFormField(forms.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['widget'] = JSONWidget
        super(JSONFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        if not value: return
        try:
            return loads(value)
        except Exception, exc:
            raise forms.ValidationError(u'JSON decode error: %s' % (unicode(exc),))


from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^common\.fields\.JSONField"])
class JSONField(models.TextField):
    __metaclass__ = models.SubfieldBase

    def formfield(self, **kwargs):
        return super(JSONField, self).formfield(form_class=JSONFormField, **kwargs)

    def __init__(self, *args, **kwargs):
        self.dump_kwargs = kwargs.pop('dump_kwargs', {'cls': Encoder})
        self.load_kwargs = kwargs.pop('load_kwargs', {})

        super(JSONField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if isinstance(value, basestring):
            try:
                return json.loads(value, **self.load_kwargs)
            except ValueError:
                pass

        return value

    def get_db_prep_save(self, value, connection=None):
        """Convert our JSON object to a string before we save"""

        if not isinstance(value, basestring):
            value = json.dumps(value, **self.dump_kwargs)

        return super(JSONField, self).get_db_prep_save(value, connection=connection)


add_introspection_rules([], ["^common\.fields\.PhoneNumberField"])
class PhoneNumberField(models.CharField):
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, **kwargs):
        validators = kwargs.get('validators', [])
        validators.append(valid_us_phone)
        kwargs['validators'] = validators
        super(PhoneNumberField, self).__init__(**kwargs)

    def get_db_prep_value(self, value, connection, prepared=False):
        try:
            return format_us_phone_number(value)
        except:
            return value
    
    def to_python(self, value):
        if isinstance(value, basestring) and value != '':
            try:
                value = format_number(parse(value,"US"),PhoneNumberFormat.INTERNATIONAL)
            except:
                pass
        return value
    
    def get_db_prep_save(self, value, **kwargs):
        if value is None: return
        try:
            return format_us_phone_number(value)
        except:
            return value
    
    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        try:
            return format_number(parse(value,"US"),PhoneNumberFormat.INTERNATIONAL)
        except:
            return value

