import re
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from rest_framework import serializers

NAME_PATTERN = re.compile(r'^[آ-یA-Za-z\u200C\s\-\'\.]+$')
PHONE_PATTERN = re.compile(r'^09\d{9}$')
EMAIL_PATTERN = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
OTP_PATTERN = re.compile(r'[0-9]\d{5}$')
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
)
HTML_PATTERN = re.compile(r'<.*?>|javascript:|on\w+\s*=', re.IGNORECASE)


def no_html_js_validator(value: str):
    if not isinstance(value, str):
        raise ValidationError("Invalid value type.")
    value = value.strip()  # delete empty space
    if HTML_PATTERN.search(value):
        raise serializers.ValidationError(
            'کد های html و جاوا اسکریپتی  مجاز نیست ای متجاوز!')
    return value


def name_validator(value: str):
    no_html_js_validator(value)
    value = value.strip()
    if NAME_PATTERN.search(value):
        raise serializers.ValidationError(
            ' در فیلد نام فقط مجاز به وارد کردن حروف فارسی یا انگلیسی هستید.')

    return value


def email_validator(value: str):
    no_html_js_validator(value)
    value = value.strip()
    if EMAIL_PATTERN.search(value):
        raise serializers.ValidationError('مقدار نا معتبر است.')
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


def phone_validator(value):
    no_html_js_validator(value)
    value = value.strip()
    if PHONE_PATTERN.search(value):
        raise serializers.ValidationError('مقدار نامعتبر است.')
    return value