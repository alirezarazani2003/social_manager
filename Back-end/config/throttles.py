from rest_framework.throttling import ScopedRateThrottle, SimpleRateThrottle


class RoleBasedRateThrottle(ScopedRateThrottle):
    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            self.scope = 'anon'
        elif request.user.is_staff:
            self.scope = 'admin'
        else:
            self.scope = 'user'
        return super().get_cache_key(request, view)


class RequestOTPThrottle(SimpleRateThrottle):
    scope = 'otp_request'

    def get_cache_key(self, request, view):
        email = request.data.get('email')
        ip = self.get_ident(request)

        if not email:
            return f"otp_request_ip:{ip}"
        return f"otp_request_email:{email.lower()}|{ip}"