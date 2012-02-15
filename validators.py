import phonenumbers


def valid_us_phone(phone):
    try:
        phone_number = phonenumbers.parse(phone, "US")
        if len(str(phone_number.national_number)) == 10 and phone_number.country_code == 1:
            return True
    except phonenumbers.phonenumberutil.NumberParseException, e:
        pass
    return False

