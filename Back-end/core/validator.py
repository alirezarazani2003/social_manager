import re
from django.core.exceptions import ValidationError
from rest_framework import serializers

OTP_PATTERN = re.compile(r'[0-9]\d{5}$')
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
)
HTML_PATTERN = re.compile(r'<.*?>|javascript:|on\w+\s*=', re.IGNORECASE)


def no_html_js_validator(value: str):
    if not isinstance(value, str):
        raise ValidationError("Invalid value type.")
    value = value.strip()
    if HTML_PATTERN.search(value):
        raise serializers.ValidationError(
            'کد های html و جاوا اسکریپتی  مجاز نیست ای متجاوز!')
    return value



def otp_validator(value):
    no_html_js_validator(value)
    value = value.strip()
    if OTP_PATTERN.search(value):
        raise serializers.ValidationError('مقدار نامعتبر است.')
    return value


def password_validator(value):
    no_html_js_validator(value)
    value = value.strip()
    if PASSWORD_PATTERN.search(value):
        raise serializers.ValidationError('مقدار نامعتبر است.')
    return value

