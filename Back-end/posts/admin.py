from django.contrib import admin
from .models import UserMediaStorage
from .forms import UserMediaStorageInlineForm

class UserMediaStorageInline(admin.StackedInline):
    model = UserMediaStorage
    form = UserMediaStorageInlineForm
    can_delete = False
    verbose_name_plural = "فضای کاربر"
