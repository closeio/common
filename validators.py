import phonenumbers

from django.core.exceptions import ValidationError


def valid_us_phone(phone):
    try:
        phone_number = phonenumbers.parse(phone, "US")
        if len(str(phone_number.national_number)) == 10 and phone_number.country_code == 1:
            return
    except phonenumbers.phonenumberutil.NumberParseException, e:
        pass
    raise ValidationError('Not a valid US phone number')

