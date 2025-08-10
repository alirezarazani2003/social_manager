from celery import shared_task
import logging
import zipfile
from pathlib import Path
from datetime import datetime
from django.conf import settings
import psutil
from django.db import connection
from django.conf import settings
from django.core.mail import EmailMessage
import logging

task_logger = logging.getLogger('core.task')

@shared_task
def daily_log_report():
    LOGS_DIR = Path(settings.BASE_DIR) / 'logs'
    today_str = datetime.now().strftime('%Y-%m-%d')

    task_logger.info(f"Starting daily log report and backup for {today_str}")

    report = {
        "users": {
            "login_count": 0,
            "failed_logins": 0,
            "registrations": 0,
            "top_ips": {},
        },
        "posts": {
            "scheduled": 0,
            "cancelled": 0,
            "retried": 0,
            "failed": 0,
            "sent": 0,
        },
        "chat": {
            "sessions_created": 0,
            "messages_sent": 0,
            "ai_errors": 0
        },
        "system": {
            "error_count": 0,
            "warning_count": 0,
        },
    }

    if not LOGS_DIR.exists():
        task_logger.error("Logs directory not found!")
        return "Logs directory missing."

    log_files = [f for f in LOGS_DIR.iterdir() if f.is_file() and (f.suffix in ['.log', '.txt'] or 'log' in f.name)]
    if not log_files:
        task_logger.warning("No log files to process.")
    else:
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if today_str not in line:
                            continue

                        if 'registered successfully' in line and 'User' in line:
                            report["users"]["registrations"] += 1
                            ip = extract_value(line, 'IP=')
                            report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                        if 'logged in successfully' in line and 'User' in line:
                            report["users"]["login_count"] += 1
                            ip = extract_value(line, 'IP=')
                            report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                        if 'Failed login attempt' in line and 'IP=' in line:
                            report["users"]["failed_logins"] += 1
                            ip = extract_value(line, 'IP=')
                            report["users"]["top_ips"][ip] = report["users"]["top_ips"].get(ip, 0) + 1
                        if 'scheduled for' in line and 'Post ' in line:
                            report["posts"]["scheduled"] += 1
                        if 'cancelled by user' in line:
                            report["posts"]["cancelled"] += 1
                        if 'posts' in line and 'retry' in line:
                            report["posts"]["retried"] += 1
                        if 'send_post_task failed' in line or 'Failed to send post' in line:
                            report["posts"]["failed"] += 1
                        if 'sent successfully to' in line and 'Post ' in line:
                            report["posts"]["sent"] += 1
                        if 'created chat session' in line and 'User' in line:
                            report["chat"]["sessions_created"] += 1
                        if 'sending message to AI' in line and 'User' in line:
                            report["chat"]["messages_sent"] += 1
                        if 'Connection error to AI service' in line or 'AI service timeout' in line:
                            report["chat"]["ai_errors"] += 1
                        if '[ERROR]' in line and 'django' not in line and 'core.task' not in line:
                            report["system"]["error_count"] += 1
                        if '[WARNING]' in line and 'django' not in line and 'core.task' not in line:
                            report["system"]["warning_count"] += 1

            except Exception as e:
                task_logger.error(f"Error reading {log_file}: {e}")

    top_ips = sorted(report["users"]["top_ips"].items(), key=lambda x: -x[1])[:5]
    top_ips_html = ''.join(
        f'<li><strong>{ip}:</strong> {cnt} بار</li>'
        for ip, cnt in top_ips
    )

    message = f"""
<html>
<head>
    <style>
        body {{ font-family: Tahoma, sans-serif; direction: rtl; background: #f9f9f9; padding: 20px; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2980b9; margin-top: 20px; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 8px 0; padding: 8px; background: #f1f8ff; border-right: 4px solid #3498db; border-radius: 6px; }}
        .error {{ background: #fdf2f2; border-right-color: #e74c3c; }}
        .warning {{ background: #fff9e6; border-right-color: #f39c12; }}
        .summary {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; font-size: 0.9em; color: #7f8c8d; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>گزارش روزانه عملکرد</h1>
        <p><strong>تاریخ:</strong> {today_str}</p>

        <div class="summary">
            <strong>خلاصه کلی:</strong><br>
            پست‌های ارسالی: {report["posts"]["sent"]}<br>
            ارسال مجدد: {report["posts"]["retried"]}<br>
            خطاها: {report["system"]["error_count"]} | اخطارها: {report["system"]["warning_count"]}
        </div>

        <h2>کاربران</h2>
        <ul>
            <li><strong>ورود موفق:</strong> {report["users"]["login_count"]}</li>
            <li><strong>ثبت‌نام:</strong> {report["users"]["registrations"]}</li>
            <li class="error"><strong>تلاش ناموفق ورود:</strong> {report["users"]["failed_logins"]}</li>
        </ul>

        <h2>پست‌ها</h2>
        <ul>
            <li><strong>ارسال شده:</strong> {report["posts"]["sent"]}</li>
            <li><strong>زمان‌بندی شده:</strong> {report["posts"]["scheduled"]}</li>
            <li><strong>لغو شده:</strong> {report["posts"]["cancelled"]}</li>
            <li><strong>ارسال مجدد:</strong> {report["posts"]["retried"]}</li>
            <li class="error"><strong>ناموفق:</strong> {report["posts"]["failed"]}</li>
        </ul>

        <h2>چت هوش مصنوعی</h2>
        <ul>
            <li><strong>سشن‌های ایجاد شده:</strong> {report["chat"]["sessions_created"]}</li>
            <li><strong>پیام‌های ارسالی:</strong> {report["chat"]["messages_sent"]}</li>
            <li class="error"><strong>خطاهای هوش مصنوعی:</strong> {report["chat"]["ai_errors"]}</li>
        </ul>

        <h2>IPهای پرتردد</h2>
        <ul>
            {top_ips_html}
        </ul>

        <h2>سلامت سیستم</h2>
        <ul>
            <li><strong>خطاها:</strong> {report["system"]["error_count"]}</li>
            <li><strong>اخطارها:</strong> {report["system"]["warning_count"]}</li>
        </ul>

        <div class="footer">
            این گزارش به صورت خودکار تولید شده است — {datetime.now().strftime('%H:%M')}
        </div>
    </div>
</body>
</html>
"""

    zip_buffer_path = LOGS_DIR / f"logs_backup_{today_str}.zip"

    try:
        with zipfile.ZipFile(zip_buffer_path, 'w', zipfile.ZIP_DEFLATED) as log_zip:
            found_logs = False
            for log_file in LOGS_DIR.iterdir():
                if log_file.is_file() and (log_file.suffix in ['.log', '.txt'] or 'log' in log_file.name):
                    log_zip.write(log_file, arcname=log_file.name)
                    task_logger.info(f"Added to zip: {log_file.name}")
                    found_logs = True
            if not found_logs:
                task_logger.warning("No log files found to include in backup.")
                zip_buffer_path.unlink(missing_ok=True)
                return "No logs to backup."
    except Exception as e:
        task_logger.error(f"❌ Failed to create log zip: {e}")
        return f"Zip creation failed: {e}"

    recipients = settings.LOGGING_EMAIL_RECIPIENTS
    if isinstance(recipients, str):
        recipients = [recipients]
    elif not isinstance(recipients, (list, tuple)):
        recipients = []

    if not recipients:
        task_logger.warning("No recipients configured for log report.")
        return "No recipients."

    try:
        from django.core.mail import EmailMessage

        email = EmailMessage(
            subject=f"گزارش روزانه و بک‌آپ لاگ‌ها - {today_str}",
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=recipients,
        )
        email.content_subtype = "html"

        if zip_buffer_path.exists():
            email.attach_file(str(zip_buffer_path))
            task_logger.info(f"Log backup attached: {zip_buffer_path}")
        else:
            task_logger.error("Zip file not found for attachment!")
            return "Zip file missing."

        email.send()
        task_logger.info("Daily report and log backup sent successfully.")

        MAIN_LOG_FILES = ['all.log', 'errors.log', 'alerts.log']
        for log_filename in MAIN_LOG_FILES:
            log_path = LOGS_DIR / log_filename
            if log_path.exists():
                try:
                    with open(log_path, 'w'):
                        pass
                    task_logger.info(f"Cleared log content: {log_filename}")
                except Exception as e:
                    task_logger.error(f"Failed to clear {log_filename}: {e}")
            else:
                task_logger.warning(f"Log file not found: {log_filename}")

        try:
            if zip_buffer_path.exists():
                zip_buffer_path.unlink()
                task_logger.info("Temporary zip file deleted.")
        except Exception as e:
            task_logger.warning(f"Could not delete zip file: {e}")

    except Exception as e:
        task_logger.error(f"Failed to send email: {e}")
        return f"Email sending failed: {e}"

    return f"Daily log report completed and logs cleared for {today_str}."

def extract_value(line, key):
    try:
        if key not in line:
            return 'Unknown'
        value = line.split(key, 1)[1].strip()
        return value.split()[0] if value.split() else 'Unknown'
    except Exception:
        return 'Unknown'

@shared_task
def health_check():
    logger = logging.getLogger('core.system')
    alert_logger = logging.getLogger('core.alert')

    memory = psutil.virtual_memory().percent
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage('/')
    disk_percent = (disk.used / disk.total) * 100

    db_ok = False
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")

    status = f"CPU={cpu:.1f}%, Mem={memory:.1f}%, Disk={disk_percent:.1f}%, DB={'OK' if db_ok else 'ERROR'}"
    logger.info(f"Health Check: {status}")

    alerts = []
    if memory > 85:
        alerts.append(f"حافظه : {memory:.1f}%")
    if cpu > 90:
        alerts.append(f"پردازنده : {cpu:.1f}%")
    if disk_percent > 90:
        alerts.append(f"فضای دیسک : {disk_percent:.1f}%")
    if not db_ok:
        alerts.append("دیتابیس قطع است!")

    if alerts:
        send_critical_alert_email(
            subject="هشدار سلامت سیستم",
            body="مشکلات زیر شناسایی شد:\n\n" + "\n".join(alerts),
            logger=alert_logger
        )

    return status

def send_critical_alert_email(subject, body, logger):
    from django.conf import settings
    from django.core.mail import EmailMessage

    recipients = settings.LOGGING_EMAIL_RECIPIENTS
    if isinstance(recipients, str):
        recipients = [recipients]
    elif not isinstance(recipients, (list, tuple)):
        logger.error("No valid recipients for critical alert.")
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
        logger.critical(f"Critical alert email sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send critical alert email: {e}")