from rest_framework.throttling import BaseThrottle
from django.core.cache import cache
from datetime import timedelta
from django.utils import timezone
from rest_framework.throttling import UserRateThrottle


class RoleBasedRateThrottle(UserRateThrottle):
    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            self.scope = 'anon'
        elif request.user.is_staff:
            self.scope = 'admin'
        else:
            self.scope = 'user'

        return super().get_cache_key(request, view)



class RequestOTPThrottle(BaseThrottle):
    scope = 'otp_request'

    def __init__(self):
        self.rate = '5/minute'

    def allow_request(self, request, view):
        email = request.data.get('email')

        if email is None:
            return True

        key = f"otp_request:{email}"
        current_time = timezone.now()

        request_times = cache.get(key, [])

        request_times = [timestamp for timestamp in request_times if timestamp >
                         current_time - timedelta(minutes=5)]

        if len(request_times) >= 5:
            return False

        request_times.append(current_time)
        cache.set(key, request_times, timeout=60*5)

        return True
