import json
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()


from devman.models import Student


def main():
    with open(
        os.path.join(os.path.curdir, 'students.json'),
        'r',
        encoding='UTF-8'
    ) as file:
        students = json.load(file)
    for student in students:
        Student.objects.update_or_create(
            name=student['name'],
            level=student['level'],
            id=student['tg_username'],
            far_east=student['is_far_east']
        )


if __name__ == '__main__':
    main()
