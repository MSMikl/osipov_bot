import os

from datetime import timedelta

import django

from django.db.models import Count, F, Value
from django.utils import timezone

from devman.models import Student, Manager, Team

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

def get_student_info(user_id):
    result = {'id': user_id}
    student = Student.objects.prefetch_related('teams').get(id=user_id)
    result['firstname'] = student.firstname
    result['secondname'] = student.secondname
    last_team = (
        student
        .teams
        .select_related('manager')
        .prefetch_related('students')
        .last()
    )
    result['in_project'] = (
        timezone.now().date() - last_team.date <= timedelta(days=7)
    )
    if result['in_project']:
        result['team_id'] = last_team.id
        result['current_team'] = last_team.title
        result['call_time'] = last_team.call_time
        result['students'] = [
            f'{x.__str__()} {x.id}' for x in last_team.students.all()
        ]
        result['PM'] = last_team.manager.__str__()
    return result


def get_team_info(id):
    team = (
        Team.objects
        .prefetch_related('students')
        .select_related('manager')
        .get(id=id)
    )
    result = {'id': id}
    result['project_name'] = team.title
    result['students'] = [f'{x.__str__()} {x.id}' for x in team.students.all()]
    result['PM'] = team.manager.__str__()
    result['call_time'] = team.call_time
    return result