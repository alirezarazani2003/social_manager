from django.test import TestCase
from services import send_message_bale
import os
import django
import sys


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()


class dummyChannel():
    platform_channel_id = "@nanajij"

# success, message = send_message_bale(channel=dummyChannel(), text="سلام از ربات بله 🚀")
# print("successfully:", success)
# print("message:", message)


# success, message = send_message_bale(
#     channel=dummyChannel(),
#     text="اینم یه تصویر تستی",
#     files=[{"path": "./image/test.jpg", "caption": "تست تصویر"}]
# )
# print("successfully:", success)
# print("message:", message)



files = [
    {"path": "image/test1.jpg", "caption": "تصاویر گل"},
    {"path": "image/test2.jpg"},
    {"path": "image/test3.jpg"},
    {"path": "image/test4.jpg"}
]

success, msg = send_message_bale(channel=dummyChannel(), files=files)
print("موفق:", success)
print("پیغام:", msg)

