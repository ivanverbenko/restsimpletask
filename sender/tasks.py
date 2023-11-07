import logging

from distribution.celery import app
from firsttask.models import Dispatch
import random

@app.task
def test():
    Dispatch.objects.filter(sent=False).update(sent=True)


