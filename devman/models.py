from datetime import datetime, time

from django.db import models


class Manager(models.Model):
    id = models.CharField(
        'Telegram id',
        max_length=50,
        unique=True,
        primary_key=True
    )
    name = models.CharField('Имя', max_length=70, blank=True)
    starttime = models.TimeField(
        'Начало рабочего интервала',
        default=time(0, 0)
    )
    finishtime = models.TimeField(
        'Окончание рабочего интервала',
        default=time(0, 0)
    )
    is_active = models.BooleanField('Работает', default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'ПМ'
        verbose_name_plural = 'ПМы'


class Student(models.Model):
    LEVEL_CHOICES = [
        ('novice', 'Новичок'),
        ('novice+', 'Новичок +'),
        ('junior', 'Джун')
    ]
    STATUS_CHOICES = [
        (1, 'Нет проекта'),
        (2, 'В ожидании ответа'),
        (3, 'Ждет команду'),
        (4, 'В проекте'),
        (0, 'Не сможет участвовать')
    ]
    id = models.CharField(
        'Telegram id',
        max_length=50,
        unique=True,
        primary_key=True
    )
    chat_id = models.IntegerField(
        'Идентификатор чата с ботом в ТГ', null=True, blank=True
    )
    name = models.CharField('Имя', max_length=70, blank=True)
    level = models.CharField(
        'Уровень подготовки',
        max_length=10,
        choices=LEVEL_CHOICES,
        default='novice'
    )
    status = models.IntegerField(
        'Текущий статус',
        choices=STATUS_CHOICES,
        default=1
    )
    banned_students = models.ManyToManyField(
        'self',
        verbose_name='Нежелательные члены команды',
        blank=True
    )
    desired_students = models.ManyToManyField(
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
    available_time_start = models.TimeField(null=True, blank=True)
    available_time_finish = models.TimeField(null=True, blank=True)
    project_date = models.DateField(
        'Дата начала ближайшего проекта',
        null=True,
        blank=True
    )
    far_east = models.BooleanField(
        verbose_name='С Дальнего Востока',
        default=False
    )
    is_active = models.BooleanField('Доступен для проекта', default=True)

    @property
    def active_team(self):
        return self.teams.filter(is_active=True).last()

    def __str__(self):
        return self.name

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
        related_name='ts',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='ПМ'
    )
    is_active = models.BooleanField('Проект активен', default=True)
    final_status = models.CharField(
        'Результат проекта',
        max_length=100,
        blank=True
    )
    trello = models.URLField('Доска в Трелло', blank=True, null=True)
    tg_chat = models.BigIntegerField('Чат в Телеграм', blank=True, null=True)
    description = models.URLField('Описание проекта', blank=True)

    def __str__(self):
        return f'Команда {self.id} {self.date}'

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'


class Start(models.Model):
    is_active = models.BooleanField('Доступна для записи', default=False)
    primary_date = models.DateField('Основная неделя проекта')
    secondary_date = models.DateField('Запасная неделя проекта')
    send_request = models.BooleanField('Отправить запрос', default=False)
    send_teams = models.BooleanField('Разослать сформированные команды', default=False)

    def __str__(self) -> str:
        return f"Даты {datetime.strftime(self.primary_date, '%d.%m')}, {datetime.strftime(self.secondary_date, '%d.%m')}"
