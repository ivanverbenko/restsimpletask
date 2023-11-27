import logging

from distribution.celery import app
from firsttask.models import Dispatch
import random

from sender.views import EmailDispatchView,SMSDispatchView


@app.task
def execute_email_dispatch_view():
    view = EmailDispatchView()
    view.get(None)

@app.task
def execute_phone_dispatch_view():
    view = SMSDispatchView()
    view.get(None)


