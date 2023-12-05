from django.db import models
from enum import Enum

class Type(models.TextChoices):
    PHONE = 'phone', 'phone'
    EMAIL= 'email', 'email'

class Dispatch(models.Model):
    name = models.CharField(max_length=255)
    message = models.TextField()
    retail_id = models.CharField(max_length=255)
    estate_id = models.CharField(max_length=255)
    broker_id = models.CharField(max_length=255)
    type =  models.CharField(max_length=20, choices=Type.choices)
    phone = models.CharField(max_length=20, default=None, null=True)
    email = models.EmailField(default=None,null=True)
    sent = models.BooleanField(default=False)