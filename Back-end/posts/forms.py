from django import forms
from .models import UserMediaStorage

class UserMediaStorageInlineForm(forms.ModelForm):
    total_space_mb = forms.FloatField(label="فضای اختصاص داده‌شده (MB)")
    used_space_mb = forms.FloatField(label="فضای استفاده‌شده (MB)")

    class Meta:
        model = UserMediaStorage
        fields = ('total_space_mb', 'used_space_mb')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.fields['total_space_mb'].initial = self.instance.total_space / (1024 * 1024)
            self.fields['used_space_mb'].initial = self.instance.used_space / (1024 * 1024)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_space = int(self.cleaned_data['total_space_mb'] * 1024 * 1024)
        instance.used_space = int(self.cleaned_data['used_space_mb'] * 1024 * 1024)
        if commit:
            instance.save()
        return instance
