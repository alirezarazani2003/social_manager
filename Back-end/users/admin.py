from django.contrib import admin
from .models import User
from posts.admin import UserMediaStorageInline
from channels.models import Channel

class ChannelInline(admin.TabularInline):  # یا StackedInline
    model = Channel
    extra = 0
    fields = ('name', 'username', 'platform', 'platform_channel_id', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    inlines = [UserMediaStorageInline, ChannelInline]
    list_display = ('email', 'first_name', 'last_name')
