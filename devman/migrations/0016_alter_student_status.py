# Generated by Django 4.0.4 on 2022-06-04 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devman', '0015_student_project_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='status',
            field=models.IntegerField(choices=[(1, 'Нет проекта'), (2, 'В ожидании ответа'), (3, 'Ждет команду'), (4, 'В проекте'), (0, 'Не сможет участвовать')], default=1, verbose_name='Текущий статус'),
        ),
    ]
