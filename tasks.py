from django.core.mail import EmailMultiAlternatives

from celery.task import Task
from celery.registry import tasks

class SendEmail(Task):
    def run(self, subject, message, from_email, to_emails, bcc=None, headers=None, fail_silently=False, html_body=None, **kwargs):
        email = EmailMultiAlternatives(subject, message, from_email=from_email, to=to_emails, bcc=None, connection=None, attachments=None, headers=headers)
        if html_body is not None:
            email.attach_alternative(html_body, 'text/html')
        email.send(fail_silently=fail_silently)

tasks.register(SendEmail)
