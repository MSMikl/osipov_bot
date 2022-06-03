import os

from datetime import date, time

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from devman.models import Manager, Team, Student


DATE = date(year=2022, month=6, day=3)


def main():
    slots = []
    for student in Student.objects.filter(is_active=True):
        start_slot = student.available_time_start.hour*2 + student.available_time_start.minute//30
        finish_slot = student.available_time_finish.hour*2 + student.available_time_finish.minute//30
        slots.append((start_slot, finish_slot, student))
    slots.sort(key=(lambda x: x[1] - x[0]))
    print(slots)

    slots_count = [0]*48
    for row in slots:
        for slot in range(row[0], row[1]):
            slots_count[slot] += 1

    print(slots_count)

    for manager in Manager.objects.filter(is_active=True):
        start_slot = manager.starttime.hour*2 + manager.starttime.minute//30
        finish_slot = manager.finishtime.hour*2 + manager.finishtime.minute//30
        for slot in range(start_slot, finish_slot):
            if slots_count[slot] < 3:
                continue
            team = Team.objects.create(
                        date=DATE,
                        call_time=time(hour=slot//2, minute=(slot%2)*30),
                        manager=manager
                    )
            count = 0
            for student in slots:
                if slot >= student[0] and slot < student[1]:
                    team.students.add(student[2])
                    count += 1
                    for removing_slot in range(student[0], student[1]):
                        slots_count[removing_slot] -= 1
                if count == 3:
                    team.save()
                    break
            print(team.students.all(), team.manager, team.call_time)

if __name__ == '__main__':
    main()
