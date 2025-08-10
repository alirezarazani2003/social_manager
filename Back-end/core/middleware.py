import logging
from django.conf import settings
from django.core.mail import EmailMessage
import traceback

logger = logging.getLogger('core.system')
alert_logger = logging.getLogger('core.alert')

class CriticalErrorAlertMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        error_trace = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
        is_db_error = 'connection' in str(exception).lower() or 'database' in str(exception).lower()
        if is_db_error or True: 
            subject = f" خطای 500 در سایت: {request.path}"
            body = f"""
خطای بحرانی در URL: {request.build_absolute_uri()}

نوع خطا: {type(exception).__name__}
پیام: {exception}

مسیر:
{error_trace}

IP کاربر: {self.get_client_ip(request)}
User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}
"""

            self.send_alert_email(subject, body, alert_logger)
        logger.error(f"500 Error on {request.path}: {exception}", exc_info=True)
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', 'Unknown')

    def send_alert_email(self, subject, body, logger):
        recipients = settings.LOGGING_EMAIL_RECIPIENTS
        if isinstance(recipients, str):
            recipients = [recipients]
        elif not isinstance(recipients, (list, tuple)):
            return

        if not recipients:
            return

        try:
            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER,
                to=recipients,
            )
            email.send()
            logger.critical(f"Critical error alert sent: {subject}")
        except Exception as e:
            logger.error(f"Failed to send error alert email: {e}")