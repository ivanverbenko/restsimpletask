# Generated by Django 4.2.4 on 2023-08-13 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firsttask', '0004_rename_conact_dispatch_contact'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dispatch',
            name='contact',
        ),
        migrations.AddField(
            model_name='dispatch',
            name='email',
            field=models.EmailField(default=None, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='dispatch',
            name='phone',
            field=models.CharField(default=None, max_length=20, null=True),
        ),
    ]
