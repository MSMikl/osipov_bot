from doctest import DONT_ACCEPT_TRUE_FOR_1
import os

from datetime import date, time

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()


from devman.models import Manager, Team, Student, Project
from functions import create_trello


DATE = date(year=2022, month=6, day=3)


def main():
    default_slots = [0]*48
    slots = {}
    slots_count = {i: 0 for i in range(0, 48)}
    for student in Student.objects.filter(is_active=True):
        student_slots = default_slots.copy()
        start_slot = student.available_time_start.hour*2 + student.available_time_start.minute//30
        finish_slot = student.available_time_finish.hour*2 + student.available_time_finish.minute//30
        for slot in range(start_slot, finish_slot):
            student_slots[slot] = 1
            slots_count[slot] += 1
        slots[student.__str__()] = ((student_slots, student))
    print(slots)

    print(slots_count)

    for manager in Manager.objects.filter(is_active=True):
        start_slot = manager.starttime.hour*2 + manager.starttime.minute//30
        finish_slot = manager.finishtime.hour*2 + manager.finishtime.minute//30
        manager_slots = sorted(list(slots_count.items())[start_slot:finish_slot], key=lambda x: x[1])
        print(manager_slots)

        for slot in range(start_slot, finish_slot):
            students = sorted(slots.items(), key=lambda x: sum(x[1][0][start_slot:finish_slot]))
            if slots_count[slot] < 3:
                continue
            team = Team.objects.create(
                        date=DATE,
                        call_time=time(hour=slot // 2, minute=(slot % 2)*30),
                        manager=manager
                    )
            count = 0
            for student in students:
                if student[1][0][slot]:
                    team.students.add(student[1][1])
                    count += 1
                    for removing_slot in range(len(student[1][0])):
                        slots_count[removing_slot] -= student[1][0][removing_slot]
                    del slots[student[0]]
                if count == 3:
                    break
            print(team.students.all(), team.manager, team.call_time)
            print(slots)

    for project in Project.objects.filter(is_active=True):
        create_trello(project.id)


if __name__ == '__main__':
    main()
