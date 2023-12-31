# Generated by Django 4.2.4 on 2023-12-05 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dispatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('retail_id', models.CharField(max_length=255)),
                ('estate_id', models.CharField(max_length=255)),
                ('broker_id', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('phone', 'phone'), ('email', 'email')], max_length=20)),
                ('phone', models.CharField(default=None, max_length=20, null=True)),
                ('email', models.EmailField(default=None, max_length=254, null=True)),
                ('sent', models.BooleanField(default=False)),
            ],
        ),
    ]
