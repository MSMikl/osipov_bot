# Generated by Django 4.0.4 on 2022-06-05 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devman', '0018_remove_start_is_active_start_send_request_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='start',
            name='is_active',
            field=models.BooleanField(default=False, verbose_name='Доступна для записи'),
        ),
    ]
