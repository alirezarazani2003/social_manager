from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access')
        if access_token is None:
            return None
        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except Exception as e:
            logging.getLogger('auth').error(f"Token validation failed: {e}")
            return None
