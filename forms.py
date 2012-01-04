from django import forms
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.forms import AuthenticationForm as AuthAuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.template import loader
from django.utils.translation import ugettext as _
from django.contrib.localflavor.us.forms import USStateField

from common import models as common_models


class AddressForm(forms.ModelForm):
    address = forms.CharField(label=_('Address'), widget=forms.TextInput(attrs={'placeholder': _('Street Address')}))
    address_2 = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': _('Street Address Cont.')}), required=False)
    city = forms.CharField(label=_('City'), widget=forms.TextInput(attrs={'placeholder': _('City')}))
    state = USStateField(widget=forms.TextInput(attrs={'placeholder': _('State'), 'maxlength': '2'}))
    zip = forms.CharField(label=_('ZIP'), widget=forms.TextInput(attrs={'placeholder': _('ZIP'), 'maxlength': '5'}))

    class Meta:
        fields = ('address', 'address_2', 'city', 'state', 'zip')


class RequiredNullBooleanField(forms.NullBooleanField):
    widget = forms.RadioSelect(choices=[(True, "Yes"), (False, "No")])
    
    def clean(self, value):
        value = super(RequiredNullBooleanField, self).clean(value)
        if value is None:
            raise forms.ValidationError("This field is required.")
        return value


class OptionalPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(OptionalPasswordChangeForm, self).__init__(*args, **kwargs)
        
        if not self.data.get('old_password', None) and \
           not self.data.get('new_password1', None) and \
           not self.data.get('new_password2'):

            self.fields['old_password'].required = False
            self.fields['new_password1'].required = False
            self.fields['new_password2'].required = False
            self.clean_old_password = lambda : None
            self.new_password2 = lambda : None
            self.save = lambda : self.user


class AuthenticationForm(AuthAuthenticationForm):
    username = forms.CharField(label=_("E-mail address"), max_length=254)


class RequestForm(forms.Form):
    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(RequestForm, self).__init__(*args, **kwargs)


class ChangeEmailForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangeEmailForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_users = list(User.objects.filter(email=email))
        if existing_users and existing_users[0] != self.instance:
            raise forms.ValidationError(_('A user with this email address already exists. Please choose a different one.'))
        return email


class EmailFormMixin(object):
    def send(self, request):
        email_template = getattr(self, 'template_name', 'common/email_form')

        context = {
            'form': self,
            'form_class_name': self.__class__.__name__,
            'data': self.cleaned_data,
            'user': request.user.is_authenticated() and request.user,
            'ip': request.META.get('REMOTE_ADDR'),
        }

        subject = loader.render_to_string('%s.subj.txt' % email_template, context).strip()
        text_body = loader.render_to_string('%s.body.txt' % email_template, context)

        recipient_list = [mail_tuple[1] for mail_tuple in settings.MANAGERS]

        msg = EmailMessage(subject, text_body, settings.DEFAULT_FROM_EMAIL, recipient_list)
        msg.send()
