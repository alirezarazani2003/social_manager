# core/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
import logging
task_logger = logging.getLogger('core.task')

LOGS_DIR = Path(settings.BASE_DIR) / 'logs'

@shared_task
def daily_log_report():
    """
    گزارش روزانه
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    task_logger.info(f"Starting daily log report for {today_str}")

    report = {
        "summary": {
            "total_activities": 0,
            "total_errors": 0,
            "failed_posts": 0,
            "security_warnings": 0,
            "active_users": set(),
        },
        "details": {
            "errors": [],
            "security_events": [],
        }
    }

    log_file = LOGS_DIR / 'all.log'
    if not log_file.exists():
        task_logger.warning("Log file not found!")
        return "Log file not found."

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if today_str not in line:
                    continue

                if '[INFO]' in line and 'published post' in line:
                    report["summary"]["total_activities"] += 1
                    if 'User' in line:
                        try:
                            user_id = line.split('User ')[1].split(' ')[0]
                            report["summary"]["active_users"].add(user_id)
                        except:
                            pass

                if '[ERROR]' in line:
                    report["summary"]["total_errors"] += 1
                    if 'publish' in line and 'Failed' in line:
                        report["summary"]["failed_posts"] += 1
                    report["details"]["errors"].append(line.strip())

                if '[WARNING]' in line and 'security' in line:
                    report["summary"]["security_warnings"] += 1
                    report["details"]["security_events"].append(line.strip())

    except Exception as e:
        task_logger.error(f"Error reading log file: {e}")
        return f"Failed to read log: {e}"

    active_users = len(report["summary"]["active_users"])
    message = f"""
گزارش روزانه عملکرد - {today_str}

آمار کلی:
- کاربران فعال: {active_users}
- پست‌های ارسالی: {report["summary"]["total_activities"]}
- خطاها: {report["summary"]["total_errors"]}
  - ارسال ناموفق پست: {report["summary"]["failed_posts"]}
- اخطارهای امنیتی: {report["summary"]["security_warnings"]}

خطاها (تست):
{chr(10).join(report['details']['errors'][:5]) if report['details']['errors'] else 'ندارد'}

رویدادهای امنیتی (تست):
{chr(10).join(report['details']['security_events'][:5]) if report['details']['security_events'] else 'ندارد'}

این گزارش به صورت خودکار تولید شده است.
"""

    try:
        send_mail(
            subject=f"گزارش روزانه سرویس شبکه اجتماعی - {today_str}",
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['arazani179@gmail.com'],
            fail_silently=False,
        )
        task_logger.info("Daily report email sent successfully.")
    except Exception as e:
        task_logger.error(f"Failed to send email: {e}")

    return f"Daily report completed for {today_str}."