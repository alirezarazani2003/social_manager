from rest_framework.throttling import SimpleRateThrottle
from django.conf import settings

class CustomRoleRateThrottle(SimpleRateThrottle):
    scope = 'custom_role'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            if request.user.is_superuser:
                self.scope = 'admin'
            else:
                self.scope = 'user'
            return self.cache_format % {
                'scope': self.scope,
                'ident': request.user.pk
            }
        else:
            self.scope = 'anon'
            return self.cache_format % {
                'scope': self.scope,
                'ident': self.get_ident(request)
            }
