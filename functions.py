import argparse
import os

import django

from django.db import models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()


from devman.models import Student, Manager, Team, Start


def get_student_full_data(student):
    result = {'id': student.id}
    result['chat_id'] = student.chat_id
    result['name'] = student.name
    result['level'] = student.level
    result['status'] = student.status
    result['start_time'] = student.available_time_start
    result['finish_time'] = student.available_time_finish
    result['project_date'] = student.project_date
    current_team = (
        student
        .teams
        .filter(is_active=True)
        .select_related('manager')
        .prefetch_related('students')
        .first()
    )
    if current_team:
        result['team_id'] = current_team.id
        result['current_team'] = current_team.title
        result['call_time'] = current_team.call_time
        result['students'] = [
            f'{x.name} {x.id}' for x in current_team.students.all()
        ]
        result['PM'] = f"{current_team.manager.name} {current_team.manager.id}"
        result['trello'] = str(current_team.trello)
        result['description'] = str(current_team.description)
    return result


def get_student_info(student_id, chat_id=None):
    student = (
        Student.objects
        .filter(id=student_id, is_active=True)
        .prefetch_related('teams')
        .first()
    )
    if not student:
        return
    student.chat_id = chat_id
    student.save()
    start = Start.objects.filter(is_active=True).last()
    result = get_student_full_data(student)
    if start:
        result['primary_date'] = start.primary_date
        result['secondary_date'] = start.secondary_date 
    return result


def set_student(data):
    student = Student.objects.filter(id=data['id'])
    student.update(
        project_date=data['week'],
        available_time_start=data['start_time'],
        available_time_finish=data['end_time'],
        status=data['status']
    )


def get_manager_info(manager_id):
    result = {'id': manager_id}
    manager = (
        Manager.objects
        .prefetch_related('ts')
        .filter(id=manager_id)
        .first()
    )
    if not manager:
        return None
    result['teams'] = []
    for team in manager.ts.filter(is_active=True):
        result['teams'].append({
            'call_time': team.call_time,
            'team_id': team.id,
            'team_title': team.title,
            'trello': str(team.trello),
            'tg_chat': team.tg_chat,
            'description': str(team.description),
            'students': [f'{x.__str__()} {x.id}' for x in team.students.all()]
        })
    result['name'] = manager.name
    result['working_time'] = (manager.starttime, manager.finishtime)
    return result


def set_new_time(manager_id, starttime, finishtime):
    manager = Manager.objects.get(id=manager_id)
    manager.starttime, manager.finishtime = starttime, finishtime
    manager.save()


def get_team_info(id):
    team = (
        Team.objects
        .prefetch_related('students')
        .select_related('manager')
        .get(id=id)
    )
    result = {'team_id': id}
    result['project_name'] = team.title
    result['students'] = [f'{x.__str__()} {x.id}' for x in team.students.all()]
    result['PM'] = team.manager.__str__()
    result['call_time'] = team.call_time
    result['description'] = str(team.description)
    result['trello'] = team.trello
    return result


def finalize_teams(start_date):
    teams = Team.objects.filter(is_active=True, date=start_date).prefetch_related('students')
    if teams:
        teams.update(is_active=False)
        teams.students.update(
            status=1,
            project_date=None,
            available_time_start=None,
            available_time_finish=None
        )
    Start.objects.filter(secondary_date=start_date).update(is_active=False)


def check_for_new_date():
    active_date = Start.objects.filter(send_request=True).last()
    if not active_date:
        return
    active_date.send_request = False
    active_date.is_active = True
    active_date.save()
    students = (
        Student.objects
        .filter(is_active=True)
        .prefetch_related('teams')
        .annotate(
            active_teams_count=models.Count('teams', filter=models.Q(teams__is_active=True))
        )
        .filter(active_teams_count=0)
    )
    students.update(status=2)
    return list(students.values_list('chat_id', flat=True))


def check_for_new_teams():
    active_date = Start.objects.filter(send_teams=True).last()
    if not active_date:
        return
    active_date.send_teams = False
    active_date.save()
    students = (
        Student.objects
        .filter(is_active=True)
        .prefetch_related('teams')
        .annotate(
            active_teams_count=models.Count('teams', filter=models.Q(teams__is_active=True))
        )
        .filter(active_teams_count__gt=0)
    )
    students.update(status=4)
    result = [get_student_full_data(student) for student in students]
    return result


if __name__ == '__main__':
    print(check_for_new_date())
    print(check_for_new_teams())
