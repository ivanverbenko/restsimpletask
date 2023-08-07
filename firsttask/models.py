from django.db import models

# Create your models here.
class Dispatch(models.Model):
    name = models.CharField(max_length=20)
    message = models.TextField()