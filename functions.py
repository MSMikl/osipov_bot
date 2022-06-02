import os
import tracemalloc

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()


from devman.models import Student, Manager, Team


def get_student_info(student_id):
    result = {'id': student_id}
    student = Student.objects.prefetch_related('teams').get(id=student_id)
    result['firstname'] = student.firstname
    result['secondname'] = student.secondname
    result['level'] = student.level
    current_team = (
        student
        .teams
        .filter(is_active=True)
        .select_related('manager')
        .prefetch_related('students')
        .current()
    )
    if current_team:
        result['in_project'] = True
        result['team_id'] = current_team.id
        result['current_team'] = current_team.title
        result['call_time'] = current_team.call_time
        result['students'] = [
            f'{x.__str__()} {x.id}' for x in current_team.students.all()
        ]
        result['PM'] = current_team.manager.__str__()
    return result


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
            'tg_chat': team.tg_chat
        })
    result['name'] = f'{manager.firstname} {manager.secondname}'
    return result


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
    return result


def close_team(team_id, manager_id, final_status=''):
    team = Team.objects.select_related('manager').get(id=team_id)
    if manager_id != team.manager.id:
        return None
    team.is_active = False
    team.final_status = final_status
    team.save()
    return team.id

if __name__ == '__main__':
    print(get_manager_info('@Michalbl4')['teams'][0]['trello'])