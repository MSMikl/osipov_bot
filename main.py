import os

import django

from devman.models import Student, Manager, Team

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

