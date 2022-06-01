from django.db import models


class Manager(models.Model):
    id = models.CharField(
        'Telegram id',
        max_length=50,
        unique=True,
        primary_key=True
    )
    firstname = models.CharField('Имя', max_length=50, blank=True)
    secondname = models.CharField('Фамилия', max_length=50, blank=True)
    starttime = models.TimeField('Начало рабочего интервала')
    finishtime = models.TimeField('Окончание рабочего интервала')

    def __str__(self):
        return f'{self.firstname} {self.secondname}'

    class Meta:
        verbose_name = 'ПМ'
        verbose_name_plural = 'ПМы'


class Student(models.Model):
    LEVEL_CHOICES = [
        ('Новичок', 'Новичок'),
        ('Новичок +', 'Новичок +'),
        ('Джун', 'Джун')
    ]
    id = models.CharField(
        'Telegram id',
        max_length=50,
        unique=True,
        primary_key=True
    )
    firstname = models.CharField('Имя', max_length=50, blank=True)
    secondname = models.CharField('Фамилия', max_length=50, blank=True)
    level = models.CharField(
        'Уровень подготовки',
        max_length=10,
        choices=LEVEL_CHOICES,
        default='Новичок'
    )
    banned_student = models.ManyToManyField(
        'self',
        verbose_name='Нежелательные члены команды',
        blank=True
    )
    desired_student = models.ManyToManyField(
        'self',
        verbose_name='Обязательные партнеры в команде',
        blank=True
    )
    banned_manager = models.ManyToManyField(
        Manager,
        verbose_name='Нежелательные ПМ',
        blank=True,
        related_name='banned_students'
    )
    desired_manager = models.ForeignKey(
        Manager,
        verbose_name='Желаемый ПМ',
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    available_time_start = models.TimeField(null=True)
    available_time_finish = models.TimeField(null=True)
    far_east = models.BooleanField(
        verbose_name='С Дальнего Востока',
        default=False
    )

    def __str__(self):
        return f'{self.firstname} {self.secondname}'

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'


class Team(models.Model):
    date = models.DateField('Дата начала проекта')
    title = models.CharField('Название проекта', max_length=100, blank=True)
    call_time = models.TimeField('Время созвона', blank=True, null=True)
    students = models.ManyToManyField(
        Student,
        related_name='teams',
        verbose_name='Студенты'
    )
    manager = models.ForeignKey(
        Manager,
        on_delete=models.SET_NULL,
        null=True, verbose_name='ПМ'
    )
    is_active = models.BooleanField('Проект активен', default=True)
    final_status = models.CharField(
        'Результат проекта',
        max_length=100,
        blank=True
    )

    def __str__(self):
        return f'Команда {self.id} {self.date}'

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'
