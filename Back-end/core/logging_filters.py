import logging
from threading import current_thread
import re

_local = {}

class TelegramRequestFilter(logging.Filter):
    TOKEN_PATTERN = re.compile(r"(bot\d+:[A-Za-z0-9_\-]+)")

    def filter(self, record):
        msg = record.getMessage()

        if 'api.telegram.org' in msg:
            masked_msg = self.TOKEN_PATTERN.sub(r"bot***:***", msg)
            record.msg = masked_msg
            record.args = ()
        return True
    
    
    
class ContextFilter(logging.Filter):
    def filter(self, record):
        ctx = _local.get(current_thread().ident, {})
        record.user_id = ctx.get('user_id', 'Anonymous')
        record.request_id = ctx.get('request_id', 'Unknown')
        record.client_ip = ctx.get('client_ip', 'Unknown')
        return True

def set_user_id(user_id):
    _local[current_thread().ident] = {
        **_local.get(current_thread().ident, {}),
        'user_id': user_id
    }

def set_request_id(request_id):
    _local[current_thread().ident] = {
        **_local.get(current_thread().ident, {}),
        'request_id': request_id
    }

def set_client_ip(ip):
    _local[current_thread().ident] = {
        **_local.get(current_thread().ident, {}),
        'client_ip': ip
    }
def clear_context():
    _local.pop(current_thread().ident, None)
