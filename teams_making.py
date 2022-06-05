import os

from datetime import date, time

import django

from django.db import models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from devman.models import Manager, Team, Student, Start


def intersections_count(list1, list2):
    result = 0
    for element in list1:
        if element in list2:
            result += 1
    return result


def make_teams(project_date, level, managers: dict):
    slots = {}
    slots_count = {i: 0 for i in range(48)}
    available_students = (
        Student.objects
        .filter(is_active=True, project_date=project_date, level=level)
        .prefetch_related('teams')
        .annotate(
            active_teams_count=models.Count('teams', filter=models.Q(teams__is_active=True))
        )
        .filter(active_teams_count=0)
    )
    for student in available_students:
        start_slot = student.available_time_start.hour*2 + student.available_time_start.minute//30
        finish_slot = student.available_time_finish.hour*2 + student.available_time_finish.minute//30
        student_slots = list(range(start_slot, finish_slot))
        for slot in student_slots:
            slots_count[slot] += 1
        slots[student.__str__()] = ((student_slots, student))

    for manager in managers:
        manager_slots = sorted([(i, slots_count[i]) for i in manager['slots']], key=lambda x: x[1])

        for slot, _ in manager_slots:
            students = sorted(slots.items(), key=lambda x: intersections_count(x[1][0], manager_slots))
            if slots_count[slot] < 3:
                continue
            team = Team.objects.create(
                        date=project_date,
                        call_time=time(hour=slot // 2, minute=(slot % 2)*30),
                        manager=manager['database']
                    )
            count = 0
            for student in students:
                if slot in student[1][0]:
                    team.students.add(student[1][1])
                    count += 1
                    for removing_slot in student[1][0]:
                        slots_count[removing_slot] -= 1
                    del slots[student[0]]
                if count == 3:
                    break
            manager['slots'].remove(slot)
            print(team.students.all(), team.manager, team.call_time)


def main():
    dates = (Start.objects.last().primary_date, Start.objects.last().secondary_date)
    levels = (
        'novice',
        'novice+',
        'junior'
    )
    for start_date in dates:
        managers = []
        for manager in Manager.objects.filter(is_active=True):
            start_slot = manager.starttime.hour*2 + manager.starttime.minute//30
            finish_slot = manager.finishtime.hour*2 + manager.finishtime.minute//30
            managers.append({
                'id': manager.id,
                'slots': list(range(start_slot, finish_slot)),
                'database': manager
            })
        for level in levels:
            make_teams(start_date, 'novice', managers)


if __name__ == '__main__':
    main()
