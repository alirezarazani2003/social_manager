# logging_setup.py
import logging
import re

class TokenMaskingFilter(logging.Filter):
    """
    این فیلتر توکن‌های تلگرام رو از پیام‌های لاگ پاک می‌کنه
    """
    def filter(self, record):
        if isinstance(record.msg, str):
            record.msg = re.sub(r'bot\d+:[\w-]+', 'bot[REDACTED]', record.msg)
        return True

def setup_logging():
    # سطح لاگ عمومی رو محدود کن (اختیاری)
    logging.basicConfig(level=logging.INFO)

    # ماسک‌کردن توکن در همه هندلرها
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(TokenMaskingFilter())

    # محدود کردن لاگ‌های پر سر و صدای http و telegram
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram.vendor.ptb_urllib3").setLevel(logging.WARNING)
    logging.getLogger("telegram.bot").setLevel(logging.WARNING)
    logging.getLogger("telegram.ext.dispatcher").setLevel(logging.WARNING)
