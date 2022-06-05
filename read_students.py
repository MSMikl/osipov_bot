import argparse
import json
import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()


from devman.models import Student, Manager


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', action='store_true', help='считать в базу со студентами')
    parser.add_argument('-m', action='store_true', help='считать в базу ПМов')
    parser.add_argument('file', help='файл для чтения')
    args = parser.parse_args()
    file_to_read, read_students, read_managers = args.file, args.s, args.m
    with open(
        os.path.join(os.path.curdir, file_to_read),
        'r',
        encoding='UTF-8'
    ) as file:
        men = json.load(file)
    if read_students:
        for man in men:
            Student.objects.update_or_create(
                name=man['name'],
                level=man['level'],
                id=man['tg_username'],
                far_east=man['is_far_east']
            )
    elif read_managers:
        for man in men:
            Manager.objects.update_or_create(
                name=man['name'],
                id=man['tg_username']
            )


if __name__ == '__main__':
    main()
