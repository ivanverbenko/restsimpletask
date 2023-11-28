from distribution.celery import app

from sender.views import BaseDispatchView


@app.task
def execute_email_dispatch_view():
    EmailSend = BaseDispatchView(url = 'http://127.0.0.1:5000/echo',fields_to_send = ['email', 'name', 'message'], type='phone')
    EmailSend.send()

@app.task
def execute_phone_dispatch_view():
    PhoneSend = BaseDispatchView(url = 'http://127.0.0.1:5000/echo',fields_to_send = ['email', 'name', 'message'], type='email')
    PhoneSend.send()


