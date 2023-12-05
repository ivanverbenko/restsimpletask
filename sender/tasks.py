from distribution.celery import app

from sender.views import LocalhostDispatchView
from dataHandler.models import Type

@app.task
def execute_email_dispatch_view():
    EmailSend = LocalhostDispatchView(fields_to_send = ['email', 'name', 'message'], type=Type.PHONE)
    result = EmailSend.send()
    return result.content
@app.task
def execute_phone_dispatch_view():
    PhoneSend = LocalhostDispatchView(fields_to_send = ['email', 'name', 'message'], type=Type.EMAIL)
    result = PhoneSend.send()
    return result.content

